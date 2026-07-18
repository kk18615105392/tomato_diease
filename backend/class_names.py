"""番茄检测类别名映射（v2 训练时 yaml 为占位名，推理时替换为病害名）。"""

# Tomato.v2 整叶 10 类（与 PlantVillage / tomato-29lap 一致）
V2_CLASS_NAMES: dict[int, str] = {
    0: "细菌性斑点病 Bacterial Spot",
    1: "早疫病 Early Blight",
    2: "晚疫病 Late Blight",
    3: "叶霉病 Leaf Mold",
    4: "斑枯病 Septoria",
    5: "红蜘蛛 Spider Mites",
    6: "靶斑病 Target Spot",
    7: "黄化曲叶病毒 YLCV",
    8: "健康 Healthy",
    9: "花叶病毒 Mosaic Virus",
}

DATASET_TASK: dict[str, dict] = {
    "v2": {
        "task_type": "whole_leaf",
        "task_label": "整叶病类识别",
        "hint": (
            "该模型在 Tomato.v2 上训练：每张图通常只有 1 个框，框住整片叶片，"
            "用于判断叶片所属病害类别（类似「检测形式的分类」），不是小病斑定位。"
        ),
        "upload_tip": "建议上传单叶片、叶片占画面主体的照片（与 v2 训练集一致）",
    },
    "merged9": {
        "task_type": "spot_detection",
        "task_label": "小病斑定位",
        "hint": (
            "该模型在 merged9 上训练：检测多个小病斑/病叶区域，框较小，"
            "适合温室叶片局部病斑筛查。"
        ),
        "upload_tip": "可上传含多个病斑的叶片特写",
    },
}


def normalize_label(label: str, cls_id: int, dataset: str) -> str:
    if dataset == "v2" and (label.startswith("tomato_class_") or label.isdigit()):
        return V2_CLASS_NAMES.get(cls_id, label)
    return label


def resolve_class_name(cls_id: int, raw: str, dataset: str | None) -> str:
    if dataset:
        return normalize_label(raw, cls_id, dataset)
    if raw.startswith("tomato_class_") or raw.isdigit():
        return V2_CLASS_NAMES.get(cls_id, raw)
    return raw


def resolve_class_names(names: dict | list, dataset: str | None) -> list[str]:
    if isinstance(names, dict):
        items = sorted(names.items(), key=lambda x: int(x[0]))
    else:
        items = list(enumerate(names))
    out = []
    for cid, raw in items:
        out.append(resolve_class_name(int(cid), str(raw), dataset or ""))
    return out


def task_info_for_dataset(dataset: str) -> dict:
    return DATASET_TASK.get(dataset, {})
