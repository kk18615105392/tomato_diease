"""跨作物病害识别的域适应研究 — 实验看板数据。

源域：PlantVillage-Tomato；目标域：Tropical-Fruit（芒果等）。
实验主线：多任务混合 → MMD 对齐 → 对抗域适应 → 消融泛化。
"""

from __future__ import annotations

import math

# ── 数据集 ──────────────────────────────────────────────
DATASET_STATS = {
    "tomato_base": 4525,
    "tropical_fruit": 1076,
    "mixed_total": 4525 + 1076,
    "tomato_label": "源域 · PlantVillage-Tomato",
    "tropical_label": "目标域 · Tropical-Fruit",
    "mixed_label": "混合训练池总量",
    "description": (
        "以番茄病害为源域、芒果等热带水果为目标域，"
        "通过多任务联合训练、MMD 特征对齐与 GRL 对抗解耦，缓解跨作物域偏倚。"
    ),
    "source_domain": "番茄（PlantVillage）",
    "target_domain": "芒果 / 莲雾 / 巴西樱桃等",
    "shared_encoder": "ResNet-50 / Swin-Transformer 共享主干",
}


def _gen_epoch_curve(start: float, end: float, epochs: int = 50, noise: float = 0.8):
    curve = []
    for e in range(1, epochs + 1):
        t = e / epochs
        base = start + (end - start) * (1 - math.exp(-3.5 * t)) / (1 - math.exp(-3.5))
        wobble = noise * math.sin(e * 0.7) * (1 - t * 0.6)
        acc = round(min(99.0, max(0.0, base + wobble)), 2)
        curve.append({"epoch": e, "accuracy": acc})
    curve[-1]["accuracy"] = end
    return curve


BASELINE_FINAL = 63.77
ENHANCED_FINAL = 68.12

EPOCH_COMPARISON = {
    "x_label": "训练轮次 (Epoch)",
    "y_label": "PlantDoc 复杂田间测试集准确率 (%)",
    "baseline": {
        "name": "Baseline-A · Source-Only 番茄",
        "color": "#9ca3af",
        "final_accuracy": BASELINE_FINAL,
        "data": _gen_epoch_curve(42.0, BASELINE_FINAL),
    },
    "enhanced": {
        "name": "Full Model · Multi-Task+MMD+Adv",
        "color": "#22c55e",
        "final_accuracy": ENHANCED_FINAL,
        "data": _gen_epoch_curve(44.0, ENHANCED_FINAL),
    },
    "improvement_abs": round(ENHANCED_FINAL - BASELINE_FINAL, 2),
    "improvement_rel": round((ENHANCED_FINAL - BASELINE_FINAL) / BASELINE_FINAL * 100, 2),
}

ROBUSTNESS_RADAR = {
    "indicators": [
        {"name": "复杂背景", "max": 100},
        {"name": "强光干扰", "max": 100},
        {"name": "多叶遮挡", "max": 100},
        {"name": "运动模糊", "max": 100},
        {"name": "尺度变化", "max": 100},
    ],
    "baseline": {"name": "Source-Only", "values": [58.2, 55.6, 52.1, 60.4, 57.8]},
    "enhanced": {"name": "Full Model", "values": [67.5, 64.3, 62.8, 68.1, 65.9]},
}

# ── 实验一：混合比例（表 1）──────────────────────────────
# 混合比例 = 目标域样本数 / 源域样本数；数值为实验记录示意终值
EXP1_MIX_RATIO = [
    {"group": "Baseline-A", "mix_ratio": "0%", "uncertainty": False, "tomato_acc": 92.4, "tomato_f1": 91.8, "fruit_acc": None, "fruit_f1": None, "note": "单任务源域"},
    {"group": "Exp 1-1", "mix_ratio": "10%", "uncertainty": True, "tomato_acc": 92.8, "tomato_f1": 92.1, "fruit_acc": 71.2, "fruit_f1": 68.5, "note": "低比例扰动"},
    {"group": "Exp 1-2", "mix_ratio": "30%", "uncertainty": True, "tomato_acc": 93.5, "tomato_f1": 92.9, "fruit_acc": 76.8, "fruit_f1": 74.1, "note": "中比例"},
    {"group": "Exp 1-3", "mix_ratio": "50%", "uncertainty": True, "tomato_acc": 94.1, "tomato_f1": 93.6, "fruit_acc": 80.3, "fruit_f1": 78.0, "note": "最佳平衡", "best": True},
    {"group": "Exp 1-4", "mix_ratio": "70%", "uncertainty": True, "tomato_acc": 93.0, "tomato_f1": 92.4, "fruit_acc": 81.5, "fruit_f1": 79.2, "note": "源域开始稀释"},
    {"group": "Exp 1-5", "mix_ratio": "100%", "uncertainty": True, "tomato_acc": 91.6, "tomato_f1": 90.9, "fruit_acc": 82.1, "fruit_f1": 80.0, "note": "等量混合"},
]

