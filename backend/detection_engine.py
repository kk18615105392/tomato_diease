"""YOLOv5 (MLCA) 目标检测推理引擎。"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import torch

from model_registry import get_detection_model

BASE_DIR = Path(__file__).resolve().parent
YOLO_ROOT = BASE_DIR / "vendor" / "MLCA"

_loaded_models: dict[str, object] = {}
_torch_load_patched = False


def _ensure_yolo_path() -> None:
    global _torch_load_patched
    root = str(YOLO_ROOT.resolve())
    if root not in sys.path:
        sys.path.insert(0, root)
    if not _torch_load_patched:
        original_load = torch.load

        def _patched_load(*args, **kwargs):
            kwargs.setdefault("weights_only", False)
            return original_load(*args, **kwargs)

        torch.load = _patched_load  # type: ignore[method-assign]
        _torch_load_patched = True


def _load_model(weights_path: str):
    _ensure_yolo_path()
    from models.experimental import attempt_load

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = attempt_load(weights_path, map_location=device, fuse=False)
    model.eval()
    for module in model.modules():
        if module.__class__.__name__ == "MLCA" and not hasattr(module, "local_weight"):
            module.local_weight = 0.5
    stride = int(model.stride.max()) if hasattr(model, "stride") else 32
    names = model.names if hasattr(model, "names") else {}
    return model, device, stride, names


def get_model(model_key: str | None = None):
    meta = get_detection_model(model_key)
    if meta is None:
        raise FileNotFoundError("未找到可用的 YOLO 检测权重，请检查 model/ 目录")

    key = meta["key"]
    if key not in _loaded_models:
        model, device, stride, names = _load_model(meta["weights"])
        _loaded_models[key] = {
            "model": model,
            "device": device,
            "stride": stride,
            "names": names,
            "meta": meta,
        }
    return _loaded_models[key]


def run_detection(
    image_path: str,
    model_key: str | None = None,
    conf_thres: float = 0.25,
    iou_thres: float = 0.45,
    imgsz: int = 640,
) -> dict:
    _ensure_yolo_path()
    from PIL import Image
    from utils.augmentations import letterbox
    from utils.general import non_max_suppression, scale_coords

    bundle = get_model(model_key)
    model = bundle["model"]
    device = bundle["device"]
    stride = bundle["stride"]
    names = bundle["names"]
    meta = bundle["meta"]
    dataset = meta.get("dataset") or "merged9"

    from class_names import resolve_class_name, resolve_class_names

    img0 = np.array(Image.open(image_path).convert("RGB"))
    h0, w0 = img0.shape[:2]

    img = letterbox(img0, imgsz, stride=stride, auto=True)[0]
    img = img.transpose((2, 0, 1))[::-1]
    img = np.ascontiguousarray(img)
    im = torch.from_numpy(img).to(device).float() / 255.0
    im = im.unsqueeze(0)

    t0 = time.perf_counter()
    with torch.no_grad():
        pred = model(im)[0]
    pred = non_max_suppression(pred, conf_thres, iou_thres, max_det=300)
    infer_ms = round((time.perf_counter() - t0) * 1000, 1)

    detections: list[dict] = []
    if pred[0] is not None and len(pred[0]):
        det = pred[0].clone()
        det[:, :4] = scale_coords(im.shape[2:], det[:, :4], img0.shape).round()
        for *xyxy, conf, cls in det.tolist():
            x1, y1, x2, y2 = xyxy
            cls_id = int(cls)
            raw = names[cls_id] if isinstance(names, dict) else names[cls_id]
            label = resolve_class_name(cls_id, str(raw), dataset)
            detections.append(
                {
                    "label": str(label),
                    "confidence": round(float(conf), 4),
                    "bbox": {
                        "x": round(max(0.0, x1 / w0), 4),
                        "y": round(max(0.0, y1 / h0), 4),
                        "width": round(min(1.0, (x2 - x1) / w0), 4),
                        "height": round(min(1.0, (y2 - y1) / h0), 4),
                    },
                }
            )

    return {
        "detections": detections,
        "model_key": meta["key"],
        "model_label": meta["label"],
        "infer_ms": infer_ms,
        "class_names": resolve_class_names(names, dataset),
    }
