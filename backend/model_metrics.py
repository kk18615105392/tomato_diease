"""模型训练指标（检测模式对接 model/ 真实 results.csv + 消融实验表）"""

from __future__ import annotations

from model_registry import (
    ABLATION_ORDER,
    DEFAULT_DETECTION_MODEL,
    scan_detection_models,
)

DATASET_DESC = {
    "v2": "Tomato.v2 整叶 10 类 · 18,405 张",
    "merged9": "merged9 小病斑 9 类 · 7,382 张",
    "legacy": "tomato.v1 YOLOv5 历史权重",
}

ENGINE_PARAMS_M = {
    "ultralytics": 3.0,
    "yolov5": 6.7,
}

MODEL_METRICS = {
    "classification": {
        "model_name": "tv_lite_kd (分类)",
        "weights": "tv_lite_kd_test_best.pth",
        "dataset": "番茄叶部病害数据集",
        "epochs": 120,
        "precision": 0.952,
        "recall": 0.938,
        "f1": 0.945,
        "accuracy": 0.961,
        "params_m": 1.2,
        "inference_ms": 18,
        "per_class": [
            {"name": "早疫病", "precision": 0.96, "recall": 0.94, "f1": 0.95},
            {"name": "晚疫病", "precision": 0.94, "recall": 0.92, "f1": 0.93},
            {"name": "叶霉病", "precision": 0.95, "recall": 0.93, "f1": 0.94},
            {"name": "健康", "precision": 0.97, "recall": 0.98, "f1": 0.975},
        ],
        "confusion": [
            [94, 2, 1, 3],
            [3, 92, 2, 3],
            [2, 3, 93, 2],
            [1, 2, 1, 96],
        ],
        "labels": ["早疫病", "晚疫病", "叶霉病", "健康"],
    },
    "segmentation": {
        "model_name": "（已弃用）DeepLabV3+ 分割",
        "weights": "—",
        "dataset": "分割模式已停用；保留字段仅兼容旧 API",
        "epochs": 0,
        "precision": 0.0,
        "recall": 0.0,
        "f1": 0.0,
        "miou": 0.0,
        "dice": 0.0,
        "params_m": 0.0,
        "inference_ms": 0,
        "deprecated": True,
    },
}


def _params_m(engine: str) -> float:
    return ENGINE_PARAMS_M.get(engine, 6.7)


def _dataset_desc(dataset: str, group: str) -> str:
    if dataset in DATASET_DESC:
        return DATASET_DESC[dataset]
    if group == "legacy":
        return DATASET_DESC["legacy"]
    return "番茄病斑目标检测集"


def _test_sort_key(m: dict) -> float:
    test = m.get("test_map50")
    if test is not None:
        return float(test)
    return float(m.get("map50") or 0)


def _rank_variants(models: list[dict]) -> list[dict]:
    ranked = sorted(models, key=_test_sort_key, reverse=True)
    rows: list[dict] = []
    for idx, m in enumerate(ranked, start=1):
        row = _variant_row(m)
        row["rank"] = idx
        row["test_score"] = round(_test_sort_key(m), 4)
        rows.append(row)
    return rows


def _variant_row(m: dict) -> dict:
    return {
        "key": m["key"],
        "label": m["label"],
        "exp_id": m.get("exp_id", ""),
        "dataset": m.get("dataset", ""),
        "group": m.get("group", ""),
        "engine": m.get("engine", ""),
        "recommend": m.get("recommend", ""),
        "improvement": m.get("improvement", ""),
        "epochs": m.get("epochs", 0),
        "map50": m["map50"],
        "map50_95": m["map50_95"],
        "test_map50": m.get("test_map50"),
        "precision": m["precision"],
        "recall": m["recall"],
        "f1": m["f1"],
        "is_default": m.get("is_default", False),
    }


def _build_test_ranking(models: list[dict]) -> dict:
    ablation = [m for m in models if m.get("group") == "ablation" and m.get("test_map50") is not None]
    ranked = sorted(ablation, key=_test_sort_key, reverse=True)
    return {
        "labels": [m["label"] for m in ranked],
        "test_map50": [m["test_map50"] for m in ranked],
        "datasets": [m.get("dataset", "") for m in ranked],
    }


