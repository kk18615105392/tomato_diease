# 番茄病虫害智能诊断与专家辅助决策系统

[![Deploy GitHub Pages](https://github.com/kk18615105392/tomato_diease/actions/workflows/deploy-pages.yml/badge.svg)](https://github.com/kk18615105392/tomato_diease/actions/workflows/deploy-pages.yml)

毕业设计系统：基于 YOLO 的番茄叶片病害**快速定性 / 精准定位**诊断，集成专家处方、病害百科、模型看板，以及论文**第六章跨作物域适应**实验看板；配套微信小程序田间版。

> 在线前端（GitHub Pages）：  
> **https://kk18615105392.github.io/tomato_diease/**  
> 说明：Pages 仅托管前端静态页；YOLO 推理、登录、上传等需在本地启动后端（见下方）。

---

## 功能概览

| 模块 | 说明 |
|------|------|
| 智能诊断 | 上传/拍照 → 定性筛查或 YOLO 目标检测 |
| 时序对比 | 多张叶片并排对比病情变化 |
| 专家问答 | 基于诊断结果的植保处方（可接 LLM） |
| 病害百科 / 对照库 | 典型病斑参考与相似度对照 |
| 模型看板 | 消融实验 test mAP@0.5 排名（读取 `model/*/results.csv`） |
| 域适应看板 (Ch6) | 番茄→热带水果：多任务 / MMD / GRL / 消融表 |
| 微信小程序 | 同账号登录、拍叶诊断、报告与百科 |

---

## 技术栈

- **前端**：Vue 3 + Vite + TypeScript + Element Plus + ECharts  
- **后端**：Flask + PyTorch / Ultralytics YOLO  
- **小程序**：微信原生小程序（`miniprogram/`）  
- **鉴权**：SQLite + Token（演示账号见下）

---

## 目录结构

```text
czk_biye/
├── frontend/          # Web 前端
├── backend/           # Flask API
├── miniprogram/       # 微信小程序
├── model/             # 实验权重与 results.csv（权重文件默认不入库）
├── .github/workflows/ # GitHub Pages 自动部署
└── README.md
```

---

## 本地快速启动

### 环境要求

- Python 3.10+（推荐 conda 环境，如 `pytorch_gpu`）
- Node.js 18+
- （可选）NVIDIA GPU + CUDA，用于加速 YOLO

### 1. 克隆仓库

```bash
git clone https://github.com/kk18615105392/tomato_diease.git
cd tomato_diease
```

### 2. 准备模型权重（本地）

仓库**不包含**体积较大的 `*.pt` 权重。请将训练好的权重放到：

```text
model/<实验名>/weights/best.pt
```

并保留已有的 `results.csv`、`opt.yaml`、`ablation_manifest.json` 等元数据，模型看板才能显示真实指标。

### 3. 启动后端

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

后端默认：`http://127.0.0.1:5000`

### 4. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端默认：`http://127.0.0.1:5173`（Vite 已代理 `/api` → 后端）

也可直接运行根目录 `setup.ps1` / `start.bat`（若已配置）。

### 演示账号

| 用户名 | 密码 |
|--------|------|
| `demo_user` | `demo123` |

也可在登录页自行注册。

### 微信小程序

1. 用微信开发者工具导入 `miniprogram/`
2. 勾选「不校验合法域名」
3. 真机调试时，将 `miniprogram/utils/config.js` 中的 `API_BASE` 改为电脑局域网 IP（如 `http://192.168.x.x:5000`）

---

## GitHub 自动部署（前端）

推送到 `main` 后，GitHub Actions 会：

1. 安装依赖并 `npm run build`
2. 将产物部署到 **GitHub Pages**

首次使用需在仓库设置中开启 Pages：

**Settings → Pages → Build and deployment → Source：GitHub Actions**

部署完成后访问：

https://kk18615105392.github.io/tomato_diease/

> Pages 上的页面无法直接调用本机 Flask。完整诊断请本地同时启动后端，或将 `VITE_API_BASE_URL` 指向已公网部署的 API。

---

## 论文第六章（域适应）

看板路径：Web 侧栏 **域适应看板(Ch6)**  
数据源：`backend/heterogeneous_stats.py`（实验终值模板，本地重跑后可替换数字）

实验主线：多任务混合比例 → MMD 对齐 → GRL 对抗域适应 → 消融与跨域泛化。

---

## API 摘要

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/register` `/login` | 注册 / 登录 |
| POST | `/api/upload` | 上传图片 |
| POST | `/api/diagnose` | 诊断（`classification` / `detection`） |
| GET  | `/api/detection_models` | 可用检测权重列表 |
| GET  | `/api/model_metrics` | 模型看板指标 |
| GET  | `/api/stats/heterogeneous` | 第六章域适应看板数据 |
| POST | `/api/chat_expert` | 专家流式问答 |

---

## 许可证与说明

本仓库用于毕业设计展示与复现。请勿将含隐私的田间原图、账号密钥提交到公开仓库。
