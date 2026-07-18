"""Ultralytics YOLOv8 检测推理（消融实验 E1–E11 权重）。"""

from __future__ import annotations

import os
import time
from pathlib import Path

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

_loaded: dict[str, object] = {}


def run_detection_v8(
    image_path: str,
    weights_path: str,
    conf_thres: float = 0.25,
    imgsz: int = 640,
    dataset: str | None = None,
) -> dict:
    import sys

    try:
        from ultralytics_patch import ensure_ultralytics_custom

        ensure_ultralytics_custom()
        from ultralytics import YOLO
    except ImportError as exc:
        py = sys.executable
        raise ImportError(
            f"{exc}。YOLOv8 消融实验需要 ultralytics。"
            f"请确认后端使用的 Python 为 pytorch_gpu 并已安装："
            f'"{py}" -m pip install ultralytics'
        ) from exc

    from class_names import resolve_class_name, resolve_class_names

    if weights_path not in _loaded:
        _loaded[weights_path] = YOLO(weights_path)
    model = _loaded[weights_path]

    t0 = time.perf_counter()
    results = model.predict(
        source=image_path,
        conf=conf_thres,
        imgsz=imgsz,
        verbose=False,
    )
    infer_ms = round((time.perf_counter() - t0) * 1000, 1)

    detections: list[dict] = []
    names = model.names or {}
    if results:
        r0 = results[0]
        h0, w0 = r0.orig_shape[:2]
        if r0.boxes is not None and len(r0.boxes):
            xyxy = r0.boxes.xyxy.cpu().tolist()
            confs = r0.boxes.conf.cpu().tolist()
            clss = r0.boxes.cls.int().cpu().tolist()
            for (x1, y1, x2, y2), conf, cls_id in zip(xyxy, confs, clss):
                cid = int(cls_id)
                raw = names[cid] if isinstance(names, dict) else names[cid]
                label = resolve_class_name(cid, str(raw), dataset)
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

    class_names = resolve_class_names(names, dataset)
    return {
        "detections": detections,
        "infer_ms": infer_ms,
        "class_names": class_names,
    }
