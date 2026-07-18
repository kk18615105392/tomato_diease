"""推断函数：三维诊断均基于真实 YOLO 检测结果（分类/分割为检测代理，无独立 .pth 时）。"""

from __future__ import annotations

import base64
from collections import defaultdict

from detection_engine import run_detection
from model_registry import DEFAULT_DETECTION_MODEL, get_detection_model, scan_detection_models


def _run_detection_router(image_path: str, model_key: str | None, conf: float = 0.25) -> dict:
    meta = get_detection_model(model_key)
    if meta is None:
        raise FileNotFoundError("未找到检测模型")
    if meta.get("engine") == "ultralytics":
        from detection_engine_v8 import run_detection_v8

        out = run_detection_v8(
            image_path,
            meta["weights"],
            conf_thres=conf,
            imgsz=meta.get("imgsz", 640),
            dataset=meta.get("dataset"),
        )
        return {
            **out,
            "model_key": meta["key"],
            "model_label": meta["label"],
            "dataset": meta.get("dataset", ""),
            "task_type": meta.get("task_type", ""),
            "task_label": meta.get("task_label", ""),
            "task_hint": meta.get("task_hint", ""),
        }
    out = run_detection(image_path, model_key=model_key, conf_thres=conf)
    return out


def _aggregate_classes(detections: list[dict]) -> list[dict]:
    buckets: dict[str, list[float]] = defaultdict(list)
    for det in detections:
        buckets[str(det.get("label", "未知"))].append(float(det.get("confidence", 0)))
    ranked = []
    for label, confs in buckets.items():
        ranked.append(
            {
                "label": label,
                "count": len(confs),
                "confidence": round(max(confs), 4),
                "mean_confidence": round(sum(confs) / len(confs), 4),
            }
        )
    ranked.sort(key=lambda x: (x["confidence"], x["count"]), reverse=True)
    return ranked


def _severity_from_dsi(dsi: float) -> str:
    if dsi < 5:
        return "健康/极轻"
    if dsi < 15:
        return "轻度发病"
    if dsi < 30:
        return "中度发病"
    return "重度发病"


def _mask_from_detections(detections: list[dict]) -> str:
    """按真实检测框生成半透明 SVG 掩码。"""
    if not detections:
        svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"></svg>"""
        return base64.b64encode(svg.encode("utf-8")).decode("utf-8")

    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" preserveAspectRatio="none">'
    ]
    for det in detections:
        box = det.get("bbox") or {}
        x = float(box.get("x", 0)) * 100
        y = float(box.get("y", 0)) * 100
        w = float(box.get("width", 0)) * 100
        h = float(box.get("height", 0)) * 100
        conf = float(det.get("confidence", 0.5))
        alpha = round(0.25 + 0.45 * conf, 2)
        parts.append(
            f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" '
            f'rx="1.5" fill="rgba(220,38,38,{alpha})" />'
        )
    parts.append("</svg>")
    return base64.b64encode("".join(parts).encode("utf-8")).decode("utf-8")


def _estimate_dsi(detections: list[dict]) -> float:
    """用检测框覆盖面积估算病情指数 DSI（%）。"""
    if not detections:
        return 0.0
    area = 0.0
    for det in detections:
        box = det.get("bbox") or {}
        area += float(box.get("width", 0)) * float(box.get("height", 0))
    # 交叠近似用饱和函数，避免简单相加超 100
    dsi = (1 - (1 - min(area, 1.0)) ** 1.2) * 100
    return round(min(100.0, max(0.0, dsi)), 1)


