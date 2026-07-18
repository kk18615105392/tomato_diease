# 番茄消融实验权重 — 导入其他检测项目

## 目录结构（按 E1–E11 实验表整理）

```
tomato_ablation_weights/
├── README_导入其他项目.md      ← 本文件
├── experiment_index.json       ← 实验对照表（与汇报表格一致）
├── data/
│   ├── tomato_v2.yaml          ← 10 类整叶
│   └── tomato_merged9.yaml       ← 9 类小病斑
└── models/
    ├── E1_baseline/
    │   ├── v2.pt               ← Tomato.v2 权重（有则存在）
    │   ├── merged9.pt          ← merged9 权重（有则存在）
    │   ├── meta_v2.json
    │   ├── meta_merged9.json
    │   └── README.txt
    ├── E2_mlca/
    ├── …
    ├── E9_pfa_parallel/
    ├── E10_cpr_distill/
    └── E11_cakd_dual_teacher/
```

## 快速选用（与实验表一致）

| 场景 | 推荐权重路径 |
|------|-------------|
| v2 最高精度 | `models/E8b_copy_paste_aug/v2.pt` |
| v2 最佳蒸馏 | `models/E6_distill_baseline_from_mlca_s/v2.pt` |
| v2 注意力 | `models/E9_pfa_parallel/v2.pt` |
| v2 少误检 | `models/E8c_p2_and_aug/v2.pt` |
| merged9 部署 | `models/E1_baseline/merged9.pt` |
| merged9 蒸馏 | `models/E6_distill_baseline_from_mlca_s/merged9.pt` |

## 导入 Ultralytics 项目

```python
from ultralytics import YOLO

# 整叶 v2 — 最高精度
model = YOLO("models/E8b_copy_paste_aug/v2.pt")
results = model.predict("image.jpg", imgsz=640, conf=0.25)

# 小病斑 merged9 — baseline
model = YOLO("models/E1_baseline/merged9.pt")
results = model.predict("image.jpg", imgsz=640, conf=0.25)
```

## 导入其他 YOLO 检测框架

1. 复制整个 `tomato_ablation_weights/` 到你的项目，例如 `your_project/weights/tomato/`
2. 使用上表路径加载对应 `.pt`
3. 类别数：v2 为 **10 类**，merged9 为 **9 类**（见 `data/*.yaml` 的 names）
4. 输入尺寸：**640×640**

## 特殊模型说明

- **E9 PFA / E2 MLCA / E7 CBAM 系列**：自定义结构已烘焙在 `.pt` 内，直接用 YOLO 加载即可，无需额外 yaml。
- **E3 教师模型**：体积约 22MB，仅建议离线蒸馏，不建议边缘部署。
- **E7c / E8a / E8b（merged9）**：merged9 上未训练，文件夹内无 merged9.pt。

## 重新导出

在 MLCA-master 项目根目录：

```powershell
python tools/export_weights_for_project.py
python tools/export_weights_for_project.py --target D:\your_detect_project\weights\tomato
```
