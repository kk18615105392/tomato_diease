"""扫描 model/ 目录，注册 YOLO 检测实验权重与训练指标。"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import yaml

from class_names import task_info_for_dataset

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
MODEL_ROOT = PROJECT_ROOT / "model"

DEFAULT_DETECTION_MODEL = "ablation-E8b-v2"

# 11 组消融实验 · 改进要点精简名
EXPERIMENT_IMPROVEMENTS: dict[str, str] = {
    "E1": "YOLOv8n基准",
    "E2": "MLCA四层+SPPF",
    "E3": "YOLOv8s+MLCA教师",
    "E4": "baseline←E2蒸馏",
    "E5": "MLCA←E2蒸馏",
    "E6": "baseline←E3蒸馏",
    "E7a": "CBAM串行k=7",
    "E7b": "CBAM-Lite×2",
    "E7c": "SA-first+ECA",
    "E7d": "CBAM-T k=3",
    "E8a": "P2四尺度头",
    "E8b": "Copy-Paste增强",
    "E8c": "P2+增强",
    "E9": "PFA并行注意力",
    "E10": "CPR蒸馏",
    "E11": "CAKD双教师",
}

ABLATION_ORDER = list(EXPERIMENT_IMPROVEMENTS.keys())

DATASET_SHORT: dict[str, str] = {
    "v2": "整叶v2",
    "merged9": "小病斑m9",
}

MODEL_LABELS: dict[str, str] = {
    "tomato-baseline": "YOLOv5·MobileNetV3基准",
    "tomato-mlca-paper": "YOLOv5·MLCA v1",
    "tomato-mlca-paper2": "YOLOv5·MLCA v2",
    "tomato-mlca2": "YOLOv5·MLCA #2",
    "tomato-mlca3": "YOLOv5·MLCA #3",
    "tomato-mlca4": "YOLOv5·MLCA #4",
    "tomato-mlca5": "YOLOv5·MLCA #5",
    "tomato-run-test": "YOLOv5·MLCA测试",
    "tomato-se": "YOLOv5·SE注意力",
}


def _load_ablation_manifest() -> dict:
    path = MODEL_ROOT / "ablation_manifest.json"
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _manifest_entry(key: str, manifest: dict) -> dict | None:
    for item in manifest.get("models", []):
        if item.get("key") == key:
            return item
    return None


def build_ablation_label(exp_id: str, dataset: str, improvement: str | None = None) -> str:
    imp = improvement or EXPERIMENT_IMPROVEMENTS.get(exp_id, exp_id)
    ds = DATASET_SHORT.get(dataset, dataset or "")
    return f"{exp_id}·{imp}·{ds}" if ds else f"{exp_id}·{imp}"


def _parse_ablation_key(key: str) -> tuple[str, str]:
    """ablation-E8b-v2 -> (E8b, v2)"""
    m = re.match(r"ablation-(E[\w]+)-(\w+)$", key)
    if m:
        return m.group(1), m.group(2)
    return "", ""


def _sort_key(model: dict) -> tuple:
    key = model["key"]
    if key.startswith("ablation-"):
        exp_id = model.get("exp_id") or _parse_ablation_key(key)[0]
        dataset = model.get("dataset") or _parse_ablation_key(key)[1]
        try:
            exp_idx = ABLATION_ORDER.index(exp_id)
        except ValueError:
            exp_idx = 99
        ds_idx = 0 if dataset == "v2" else 1 if dataset == "merged9" else 2
        return (0, exp_idx, ds_idx, key)
    return (1, 99, 99, key)


def _read_opt(exp_dir: Path) -> dict:
    opt_path = exp_dir / "opt.yaml"
    if not opt_path.exists():
        return {}
    with opt_path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _read_last_metrics(exp_dir: Path) -> dict:
    csv_path = exp_dir / "results.csv"
    if not csv_path.exists():
        return {}
    with csv_path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, skipinitialspace=True))
    if not rows:
        return {}
    last = rows[-1]
    return {
        "precision": float(last.get("metrics/precision", 0) or 0),
        "recall": float(last.get("metrics/recall", 0) or 0),
        "map50": float(last.get("metrics/mAP_0.5", 0) or 0),
        "map50_95": float(last.get("metrics/mAP_0.5:0.95", 0) or 0),
        "epochs": int(float(last.get("epoch", 0) or 0)) + 1,
    }


def scan_detection_models() -> list[dict]:
    if not MODEL_ROOT.is_dir():
        return []

    manifest = _load_ablation_manifest()
    models: list[dict] = []

    for exp_dir in MODEL_ROOT.iterdir():
        if not exp_dir.is_dir():
            continue
        weights = exp_dir / "weights" / "best.pt"
        if not weights.is_file():
            continue

        opt = _read_opt(exp_dir)
        metrics = _read_last_metrics(exp_dir)
        key = exp_dir.name
        cfg = opt.get("cfg", "")
        engine = opt.get("engine", "yolov5")
        exp_id = opt.get("exp_id", "") or _parse_ablation_key(key)[0]
        dataset = opt.get("dataset", "") or _parse_ablation_key(key)[1]

        precision = metrics.get("precision", 0.0)
        recall = metrics.get("recall", 0.0)
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

        entry = _manifest_entry(key, manifest)
        improvement = entry.get("improvement", "") if entry else ""
        recommend = entry.get("recommend", "") if entry else ""
        test_map50 = entry.get("test_map50") if entry else None

        if key.startswith("ablation-"):
            label = build_ablation_label(exp_id, dataset, improvement or None)
            group = "ablation"
        else:
            label = MODEL_LABELS.get(key, key)
            group = "legacy"

        map50 = metrics.get("map50", 0.0)
        if not map50 and test_map50 is not None:
            map50 = float(test_map50)

        task = task_info_for_dataset(dataset) if dataset else {}

        models.append(
            {
                "key": key,
                "label": label,
                "improvement": improvement or EXPERIMENT_IMPROVEMENTS.get(exp_id, ""),
                "recommend": recommend,
                "group": group,
                # 相对路径对外展示，避免暴露本机用户目录
                "weights": str(weights.relative_to(PROJECT_ROOT)).replace("\\", "/"),
                "cfg": cfg,
                "engine": engine,
                "dataset": dataset,
                "exp_id": exp_id,
                "task_type": task.get("task_type", ""),
                "task_label": task.get("task_label", ""),
                "task_hint": task.get("hint", ""),
                "upload_tip": task.get("upload_tip", ""),
                "imgsz": int(opt.get("imgsz", 640) or 640),
                "epochs": metrics.get("epochs", int(opt.get("epochs", 0) or 0)),
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1": round(f1, 4),
                "map50": round(map50, 4),
                "map50_95": round(metrics.get("map50_95", 0.0), 4),
                "test_map50": round(float(test_map50), 4) if test_map50 is not None else None,
                "is_default": key == DEFAULT_DETECTION_MODEL,
            }
        )

    models.sort(key=_sort_key)

    if models and not any(m["is_default"] for m in models):
        default_key = manifest.get("default_v2")
        if default_key and any(m["key"] == default_key for m in models):
            for m in models:
                m["is_default"] = m["key"] == default_key
        else:
            models[0]["is_default"] = True
    return models


def get_detection_model(key: str | None = None) -> dict | None:
    models = scan_detection_models()
    if not models:
        return None
    if not key:
        return next((m for m in models if m["is_default"]), models[0])
    return next((m for m in models if m["key"] == key), None)


def resolve_weights_path(meta: dict) -> str:
    """将 registry 中的相对 weights 转为绝对路径供推理加载。"""
    p = Path(meta["weights"])
    if not p.is_absolute():
        p = PROJECT_ROOT / p
    return str(p.resolve())
