import os
import sys
import uuid
from pathlib import Path

from flask import Flask, Response, jsonify, request
from flask_cors import CORS
from werkzeug.utils import secure_filename

from auth import register_auth_routes
from expert import stream_expert_response
from grad_cam import generate_gradcam
from dsi_predictor import predict_dsi_forecast
from heterogeneous_stats import get_heterogeneous_stats
from model_metrics import get_all_metrics
from predictors import MODE_HANDLERS, VALID_MODES, list_detection_models
from reports import register_report_routes
from wiki import register_wiki_routes

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = str(UPLOAD_DIR)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
CORS(app, resources={r"/api/*": {"origins": "*"}})
register_auth_routes(app)
register_report_routes(app)
register_wiki_routes(app)


def _runtime_info() -> dict:
    ultralytics_ok = False
    ultralytics_error = ""
    custom_ok = False
    try:
        from ultralytics_patch import custom_modules_ready, ensure_ultralytics_custom

        ensure_ultralytics_custom()
        import ultralytics  # noqa: F401

        ultralytics_ok = True
        custom_ok = custom_modules_ready()
    except Exception as exc:
        ultralytics_error = str(exc)
    return {
        "python": sys.executable,
        "ultralytics_ok": ultralytics_ok,
        "ultralytics_custom_ok": custom_ok,
        "ultralytics_error": ultralytics_error,
    }


@app.get("/")
def index():
    return (
        """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>Tomato AI API</title>
<style>
body{font-family:Microsoft YaHei,sans-serif;background:#0a3f27;color:#fff;display:flex;min-height:100vh;align-items:center;justify-content:center;margin:0}
.card{background:rgba(255,255,255,.96);color:#14532d;padding:28px 32px;border-radius:14px;max-width:460px;line-height:1.6}
a{color:#166534;font-weight:700}
code{background:#ecfdf5;padding:2px 6px;border-radius:4px}
</style></head><body><div class="card">
<h2 style="margin:0 0 8px">Tomato AI 后端已启动</h2>
<p>这是 API 服务（端口 5000），页面请打开前端：</p>
<p><a href="http://127.0.0.1:5173/login">http://127.0.0.1:5173/login</a></p>
<p>若打不开，请另开终端执行：<br><code>cd frontend</code><br><code>npm run dev</code></p>
</div></body></html>""",
        200,
        {"Content-Type": "text/html; charset=utf-8"},
    )


@app.get("/api/health")
def health():
    info = _runtime_info()
    return jsonify(
        {
            "status": "ok" if info["ultralytics_ok"] else "degraded",
            **info,
        }
    )


@app.post("/api/upload")
def upload_image():
    if "image" not in request.files:
        return jsonify({"error": "缺少 image 文件字段"}), 400

    image = request.files["image"]
    if not image.filename:
        return jsonify({"error": "文件名为空"}), 400

    image_id = uuid.uuid4().hex
    safe_name = secure_filename(image.filename)
    save_name = f"{image_id}_{safe_name}"
    save_path = UPLOAD_DIR / save_name
    image.save(save_path)

    return jsonify(
        {
            "image_id": image_id,
            "image_path": str(save_path.resolve()),
        }
    )


def _find_image_path(image_id: str) -> Path | None:
    for path in UPLOAD_DIR.glob(f"{image_id}_*"):
        if path.is_file():
            return path
    return None


@app.post("/api/diagnose")
def diagnose():
    data = request.get_json(silent=True) or {}
    image_id = data.get("image_id")
    mode = data.get("mode", "classification")

    if not image_id:
        return jsonify({"error": "缺少 image_id"}), 400
    if mode not in VALID_MODES:
        return jsonify({"error": f"无效的 mode，可选值: {sorted(VALID_MODES)}"}), 400

    image_path = _find_image_path(image_id)
    if image_path is None:
        return jsonify({"error": f"未找到 image_id={image_id} 对应的图片"}), 404

    handler = MODE_HANDLERS[mode]
    extra = {"detection_model": data.get("detection_model")}
    result = handler(image_id, str(image_path), **extra)
    return jsonify(result)