def _predict_classification(
    image_id: str,
    image_path: str,
    detection_model: str | None = None,
    **_kwargs,
) -> dict:
    """快速定性：复用 YOLO 检测，取最高置信度类别作为病害名。"""
    model_key = detection_model or DEFAULT_DETECTION_MODEL
    try:
        result = _run_detection_router(image_path, model_key=model_key, conf=0.2)
        ranked = _aggregate_classes(result.get("detections") or [])
        if not ranked:
            return {
                "mode": "classification",
                "image_id": image_id,
                "disease_name": "未检出病害",
                "confidence": 0.0,
                "top_classes": [],
                "model_key": result.get("model_key", model_key),
                "model_label": result.get("model_label", ""),
                "infer_ms": result.get("infer_ms"),
                "note": f"基于检测模型定性 · {result.get('model_label', model_key)} · 未检出目标",
            }
        top = ranked[0]
        return {
            "mode": "classification",
            "image_id": image_id,
            "disease_name": top["label"],
            "confidence": top["confidence"],
            "top_classes": ranked[:5],
            "model_key": result.get("model_key", model_key),
            "model_label": result.get("model_label", ""),
            "infer_ms": result.get("infer_ms"),
            "note": (
                f"基于检测模型定性 · {result.get('model_label', model_key)} · "
                f"主类「{top['label']}」×{top['count']} · 推理 {result.get('infer_ms', 0)}ms"
            ),
        }
    except Exception as exc:
        return {
            "mode": "classification",
            "image_id": image_id,
            "disease_name": "推理失败",
            "confidence": 0.0,
            "error": str(exc),
            "note": f"定性推理失败：{exc}",
        }


def _predict_detection(
    image_id: str,
    image_path: str,
    detection_model: str | None = None,
    **_kwargs,
) -> dict:
    model_key = detection_model or DEFAULT_DETECTION_MODEL
    try:
        result = _run_detection_router(image_path, model_key=model_key)
        count = len(result["detections"])
        note = (
            f"精准目标定位完成 · {result['model_label']} · "
            f"检测到 {count} 个目标 · 推理 {result['infer_ms']}ms"
        )
        return {
            "mode": "detection",
            "image_id": image_id,
            "detections": result["detections"],
            "model_key": result["model_key"],
            "model_label": result["model_label"],
            "infer_ms": result["infer_ms"],
            "note": note,
        }
    except Exception as exc:
        return {
            "mode": "detection",
            "image_id": image_id,
            "detections": [],
            "model_key": model_key,
            "error": str(exc),
            "note": f"检测推理失败：{exc}",
        }


def _predict_segmentation(
    image_id: str,
    image_path: str,
    detection_model: str | None = None,
    **_kwargs,
) -> dict:
    """严重度定量：用检测框面积估算 DSI，并生成真实框掩码（无独立分割权重时）。"""
    model_key = detection_model or DEFAULT_DETECTION_MODEL
    try:
        result = _run_detection_router(image_path, model_key=model_key, conf=0.2)
        detections = result.get("detections") or []
        ranked = _aggregate_classes(detections)
        disease = ranked[0]["label"] if ranked else "未检出病害"
        dsi = _estimate_dsi(detections)
        level = _severity_from_dsi(dsi)
        return {
            "mode": "segmentation",
            "image_id": image_id,
            "disease_name": disease,
            "dsi": dsi,
            "severity_level": level,
            "mask_base64": _mask_from_detections(detections),
            "detections": detections,
            "model_key": result.get("model_key", model_key),
            "model_label": result.get("model_label", ""),
            "infer_ms": result.get("infer_ms"),
            "note": (
                f"基于检测框估算 DSI · {result.get('model_label', model_key)} · "
                f"{disease} · DSI {dsi}%（{level}）· 推理 {result.get('infer_ms', 0)}ms"
            ),
        }
    except Exception as exc:
        return {
            "mode": "segmentation",
            "image_id": image_id,
            "disease_name": "推理失败",
            "dsi": 0.0,
            "severity_level": "未知",
            "mask_base64": _mask_from_detections([]),
            "error": str(exc),
            "note": f"严重度评估失败：{exc}",
        }


def list_detection_models() -> list[dict]:
    return scan_detection_models()


MODE_HANDLERS = {
    "classification": _predict_classification,
    "detection": _predict_detection,
    "segmentation": _predict_segmentation,
}

VALID_MODES = frozenset(MODE_HANDLERS.keys())