def _build_ablation_chart(models: list[dict]) -> dict:
    ablation = [m for m in models if m.get("group") == "ablation"]
    by_exp_ds: dict[tuple[str, str], dict] = {}
    for m in ablation:
        exp_id = m.get("exp_id") or ""
        dataset = m.get("dataset") or ""
        if exp_id and dataset:
            by_exp_ds[(exp_id, dataset)] = m

    v2_vals: list[float | None] = []
    m9_vals: list[float | None] = []
    test_v2: list[float | None] = []
    test_m9: list[float | None] = []
    for exp_id in ABLATION_ORDER:
        v2 = by_exp_ds.get((exp_id, "v2"))
        m9 = by_exp_ds.get((exp_id, "merged9"))
        v2_vals.append(v2["map50"] if v2 else None)
        m9_vals.append(m9["map50"] if m9 else None)
        test_v2.append(v2.get("test_map50") if v2 else None)
        test_m9.append(m9.get("test_map50") if m9 else None)

    return {
        "experiments": ABLATION_ORDER,
        "v2": v2_vals,
        "merged9": m9_vals,
        "test_v2": test_v2,
        "test_merged9": test_m9,
    }


def _build_detection_metrics() -> dict:
    models = scan_detection_models()
    if not models:
        return {
            "model_name": "YOLO 目标检测",
            "weights": "model/*/weights/best.pt",
            "dataset": "—",
            "engine": "",
            "epochs": 0,
            "precision": 0,
            "recall": 0,
            "f1": 0,
            "map50": 0,
            "map50_95": 0,
            "test_map50": None,
            "params_m": 3.0,
            "inference_ms": 0,
            "variants": [],
            "ablation_chart": _build_ablation_chart([]),
            "test_ranking": _build_test_ranking([]),
            "summary": {"total": 0, "ablation": 0, "legacy": 0},
        }

    default = next(
        (m for m in models if m["key"] == DEFAULT_DETECTION_MODEL),
        next((m for m in models if m.get("is_default")), models[0]),
    )
    variants = _rank_variants(models)
    ablation = [m for m in models if m.get("group") == "ablation"]
    legacy = [m for m in models if m.get("group") == "legacy"]

    v2_pool = [m for m in ablation if m.get("dataset") == "v2" and m.get("test_map50") is not None]
    m9_pool = [m for m in ablation if m.get("dataset") == "merged9" and m.get("test_map50") is not None]
    best_v2 = max(v2_pool, key=_test_sort_key, default=None)
    best_m9 = max(m9_pool, key=_test_sort_key, default=None)

    engine = default.get("engine", "ultralytics")
    dataset = default.get("dataset", "v2")
    return {
        "model_name": default["label"],
        "weights": f"model/{default['key']}/weights/best.pt",
        "dataset": _dataset_desc(dataset, default.get("group", "")),
        "engine": engine,
        "epochs": default["epochs"],
        "precision": default["precision"],
        "recall": default["recall"],
        "f1": default["f1"],
        "map50": default["map50"],
        "map50_95": default["map50_95"],
        "test_map50": default.get("test_map50"),
        "params_m": _params_m(engine),
        "inference_ms": 10 if engine == "ultralytics" else 80,
        "variants": variants,
        "ablation_chart": _build_ablation_chart(models),
        "test_ranking": _build_test_ranking(models),
        "summary": {
            "total": len(models),
            "ablation": len(ablation),
            "legacy": len(legacy),
            "best_v2": best_v2["label"] if best_v2 else None,
            "best_merged9": best_m9["label"] if best_m9 else None,
            "best_v2_test": round(float(best_v2["test_map50"]), 4) if best_v2 else None,
            "best_merged9_test": round(float(best_m9["test_map50"]), 4) if best_m9 else None,
            "default_key": default["key"],
        },
    }


def get_all_metrics():
    metrics = dict(MODEL_METRICS)
    metrics["detection"] = _build_detection_metrics()
    det = metrics["detection"]
    # 分类/分割当前以检测模型代理，看板指标对齐默认检测模型真实 results.csv
    if det.get("map50"):
        metrics["classification"] = {
            **MODEL_METRICS["classification"],
            "model_name": f"{det['model_name']}（定性代理）",
            "weights": det["weights"],
            "dataset": det["dataset"] + " · 取最高置信度类别",
            "epochs": det.get("epochs", 0),
            "precision": det["precision"],
            "recall": det["recall"],
            "f1": det["f1"],
            "accuracy": det["map50"],
            "params_m": det["params_m"],
            "inference_ms": det["inference_ms"],
            "per_class": [
                {"name": "检测主类", "precision": det["precision"], "recall": det["recall"], "f1": det["f1"]},
                {"name": "mAP@0.5", "precision": det["map50"], "recall": det["map50"], "f1": det["map50"]},
                {"name": "mAP@0.5:0.95", "precision": det.get("map50_95", 0), "recall": det.get("map50_95", 0), "f1": det.get("map50_95", 0)},
            ],
            "note": "无独立分类权重时，定性筛查复用 YOLO 检测结果",
        }
        metrics["segmentation"] = {
            **MODEL_METRICS["segmentation"],
            "note": "分割模式已停用；前端不再提供该入口",
        }
    return metrics
