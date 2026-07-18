# Tomato AI 微信小程序（田间版）

与 Web 端共用同一套 Flask 后端、同一账号体系与诊断报告库。

## 功能

| 模块 | 说明 |
|------|------|
| 登录/注册 | 与 Web 同一账号（`/api/auth/*`） |
| 拍叶诊断 | 拍照/相册 → 上传 → YOLO 检测 → 写入云端报告 |
| 我的报告 | 拉取同账号报告（Web + 小程序互通） |
| 病害百科 | 调用 `/api/wiki/diseases` |
| 扫码看报告 | 扫描 Web「扫码分享」二维码，打开报告详情 |

## 开发调试

1. 启动后端：`conda activate pytorch_gpu` → `cd backend` → `python app.py`
2. 用[微信开发者工具](https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html)导入本目录 `miniprogram/`
3. AppID 可选「测试号 / 游客」；详情里勾选：**不校验合法域名、web-view、TLS 版本以及 HTTPS 证书**
4. 真机调试时，把 `utils/config.js` 里的 `API_BASE` 改成电脑局域网 IP，例如 `http://192.168.1.8:5000`

## 与 Web 关联链路

```
Web 诊断成功 → POST /api/reports → 生成 report_id
                ↓
     扫码分享二维码（含 report_id）
                ↓
小程序扫码 /pages/report/report?id=xxx → GET /api/reports/:id
```

小程序拍叶诊断同样写入 `/api/reports`，在 Web 历史（云端同步后）与小程序「我的报告」中都能看到。