@app.post("/api/compare")
def compare():
    data = request.get_json(silent=True) or {}
    image_ids = data.get("image_ids", [])
    mode = data.get("mode", "detection")
    labels = data.get("labels", [])

    if not isinstance(image_ids, list) or len(image_ids) < 2 or len(image_ids) > 4:
        return jsonify({"error": "请提供 2～4 张图片的 image_id"}), 400
    if mode not in VALID_MODES:
        return jsonify({"error": f"无效的 mode，可选值: {sorted(VALID_MODES)}"}), 400

    items = []
    dsi_values = []
    for idx, image_id in enumerate(image_ids):
        image_path = _find_image_path(image_id)
        if image_path is None:
            return jsonify({"error": f"未找到 image_id={image_id} 对应的图片"}), 404

        extra = {"detection_model": data.get("detection_model")}
        result = MODE_HANDLERS[mode](image_id, str(image_path), **extra)
        label = labels[idx] if idx < len(labels) else f"样本 {idx + 1}"
        items.append({"label": label, "image_id": image_id, "result": result})

        if result.get("mode") == "segmentation":
            dsi_values.append(result.get("dsi", 0))

    trend_summary = "已完成多图对比分析"
    if len(dsi_values) >= 2:
        diff = dsi_values[-1] - dsi_values[0]
        direction = "上升" if diff > 0 else "下降" if diff < 0 else "持平"
        trend_summary = (
            f"DSI 从 {dsi_values[0]}% 变化至 {dsi_values[-1]}%（{direction} {abs(diff):.1f}%），"
            "建议持续监测病斑扩展趋势"
        )

    return jsonify({"mode": mode, "items": items, "trend_summary": trend_summary})


@app.post("/api/predict_dsi")
def predict_dsi():
    data = request.get_json(silent=True) or {}
    history = data.get("history", [])
    if not isinstance(history, list) or len(history) < 2:
        return jsonify({"error": "至少需要 2 个历史 DSI 数据点"}), 400
    result = predict_dsi_forecast(history)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


@app.post("/api/gradcam")
def gradcam():
    data = request.get_json(silent=True) or {}
    image_id = data.get("image_id")
    if not image_id:
        return jsonify({"error": "缺少 image_id"}), 400
    image_path = _find_image_path(image_id)
    if image_path is None:
        return jsonify({"error": f"未找到 image_id={image_id} 对应的图片"}), 404
    return jsonify(generate_gradcam(str(image_path)))


@app.get("/api/model_metrics")
def model_metrics():
    return jsonify(get_all_metrics())


@app.get("/api/detection_models")
def detection_models():
    models = list_detection_models()
    default = next((m["key"] for m in models if m.get("is_default")), None)
    return jsonify({"models": models, "default": default})


@app.get("/api/stats/heterogeneous")
def heterogeneous_stats():
    return jsonify(get_heterogeneous_stats())


@app.post("/api/chat_expert")
def chat_expert():
    data = request.get_json(silent=True) or {}
    diagnosis = data.get("diagnosis", {})
    user_message = data.get("message", "")
    return Response(
        stream_expert_response(diagnosis, user_message),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


if __name__ == "__main__":
    from auth import init_db

    init_db()
    port = int(os.getenv("PORT", "5000"))
    info = _runtime_info()
    print(f"[backend] Python: {info['python']}")
    print(f"[backend] auth DB: {BASE_DIR / 'data' / 'users.db'}")
    if info["ultralytics_ok"]:
        custom = "已注册 MLCA/CBAM/PFA" if info.get("ultralytics_custom_ok") else "自定义模块待注册"
        print(f"[backend] ultralytics: OK ({custom})")
    else:
        print(f"[backend] ultralytics: 未安装 — {info['ultralytics_error']}")
        print("[backend] 请在当前环境执行: pip install ultralytics")
    # Windows 下 debug 重载器可能拉起 base 环境子进程，导致 E1–E11 报 No module named ultralytics
    app.run(host="0.0.0.0", port=port, debug=True, use_reloader=False)
