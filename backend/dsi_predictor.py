"""DSI 时序预测 — 最小二乘线性回归（后续可替换为 LSTM）"""

import re


def _parse_day(label: str, fallback: int) -> int:
    m = re.search(r"(\d+)", label or "")
    return int(m.group(1)) if m else fallback


def predict_dsi_forecast(history: list[dict]) -> dict:
    """
    history: [{"label": "第1天", "dsi": 12.5}, ...]
    返回历史点 + 未来 7 天预测
    """
    if len(history) < 2:
        return {"error": "至少需要 2 个历史 DSI 数据点"}

    points = []
    for i, item in enumerate(history):
        day = _parse_day(item.get("label", ""), (i + 1) * 2)
        dsi = float(item.get("dsi", 0))
        points.append({"day": day, "dsi": dsi, "label": item.get("label", f"第{day}天")})

    points.sort(key=lambda p: p["day"])
    n = len(points)
    xs = [p["day"] for p in points]
    ys = [p["dsi"] for p in points]

    x_mean = sum(xs) / n
    y_mean = sum(ys) / n
    num = sum((xs[i] - x_mean) * (ys[i] - y_mean) for i in range(n))
    den = sum((xs[i] - x_mean) ** 2 for i in range(n)) or 1e-6
    slope = num / den
    intercept = y_mean - slope * x_mean

    last_day = xs[-1]
    day_step = max(1, round((xs[-1] - xs[0]) / max(n - 1, 1)))

    forecast = []
    for i in range(1, 8):
        day = last_day + day_step * i
        pred = intercept + slope * day
        pred = max(0.0, min(100.0, pred))
        level = "轻度发病" if pred < 10 else "中度发病" if pred < 25 else "重度发病"
        forecast.append(
            {
                "day": day,
                "label": f"预测第{day}天",
                "dsi": round(pred, 1),
                "severity_level": level,
            }
        )

    trend = "上升" if slope > 0.5 else "下降" if slope < -0.5 else "平稳"
    risk = "高" if slope > 1.5 or ys[-1] > 30 else "中" if slope > 0.3 or ys[-1] > 15 else "低"

    return {
        "model": "LeastSquares-LinearRegression",
        "history": [{"label": p["label"], "day": p["day"], "dsi": p["dsi"]} for p in points],
        "forecast": forecast,
        "slope_per_day": round(slope, 4),
        "trend": trend,
        "risk_level": risk,
        "summary": f"近程趋势{trend}，斜率 {slope:.2f}/天，风险等级 {risk}",
    }
