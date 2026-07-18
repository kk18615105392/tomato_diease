# 番茄消融实验权重（E1–E11）

本目录包含从 `MLCA-master` 导入的全部消融实验权重。

## 结构

```
model/
├── ablation_manifest.json          # 26 个已注册模型索引
├── tomato_ablation/                # 完整导出包（按实验表分文件夹）
│   ├── experiment_index.json
│   ├── models/E1_baseline/v2.pt
│   └── ...
├── ablation-E1-v2/               # 后端可直接加载
│   └── weights/best.pt
├── ablation-E8b-v2/              # 默认推荐（test 97.6%）
└── ...
```

## 默认检测模型

- **整叶 v2**：`ablation-E8b-v2`（E8b Copy-Paste 增强）
- **小病斑 merged9**：`ablation-E1-merged9`

## 前端/API 选用模型

诊断接口传参：

```json
{
  "image_id": "...",
  "mode": "detection",
  "detection_model": "ablation-E9-v2"
}
```

模型列表：`GET /api/detection-models`

## 重新同步权重

在 MLCA-master 项目执行：

```powershell
python tools/deploy_to_czk_biye.py --target C:\Users\cuizekun\czk_biye
```

## 实验对照

| 实验 | v2 模型 key | merged9 模型 key |
|------|-------------|------------------|
| E1 Baseline | ablation-E1-v2 | ablation-E1-merged9 |
| E8b 增强 | ablation-E8b-v2 | — |
| E9 PFA | ablation-E9-v2 | — |
| E6 蒸馏 | ablation-E6-v2 | ablation-E6-merged9 |

完整列表见 `tomato_ablation/experiment_index.json`。
