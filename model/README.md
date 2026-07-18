# 模型权重说明

本目录存放 YOLO 消融实验与基线权重。

- **已纳入 Git**：`results.csv`、`opt.yaml`、`ablation_manifest.json`、说明文档等轻量文件（供模型看板读取指标）。
- **未纳入 Git**：`weights/best.pt` 等权重（体积大，约数百 MB）。

本地推理时请将权重放在：

```text
model/<实验目录名>/weights/best.pt
```

与训练时目录结构保持一致即可被 `backend/model_registry.py` 自动扫描。
