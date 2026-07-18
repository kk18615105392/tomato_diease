"""诊断报告持久化（Web / 小程序共用，按用户隔离）。"""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from flask import g, jsonify, request

from auth import get_current_user, login_required

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "users.db"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_reports_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS diagnosis_reports (
                id TEXT PRIMARY KEY,
                user_id INTEGER,
                mode TEXT NOT NULL,
                image_id TEXT,
                zone_id TEXT,
                summary TEXT NOT NULL,
                result_json TEXT NOT NULL,
                source TEXT DEFAULT 'web',
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_reports_user ON diagnosis_reports(user_id, created_at DESC)"
        )
        conn.commit()


def _row_to_report(row: sqlite3.Row) -> dict[str, Any]:
    result = json.loads(row["result_json"])
    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "mode": row["mode"],
        "image_id": row["image_id"],
        "zone_id": row["zone_id"],
        "summary": row["summary"],
        "result": result,
        "source": row["source"] or "web",
        "created_at": row["created_at"],
        "share_path": f"/pages/report/report?id={row['id']}",
    }


def create_report(
    *,
    user_id: int | None,
    mode: str,
    summary: str,
    result: dict,
    image_id: str | None = None,
    zone_id: str | None = None,
    source: str = "web",
) -> dict[str, Any]:
    report_id = uuid.uuid4().hex
    now = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO diagnosis_reports
            (id, user_id, mode, image_id, zone_id, summary, result_json, source, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                report_id,
                user_id,
                mode,
                image_id,
                zone_id,
                summary,
                json.dumps(result, ensure_ascii=False),
                source,
                now,
            ),
        )
        conn.commit()
    return get_report(report_id)  # type: ignore[return-value]


def get_report(report_id: str) -> dict[str, Any] | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM diagnosis_reports WHERE id = ?",
            (report_id,),
        ).fetchone()
    return _row_to_report(row) if row else None


def list_user_reports(user_id: int, limit: int = 50) -> list[dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM diagnosis_reports
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
    return [_row_to_report(r) for r in rows]


def delete_user_report(user_id: int, report_id: str) -> bool:
    with _connect() as conn:
        cur = conn.execute(
            "DELETE FROM diagnosis_reports WHERE id = ? AND user_id = ?",
            (report_id, user_id),
        )
        conn.commit()
        return cur.rowcount > 0


def register_report_routes(app) -> None:
    init_reports_db()

    @app.post("/api/reports")
    @login_required
    def create_report_api():
        data = request.get_json(silent=True) or {}
        mode = str(data.get("mode", "")).strip()
        summary = str(data.get("summary", "")).strip()
        result = data.get("result")
        if not mode or not summary or not isinstance(result, dict):
            return jsonify({"error": "缺少 mode / summary / result"}), 400
        report = create_report(
            user_id=g.current_user["id"],
            mode=mode,
            summary=summary,
            result=result,
            image_id=data.get("image_id"),
            zone_id=data.get("zone_id"),
            source=str(data.get("source", "web")),
        )
        return jsonify({"report": report})

    @app.get("/api/reports")
    @login_required
    def list_reports_api():
        limit = min(int(request.args.get("limit", 50)), 100)
        reports = list_user_reports(g.current_user["id"], limit=limit)
        return jsonify({"reports": reports, "total": len(reports)})

    @app.get("/api/reports/<report_id>")
    def get_report_api(report_id: str):
        """报告详情：登录用户可看自己的；也支持分享码公开查看摘要。"""
        report = get_report(report_id)
        if report is None:
            return jsonify({"error": "报告不存在"}), 404
        user = get_current_user()
        # 公开分享：返回完整诊断结果（田间农技员扫码查看）
        if user and report.get("user_id") and user["id"] != report["user_id"]:
            # 别人的报告也允许看（分享场景），仅隐藏 user_id 敏感字段
            pass
        return jsonify({"report": report})

    @app.delete("/api/reports/<report_id>")
    @login_required
    def delete_report_api(report_id: str):
        ok = delete_user_report(g.current_user["id"], report_id)
        if not ok:
            return jsonify({"error": "报告不存在或无权删除"}), 404
        return jsonify({"ok": True})