# ── 实验二：MMD（表 2）──────────────────────────────────
EXP2_MMD = [
    {"group": "Baseline-B", "method": "无对齐（50% 混合）", "tomato_acc": 94.1, "fruit_acc": 80.3, "cross_acc": 72.4, "mmd": 0.186, "note": "实验一最佳作基线"},
    {"group": "Exp 2-1", "method": "Linear MMD", "tomato_acc": 94.0, "fruit_acc": 81.0, "cross_acc": 73.8, "mmd": 0.142, "note": "线性核"},
    {"group": "Exp 2-2", "method": "RBF MMD", "tomato_acc": 94.2, "fruit_acc": 81.8, "cross_acc": 75.1, "mmd": 0.118, "note": "非线性"},
    {"group": "Exp 2-3", "method": "Multi-Kernel MMD", "tomato_acc": 94.3, "fruit_acc": 82.4, "cross_acc": 76.6, "mmd": 0.095, "note": "最稳健", "best": True},
]

# ── 实验三：对抗（表 3）──────────────────────────────────
EXP3_ADV = [
    {"group": "Baseline-C", "method": "Multi-Task + MMD", "source_acc": 94.3, "domain_disc_acc": 88.5, "cross_acc": 76.6, "note": "实验二最佳"},
    {"group": "Exp 3-1", "method": "GRL 固定 β", "source_acc": 93.1, "domain_disc_acc": 62.4, "cross_acc": 79.2, "note": "基础对抗"},
    {"group": "Exp 3-2", "method": "GRL 调度 β（DANN）", "source_acc": 93.8, "domain_disc_acc": 54.1, "cross_acc": 82.7, "note": "渐进对抗", "best": True},
    {"group": "Exp 3-3", "method": "类别条件 GRL", "source_acc": 93.5, "domain_disc_acc": 52.8, "cross_acc": 81.9, "note": "条件对抗"},
]

# ── 实验四：消融与跨域（表 4）────────────────────────────
EXP4_ABLATION = [
    {"group": "A", "method": "Source-Only", "tomato_test": 92.4, "fruit_test": 41.2, "cross_test": 38.5, "note": "直接跨域失效"},
    {"group": "B", "method": "Fine-tune Target", "tomato_test": 88.1, "fruit_test": 85.6, "cross_test": 71.0, "note": "目标域上限参考"},
    {"group": "C", "method": "Multi-Task（50%）", "tomato_test": 94.1, "fruit_test": 80.3, "cross_test": 72.4, "note": "实验一最佳"},
    {"group": "D", "method": "+ Multi-Kernel MMD", "tomato_test": 94.3, "fruit_test": 82.4, "cross_test": 76.6, "note": "实验二最佳"},
    {"group": "E", "method": "+ GRL scheduled", "tomato_test": 93.8, "fruit_test": 83.1, "cross_test": 82.7, "note": "实验三最佳"},
    {"group": "F", "method": "Full Model", "tomato_test": 93.9, "fruit_test": 84.0, "cross_test": 85.2, "note": "多任务+MMD+对抗", "best": True},
]

CHAPTER6_META = {
    "title": "跨作物病害识别的域适应研究",
    "hypothesis": "不同作物病害的病理表征存在可迁移共享隐向量，可通过域适应对齐。",
    "pipeline": [
        "先验探索：多任务联合 + 不确定性动态加权",
        "显式对齐：MMD 特征对齐损失",
        "对抗解耦：GRL + 作物域判别器",
        "综合验证：跨域泛化与消融",
    ],
    "best_cross_acc": 85.2,
    "best_method": "Full Model（Multi-Task + Multi-Kernel MMD + GRL scheduled）",
}


def get_heterogeneous_stats() -> dict:
    return {
        "meta": CHAPTER6_META,
        "dataset": DATASET_STATS,
        "epoch_comparison": EPOCH_COMPARISON,
        "robustness_radar": ROBUSTNESS_RADAR,
        "exp1_mix_ratio": EXP1_MIX_RATIO,
        "exp2_mmd": EXP2_MMD,
        "exp3_adversarial": EXP3_ADV,
        "exp4_ablation": EXP4_ABLATION,
        "summary": (
            f"{CHAPTER6_META['title']}：源域番茄 + 目标域热带水果。"
            f"Full Model 跨域测试 Acc={CHAPTER6_META['best_cross_acc']}%"
            f"（相对 Source-Only 跨域 {EXP4_ABLATION[0]['cross_test']}% 显著提升）。"
            f"PlantDoc 田间精度 {BASELINE_FINAL}% → {ENHANCED_FINAL}%（+{EPOCH_COMPARISON['improvement_abs']}%）。"
        ),
        "data_source": "domain_adaptation_experiment_tables",
        "note": "表内数值为实验终值模板；若本地重跑实验，可替换 backend/heterogeneous_stats.py 中对应列表。",
    }
