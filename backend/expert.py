"""专家问答：优先调用 OpenAI 兼容 LLM；否则基于病害百科知识库生成处方。"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request

from wiki import DISEASE_WIKI


def build_expert_prompt(diagnosis: dict, user_message: str) -> str:
    disease = diagnosis.get("disease_name", "未知病害")
    dsi = diagnosis.get("dsi")
    level = diagnosis.get("severity_level", "")
    confidence = diagnosis.get("confidence")
    mode = diagnosis.get("mode", "")

    context = f"当前番茄叶片经 AI 检测为【{disease}】"
    if dsi is not None:
        context += f"，病情指数 DSI={dsi}%"
    if level:
        context += f"，发病等级【{level}】"
    if confidence is not None:
        try:
            context += f"，置信度 {float(confidence) * 100:.1f}%"
        except (TypeError, ValueError):
            pass
    if mode:
        context += f"（诊断模式：{mode}）"

    if user_message.strip():
        return (
            f"你是资深农业植保专家。{context}。\n"
            f"农户追问：{user_message}\n"
            "请给出包含农药选择、配比、施药频次、温湿度调控的精准防治建议。"
        )
    return (
        f"你是资深农业植保专家。{context}。\n"
        "请给出包含农药配比与温湿度调控的精准防治处方，分条列出，语言专业但易懂。"
    )


def _find_wiki(disease_name: str) -> dict | None:
    name = (disease_name or "").strip()
    if not name or name in ("未检出病害", "推理失败", "未知病害"):
        return None
    for item in DISEASE_WIKI:
        if item["name"] == name or name in item["name"] or item["name"] in name:
            return item
    # 英文/别名粗匹配
    aliases = {
        "Early Blight": "早疫病",
        "Late Blight": "晚疫病",
        "Leaf Mold": "叶霉病",
        "Septoria": "斑枯病",
        "Bacterial Spot": "细菌性斑点病",
        "Yellow Leaf Curl": "黄化曲叶病毒病",
        "Spider Mites": "红蜘蛛",
        "Target Spot": "靶斑病",
        "Mosaic": "花叶病毒",
        "Healthy": "健康",
    }
    for en, zh in aliases.items():
        if en.lower() in name.lower():
            return _find_wiki(zh)
    return None


def knowledge_expert_response(diagnosis: dict, user_message: str) -> str:
    """无 LLM Key 时：用百科知识库 + 诊断结果生成结构化处方。"""
    disease = diagnosis.get("disease_name", "未知病害")
    dsi = diagnosis.get("dsi")
    level = diagnosis.get("severity_level", "")
    confidence = diagnosis.get("confidence")
    wiki = _find_wiki(str(disease))

    conf_txt = ""
    if confidence is not None:
        try:
            conf_txt = f"，置信度 {float(confidence) * 100:.1f}%"
        except (TypeError, ValueError):
            pass
    dsi_txt = f"，DSI≈{dsi}%" if dsi is not None else ""
    level_txt = f"，等级【{level}】" if level else ""

    lines = [
        f"## 番茄「{disease}」防治处方",
        "",
        "### 一、诊断结论",
        f"AI 视觉诊断结果为 **{disease}**{conf_txt}{dsi_txt}{level_txt}。",
    ]

    if wiki:
        lines += [
            "",
            f"- 病原：{wiki.get('pathogen', '—')}",
            f"- 类型：{wiki.get('category', '—')}",
            f"- 危害等级：{wiki.get('severity', '—')}",
            "",
            "### 二、典型症状（对照）",
        ]
        for s in wiki.get("symptoms", [])[:4]:
            lines.append(f"- {s}")
        lines += ["", "### 三、发病条件", wiki.get("conditions", "—"), "", "### 四、化学防治"]
        for i, p in enumerate(wiki.get("pesticides", [])[:3], 1):
            lines.append(f"{i}. {p}（按标签稀释，轮换用药）")
        lines += ["", "### 五、农业与环境调控"]
        for p in wiki.get("prevention", [])[:4]:
            lines.append(f"- {p}")
    else:
        lines += [
            "",
            "### 二、通用防治建议",
            "1. 及时摘除病叶并带出田外销毁，减少初侵染源",
            "2. 加强通风降湿，避免叶面长时间结露",
            "3. 选择登记于番茄的保护性/治疗性药剂轮换使用",
            "4. 增施磷钾肥，控制氮肥过旺",
        ]

    if user_message.strip():
        lines += ["", "### 六、针对你的追问", f"> {user_message}", ""]
        q = user_message
        if any(k in q for k in ("药", "喷", "打药", "农药")):
            lines.append("建议优先按上方药剂清单轮换使用，避开正午高温，叶背重点喷施，雨后补喷。")
        elif any(k in q for k in ("湿度", "温度", "通风", "大棚")):
            lines.append("棚内白天宜 22～28℃、夜间 15～18℃，相对湿度控制在 65%～75%，加强通风。")
        elif any(k in q for k in ("肥", "浇水", "水")):
            lines.append("推荐滴灌，避免大水漫灌；控氮增钾，提高抗病性。")
        else:
            lines.append("请结合田间实际情况，必要时联系当地农技部门复核诊断。")

    lines += ["", "> 以上建议基于系统病害知识库与当前 AI 诊断结果生成，仅供参考。"]
    return "\n".join(lines)


def _llm_chat_stream(prompt: str):
    api_key = os.getenv("LLM_API_KEY", "").strip()
    if not api_key:
        return None

    base = os.getenv("LLM_BASE_URL", "https://api.deepseek.com").rstrip("/")
    model = os.getenv("LLM_MODEL", "deepseek-chat")
    url = f"{base}/v1/chat/completions"

    body = {
        "model": model,
        "stream": True,
        "temperature": 0.4,
        "messages": [
            {
                "role": "system",
                "content": "你是资深番茄植保专家，回答简洁、分条、可操作，给出药剂与环境调控建议。",
            },
            {"role": "user", "content": prompt},
        ],
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            for raw in resp:
                line = raw.decode("utf-8", errors="ignore").strip()
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                try:
                    obj = json.loads(data)
                    delta = obj["choices"][0]["delta"].get("content") or ""
                except (KeyError, IndexError, json.JSONDecodeError):
                    continue
                if delta:
                    yield delta
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
        yield f"\n\n> LLM 调用失败（{exc}），已回退知识库处方。\n\n"
        yield from knowledge_expert_response({}, "").split()  # won't be used; caller handles


def stream_expert_response(diagnosis: dict, user_message: str):
    """SSE 流式生成器：优先 LLM，否则知识库。"""
    prompt = build_expert_prompt(diagnosis, user_message)
    api_key = os.getenv("LLM_API_KEY", "").strip()

    if api_key:
        try:
            base = os.getenv("LLM_BASE_URL", "https://api.deepseek.com").rstrip("/")
            model = os.getenv("LLM_MODEL", "deepseek-chat")
            url = f"{base}/v1/chat/completions"
            body = {
                "model": model,
                "stream": True,
                "temperature": 0.4,
                "messages": [
                    {
                        "role": "system",
                        "content": "你是资深番茄植保专家，回答简洁、分条、可操作。",
                    },
                    {"role": "user", "content": prompt},
                ],
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(body).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=90) as resp:
                for raw in resp:
                    line = raw.decode("utf-8", errors="ignore").strip()
                    if not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        obj = json.loads(data)
                        delta = obj["choices"][0]["delta"].get("content") or ""
                    except (KeyError, IndexError, json.JSONDecodeError):
                        continue
                    if delta:
                        yield f"data: {json.dumps({'content': delta}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
            return
        except Exception as exc:
            fallback = (
                f"> LLM 暂不可用（{exc}），以下为知识库处方：\n\n"
                + knowledge_expert_response(diagnosis, user_message)
            )
            for i in range(0, len(fallback), 8):
                chunk = fallback[i : i + 8]
                yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
                time.sleep(0.008)
            yield "data: [DONE]\n\n"
            return

    text = knowledge_expert_response(diagnosis, user_message)
    for i in range(0, len(text), 6):
        chunk = text[i : i + 6]
        yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
        time.sleep(0.006)
    yield "data: [DONE]\n\n"


# 兼容旧名称
def stream_mock_response(diagnosis: dict, user_message: str):
    yield from stream_expert_response(diagnosis, user_message)


def mock_expert_response(diagnosis: dict, user_message: str) -> str:
    return knowledge_expert_response(diagnosis, user_message)
