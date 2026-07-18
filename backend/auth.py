"""用户注册 / 登录 / JWT 鉴权（SQLite + Werkzeug + itsdangerous）。"""

from __future__ import annotations

import os
import re
import sqlite3
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from typing import Any, Callable

from flask import g, jsonify, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "users.db"
SECRET_KEY = os.getenv("AUTH_SECRET_KEY", "tomato-ai-auth-secret-change-me")
TOKEN_MAX_AGE = int(os.getenv("AUTH_TOKEN_DAYS", "7")) * 24 * 3600

_USERNAME_RE = re.compile(r"^[a-zA-Z0-9_\u4e00-\u9fff]{2,32}$")


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(SECRET_KEY, salt="tomato-ai-auth")


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                display_name TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def _connect() -> sqlite3.Connection:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _row_to_user(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {
        "id": row["id"],
        "username": row["username"],
        "display_name": row["display_name"] or row["username"],
        "created_at": row["created_at"],
    }


def get_user_by_id(user_id: int) -> dict[str, Any] | None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return _row_to_user(row)


def get_user_by_username(username: str) -> sqlite3.Row | None:
    with _connect() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE username = ? COLLATE NOCASE",
            (username.strip(),),
        ).fetchone()


def create_token(user: dict[str, Any]) -> str:
    return _serializer().dumps({"uid": user["id"], "username": user["username"]})


def decode_token(token: str) -> dict[str, Any] | None:
    try:
        payload = _serializer().loads(token, max_age=TOKEN_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None
    if not isinstance(payload, dict) or "uid" not in payload:
        return None
    return payload


def _validate_credentials(username: str, password: str) -> str | None:
    username = username.strip()
    if not username or not _USERNAME_RE.match(username):
        return "用户名需为 2–32 位字母、数字、下划线或中文"
    if len(password) < 6:
        return "密码至少 6 位"
    if len(password) > 64:
        return "密码过长"
    return None


def register_user(username: str, password: str, display_name: str | None = None) -> tuple[dict | None, str | None]:
    err = _validate_credentials(username, password)
    if err:
        return None, err

    username = username.strip()
    display = (display_name or username).strip()[:32] or username
    now = datetime.now(timezone.utc).isoformat()

    try:
        with _connect() as conn:
            cur = conn.execute(
                "INSERT INTO users (username, password_hash, display_name, created_at) VALUES (?, ?, ?, ?)",
                (username, generate_password_hash(password), display, now),
            )
            conn.commit()
            user_id = int(cur.lastrowid)
    except sqlite3.IntegrityError:
        return None, "用户名已被注册"

    user = get_user_by_id(user_id)
    return user, None


def login_user(username: str, password: str) -> tuple[dict | None, str | None]:
    if not username or not password:
        return None, "请输入用户名和密码"
    row = get_user_by_username(username)
    if row is None or not check_password_hash(row["password_hash"], password):
        return None, "用户名或密码错误"
    return _row_to_user(row), None


def extract_bearer_token() -> str | None:
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip() or None
    return None


def get_current_user() -> dict[str, Any] | None:
    token = extract_bearer_token()
    if not token:
        return None
    payload = decode_token(token)
    if not payload:
        return None
    return get_user_by_id(int(payload["uid"]))


def login_required(fn: Callable):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if user is None:
            return jsonify({"error": "未登录或登录已过期"}), 401
        g.current_user = user
        return fn(*args, **kwargs)

    return wrapper


def register_auth_routes(app) -> None:
    init_db()

    @app.post("/api/auth/register")
    def auth_register():
        data = request.get_json(silent=True) or {}
        user, err = register_user(
            str(data.get("username", "")),
            str(data.get("password", "")),
            str(data.get("display_name", "") or "") or None,
        )
        if err:
            return jsonify({"error": err}), 400
        assert user is not None
        token = create_token(user)
        return jsonify({"token": token, "user": user})

    @app.post("/api/auth/login")
    def auth_login():
        data = request.get_json(silent=True) or {}
        user, err = login_user(str(data.get("username", "")), str(data.get("password", "")))
        if err:
            return jsonify({"error": err}), 401
        assert user is not None
        token = create_token(user)
        return jsonify({"token": token, "user": user})

    @app.get("/api/auth/me")
    @login_required
    def auth_me():
        return jsonify({"user": g.current_user})
