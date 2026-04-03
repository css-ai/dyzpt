from __future__ import annotations

import hashlib
import hmac
import html
import json
import logging
import os
import re
import secrets
import sqlite3
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Literal
from urllib.parse import unquote, urlparse

import pymysql
import redis
from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import JSONResponse

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "site_pages.db"  # 兼容当前 SQLite 相关逻辑

# ==================== 生产安全配置 ====================
ENV = os.environ.get("APP_ENV", "development").lower()
IS_PROD = ENV == "production"

# MySQL 连接串示例：
# mysql://user:password@127.0.0.1:3306/template_cms
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "mysql://root:123456@127.0.0.1:3306/template_cms",
)

# Redis 连接
REDIS_URL = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")
REDIS_PREFIX = os.environ.get("SECURITY_REDIS_PREFIX", "template_cms")
REDIS_CONNECT_TIMEOUT = float(os.environ.get("REDIS_CONNECT_TIMEOUT", "0.3"))
REDIS_SOCKET_TIMEOUT = float(os.environ.get("REDIS_SOCKET_TIMEOUT", "0.3"))

# 仅在显式开启时信任反向代理 X-Forwarded-For（避免被伪造）
TRUST_PROXY_HEADERS = os.environ.get("TRUST_PROXY_HEADERS", "0") == "1"

# 强制 HTTPS / Host 白名单（生产建议开启）
FORCE_HTTPS = os.environ.get("FORCE_HTTPS", "1" if IS_PROD else "0") == "1"
_ALLOWED_HOSTS_RAW = os.environ.get("ALLOWED_HOSTS", "")
if _ALLOWED_HOSTS_RAW.strip():
    ALLOWED_HOSTS: list[str] = [h.strip() for h in _ALLOWED_HOSTS_RAW.split(",") if h.strip()]
else:
    ALLOWED_HOSTS = ["localhost", "127.0.0.1"] if not IS_PROD else ["example.com"]

# 攻击防护参数
GLOBAL_RATE_LIMIT = int(os.environ.get("GLOBAL_RATE_LIMIT", "180"))
GLOBAL_RATE_WINDOW_SEC = int(os.environ.get("GLOBAL_RATE_WINDOW_SEC", "60"))
CC_PATH_RATE_LIMIT = int(os.environ.get("CC_PATH_RATE_LIMIT", "60"))
CC_PATH_RATE_WINDOW_SEC = int(os.environ.get("CC_PATH_RATE_WINDOW_SEC", "10"))
BOT_SCORE_BLOCK = int(os.environ.get("BOT_SCORE_BLOCK", "80"))
BOT_SCORE_CHALLENGE = int(os.environ.get("BOT_SCORE_CHALLENGE", "50"))

# 登录防暴力（Redis 持久化）
_LOGIN_MAX_FAIL = int(os.environ.get("LOGIN_MAX_FAIL", "5"))
_LOGIN_WINDOW_SEC = int(os.environ.get("LOGIN_WINDOW_SEC", "60"))
_LOGIN_LOCK_SEC = int(os.environ.get("LOGIN_LOCK_SEC", "300"))

# JWT 黑名单过期时间（秒）
JWT_BLACKLIST_TTL_SEC = int(os.environ.get("JWT_BLACKLIST_TTL_SEC", str(7 * 24 * 3600)))

# 结构化安全日志
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
logger = logging.getLogger("security")
if not logger.handlers:
    logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO), format="%(asctime)s %(levelname)s %(message)s")


def _get_redis_client() -> redis.Redis:
    """创建 Redis 客户端。decode_responses=True 便于直接处理字符串。"""
    return redis.Redis.from_url(
        REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=REDIS_CONNECT_TIMEOUT,
        socket_timeout=REDIS_SOCKET_TIMEOUT,
    )


redis_client = _get_redis_client()


def _rk(name: str) -> str:
    """统一 Redis key 前缀，防止多项目冲突。"""
    return f"{REDIS_PREFIX}:{name}"


def get_client_ip(request: Request) -> str:
    """获取客户端 IP。默认使用 request.client，避免盲目信任头部。"""
    if TRUST_PROXY_HEADERS:
        xff = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        if xff:
            return xff
    return request.client.host if request.client else "unknown"


BASE_DIR = Path(__file__).resolve().parent

# ==================== JWT 配置 ====================
_jwt_secret_env = os.environ.get("JWT_SECRET", "")
if IS_PROD and not _jwt_secret_env:
    raise RuntimeError("生产环境必须设置 JWT_SECRET")
JWT_SECRET: str = _jwt_secret_env or secrets.token_hex(32)
JWT_ALGORITHM = "HS256"
# accessToken 有效期（分钟），生产建议 30 分钟
JWT_ACCESS_EXPIRE_MINUTES: int = int(os.environ.get("JWT_ACCESS_EXPIRE_MINUTES", "60"))


def jwt_encode(payload: dict) -> str:
    """生成 JWT token（HS256，无第三方依赖）。"""
    import base64
    header = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).rstrip(b"=").decode()
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
    sig = hmac.new(JWT_SECRET.encode(), f"{header}.{body}".encode(), hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(sig).rstrip(b"=").decode()
    return f"{header}.{body}.{sig_b64}"


def jwt_decode(token: str) -> dict:
    """验证并解析 JWT token，失败抛出 HTTPException 401。"""
    import base64
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("格式错误")
        header_b, body_b, sig_b = parts
        expected_sig = hmac.new(
            JWT_SECRET.encode(),
            f"{header_b}.{body_b}".encode(),
            hashlib.sha256,
        ).digest()
        actual_sig = base64.urlsafe_b64decode(sig_b + "==")
        if not hmac.compare_digest(expected_sig, actual_sig):
            raise ValueError("签名无效")
        # 补充 padding 再解码
        pad = lambda s: s + "=" * (-len(s) % 4)
        payload = json.loads(base64.urlsafe_b64decode(pad(body_b)).decode())
        if payload.get("exp") and time.time() > payload["exp"]:
            raise ValueError("Token 已过期")
        return payload
    except ValueError as e:
        raise HTTPException(status_code=401, detail=f"Token 无效：{e}")


def create_access_token(username: str) -> str:
    """为指定用户名生成带过期时间的 accessToken。"""
    exp = time.time() + JWT_ACCESS_EXPIRE_MINUTES * 60
    return jwt_encode({"sub": username, "exp": exp})


# ==================== 登录限流（内存，重启清零）====================
# 结构：{ ip: {"count": int, "window_start": float, "locked_until": float} }
_login_fail_map: dict[str, dict] = {}
_LOGIN_MAX_FAIL = 5        # 窗口内最大失败次数
_LOGIN_WINDOW_SEC = 60     # 滑动窗口（秒）
_LOGIN_LOCK_SEC = 300      # 锁定时长（秒）


def check_login_rate_limit(ip: str) -> None:
    """登录失败频率检测，超出限制抛出 429。"""
    now = time.time()
    rec = _login_fail_map.get(ip)
    if rec and now < rec.get("locked_until", 0):
        remaining = int(rec["locked_until"] - now)
        raise HTTPException(status_code=429, detail=f"登录失败过多，请 {remaining} 秒后重试")


def record_login_fail(ip: str) -> None:
    """记录一次登录失败，必要时触发锁定。"""
    now = time.time()
    rec = _login_fail_map.setdefault(ip, {"count": 0, "window_start": now, "locked_until": 0})
    # 窗口过期则重置
    if now - rec["window_start"] > _LOGIN_WINDOW_SEC:
        rec["count"] = 0
        rec["window_start"] = now
    rec["count"] += 1
    if rec["count"] >= _LOGIN_MAX_FAIL:
        rec["locked_until"] = now + _LOGIN_LOCK_SEC


def clear_login_fail(ip: str) -> None:
    """登录成功后清除失败记录。"""
    _login_fail_map.pop(ip, None)


# ==================== CORS ====================
# 生产环境必须显式配置白名单域名
_raw_origins = os.environ.get("ALLOWED_ORIGINS", "")
if _raw_origins.strip():
    ALLOWED_ORIGINS: list[str] = [o.strip() for o in _raw_origins.split(",") if o.strip()]
else:
    if IS_PROD:
        raise RuntimeError("生产环境必须配置 ALLOWED_ORIGINS")
    ALLOWED_ORIGINS = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
    ]

_PBKDF2_ITERATIONS = 310_000


def hash_password(plain: str) -> str:
    """使用 PBKDF2-SHA256 哈希密码，返回 salt$hash 格式。"""
    salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", plain.encode(), salt.encode(), _PBKDF2_ITERATIONS).hex()
    return f"{salt}${h}"


def verify_password(plain: str, stored: str) -> bool:
    """验证密码。兼容旧明文密码（迁移期）。"""
    if "$" not in stored:
        # 旧明文密码直接比对
        return plain == stored
    salt, expected = stored.split("$", 1)
    h = hashlib.pbkdf2_hmac("sha256", plain.encode(), salt.encode(), _PBKDF2_ITERATIONS).hex()
    return secrets.compare_digest(h, expected)


def now_iso() -> str:
    """返回当前 UTC 时间的 ISO 格式字符串（替代已弃用的 datetime.utcnow()）。"""
    return datetime.now(timezone.utc).isoformat()


def today_str() -> str:
    """返回当前 UTC 日期字符串 YYYY-MM-DD。"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


# ==================== Pydantic 模型 ====================


class SitePageBase(BaseModel):
    """站点页面基础字段模型。"""

    site_path: str = Field(min_length=1, max_length=128)
    bind_domain: str = Field(min_length=1, max_length=253)
    site_name: str = Field(min_length=1, max_length=128)
    site_description: str = ""
    template_id: str = Field(min_length=1, max_length=64)
    nav_items: list[dict[str, Any]] = Field(default_factory=list)
    colors: dict[str, Any] = Field(default_factory=dict)
    fonts: dict[str, Any] = Field(default_factory=dict)
    status: Literal["draft", "published"] = "draft"


class SitePageCreate(SitePageBase):
    """创建页面请求模型。"""

    pass


class SitePageUpdate(BaseModel):
    """更新页面请求模型（支持部分字段更新）。"""

    site_path: str | None = Field(default=None, min_length=1, max_length=128)
    bind_domain: str | None = Field(default=None, min_length=1, max_length=253)
    site_name: str | None = Field(default=None, min_length=1, max_length=128)
    site_description: str | None = None
    template_id: str | None = Field(default=None, min_length=1, max_length=64)
    nav_items: list[dict[str, Any]] | None = None
    colors: dict[str, Any] | None = None
    fonts: dict[str, Any] | None = None
    status: Literal["draft", "published"] | None = None


class SitePageOut(SitePageBase):
    """页面输出模型，包含系统生成字段。"""

    id: str
    owner_username: str
    created_at: str
    updated_at: str


class LoginPayload(BaseModel):
    username: str
    password: str


class RegisterPayload(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=6, max_length=64)
    register_key: str = Field(min_length=8, max_length=64)


class RegisterKeyCreatePayload(BaseModel):
    role: Literal["admin", "super", "user"] = "user"


class UserPasswordUpdatePayload(BaseModel):
    password: str = Field(min_length=6, max_length=64)


class UserQuotaUpdatePayload(BaseModel):
    # ge=-1 允许传 -1 表示无限配额
    max_pages: int = Field(ge=-1, le=9999)
    start_date: str | None = None   # ISO date YYYY-MM-DD
    end_date: str | None = None     # ISO date YYYY-MM-DD


class CreateRechargeOrderPayload(BaseModel):
    plan_type: Literal["free", "basic", "pro", "enterprise"]


class UserPlanUpdatePayload(BaseModel):
    plan_type: Literal["free", "basic", "pro", "enterprise"]


class ResetPasswordPayload(BaseModel):
    """忘记密码：用账号+密钥重置密码"""
    username: str = Field(min_length=1, max_length=32)
    register_key: str = Field(min_length=8, max_length=64)
    new_password: str = Field(min_length=6, max_length=64)
    confirm_password: str = Field(min_length=6, max_length=64)


class RegisterKeyUpdatePayload(BaseModel):
    """更新密钥有效期"""
    expires_at: str | None = None   # ISO datetime，None 表示永不过期


class ApiEnvelope(BaseModel):
    code: int = 0
    data: Any = None
    message: str = "ok"


# 默认用户（密码在 seed 阶段会被哈希存储）
DEFAULT_USERS = [
    {
        "id": "1",
        "username": "admin",
        "password": "123456",
        "real_name": "Admin",
        "desc": "企业门户管理后台管理员",
        "home_path": "/analytics",
        "roles": "admin",
    },
    {
        "id": "2",
        "username": "vben",
        "password": "123456",
        "real_name": "内容编辑",
        "desc": "内容运营与维护",
        "home_path": "/analytics",
        "roles": "super",
    },
    {
        "id": "3",
        "username": "jack",
        "password": "123456",
        "real_name": "Jack",
        "desc": "只读账号",
        "home_path": "/analytics",
        "roles": "user",
    },
]

PLAN_CONFIG: dict[str, dict[str, Any]] = {
    "free": {"name": "免费版", "maxPages": 1, "durationDays": 30},
    "basic": {"name": "基础版", "maxPages": 5, "durationDays": 30},
    "pro": {"name": "专业版", "maxPages": 20, "durationDays": 90},
    "enterprise": {"name": "企业版", "maxPages": -1, "durationDays": 365},
}


def build_plan_quota(plan_type: str) -> dict[str, Any]:
    if plan_type not in PLAN_CONFIG:
        raise HTTPException(status_code=400, detail="套餐类型不合法")

    from datetime import timedelta

    cfg = PLAN_CONFIG[plan_type]
    start_date = today_str()
    end_date = (datetime.now(timezone.utc) + timedelta(days=cfg["durationDays"]))\
        .strftime("%Y-%m-%d")
    return {
        "planType": plan_type,
        "maxPages": cfg["maxPages"],
        "startDate": start_date,
        "endDate": end_date,
    }



# ==================== 数据库工具 ====================


def get_conn() -> sqlite3.Connection:
    """创建并返回 SQLite 连接，同时启用按列名访问行数据。"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def normalize_domain(raw_domain: str) -> str:
    """归一化域名输入：去协议、去端口、去路径、转小写。"""
    domain = raw_domain.strip().lower()
    if "://" in domain:
        domain = domain.split("://", 1)[1]
    domain = domain.split("/", 1)[0]
    domain = domain.split(":", 1)[0]
    domain = domain.strip(".")

    if not domain:
        raise HTTPException(status_code=400, detail="域名不能为空")
    if len(domain) > 253:
        raise HTTPException(status_code=400, detail="域名长度不能超过253")
    if not re.match(r"^[a-z0-9.-]+$", domain):
        raise HTTPException(status_code=400, detail="域名格式不合法")
    return domain


def ensure_auth_tables(conn: sqlite3.Connection) -> None:
    """创建鉴权相关数据表（users、register_keys、user_page_quota、operation_logs、trash）。
    各表均使用 CREATE TABLE IF NOT EXISTS，可安全重复调用。
    同时执行字段迁移：为 register_keys 补充 expires_at 列（旧库升级兼容）。
    """
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id VARCHAR(64) PRIMARY KEY,
            username VARCHAR(64) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            real_name VARCHAR(100) NOT NULL,
            avatar VARCHAR(500) NOT NULL,
            user_desc TEXT NOT NULL,
            home_path VARCHAR(255) NOT NULL,
            roles TEXT NOT NULL,
            created_at VARCHAR(40) NOT NULL
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS register_keys (
            id VARCHAR(64) PRIMARY KEY,
            register_key VARCHAR(255) NOT NULL UNIQUE,
            role TEXT NOT NULL CHECK (role IN ('admin', 'super', 'user')),
            created_by TEXT NOT NULL,
            used_by TEXT,
            used_at TEXT,
            created_at TEXT NOT NULL
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS user_page_quota (
            user_id VARCHAR(64) PRIMARY KEY,
            max_pages INTEGER NOT NULL DEFAULT 1,
            start_date TEXT,
            end_date TEXT
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS recharge_orders (
            id VARCHAR(64) PRIMARY KEY,
            user_id TEXT NOT NULL,
            username TEXT NOT NULL,
            plan_type TEXT NOT NULL CHECK (plan_type IN ('free', 'basic', 'pro', 'enterprise')),
            status TEXT NOT NULL CHECK (status IN ('pending', 'paid')),
            created_at TEXT NOT NULL
        )
        """
    )

    # 操作日志表
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS operation_logs (
            id VARCHAR(64) PRIMARY KEY,
            operator TEXT NOT NULL,
            action TEXT NOT NULL,
            target TEXT NOT NULL DEFAULT '',
            detail TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        )
        """
    )

    # 密钥有效期字段迁移
    rk_cols = {r["name"] for r in conn.execute("PRAGMA table_info(register_keys)").fetchall()}
    if "expires_at" not in rk_cols:
        conn.execute("ALTER TABLE register_keys ADD COLUMN expires_at TEXT")

    # 配额套餐字段迁移
    quota_cols = {r["name"] for r in conn.execute("PRAGMA table_info(user_page_quota)").fetchall()}
    if "plan_type" not in quota_cols:
        conn.execute("ALTER TABLE user_page_quota ADD COLUMN plan_type TEXT NOT NULL DEFAULT 'free'")

    # 回收站表
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS trash (
            id VARCHAR(64) PRIMARY KEY,
            item_type TEXT NOT NULL CHECK (item_type IN ('user', 'page', 'key')),
            item_id TEXT NOT NULL,
            item_data TEXT NOT NULL,
            deleted_by TEXT NOT NULL,
            deleted_at TEXT NOT NULL,
            expire_at TEXT NOT NULL
        )
        """
    )


def seed_default_users(conn: sqlite3.Connection) -> None:
    """初始化默认用户（仅在 users 表为空时执行）。
    默认用户密码以 PBKDF2-SHA256 哈希形式存储，避免明文入库。
    """
    count = conn.execute("SELECT COUNT(1) AS c FROM users").fetchone()["c"]
    if count > 0:
        return

    ts = now_iso()
    for user in DEFAULT_USERS:
        conn.execute(
            """
            INSERT INTO users (
                id, username, password, real_name, avatar, user_desc,
                home_path, roles, created_at
            ) VALUES (?, ?, ?, ?, '', ?, ?, ?, ?)
            """,
            (
                user["id"],
                user["username"],
                hash_password(user["password"]),  # 哈希存储
                user["real_name"],
                user["desc"],
                user["home_path"],
                user["roles"],
                ts,
            ),
        )


def parse_roles(raw_roles: str) -> list[str]:
    """将逗号分隔的角色字符串解析为列表，自动过滤空项。
    例如：'admin,super' -> ['admin', 'super']
    """
    return [item.strip() for item in raw_roles.split(",") if item.strip()]


def row_to_user(row: sqlite3.Row) -> dict[str, Any]:
    """将 users 表行数据转换为前端用户信息字典（含密码字段，仅内部鉴权使用）。"""
    return {
        "password": row["password"],
        "userId": row["id"],
        "username": row["username"],
        "realName": row["real_name"],
        "avatar": row["avatar"],
        "desc": row["user_desc"],
        "homePath": row["home_path"],
        "roles": parse_roles(row["roles"]),
    }


def row_to_user_admin(row: sqlite3.Row) -> dict[str, Any]:
    """将 users 表行数据转换为管理后台用户列表项（不含密码字段，对外安全输出）。"""
    return {
        "userId": row["id"],
        "username": row["username"],
        "realName": row["real_name"],
        "roles": parse_roles(row["roles"]),
        "createdAt": row["created_at"],
    }


def get_user_quota(conn: sqlite3.Connection, user_id: str) -> dict[str, Any]:
    """返回用户配额。admin/super 若无自定义配额则返回 maxPages=-1（无限）。"""
    user_row = conn.execute("SELECT roles FROM users WHERE id = ?", (user_id,)).fetchone()
    roles = set(parse_roles(user_row["roles"])) if user_row else set()
    is_admin = "admin" in roles or "super" in roles

    row = conn.execute(
        "SELECT * FROM user_page_quota WHERE user_id = ?", (user_id,)
    ).fetchone()
    if row:
        return {
            "planType": row["plan_type"] if "plan_type" in row.keys() else "free",
            "maxPages": row["max_pages"],
            "startDate": row["start_date"],
            "endDate": row["end_date"],
        }
    return {"planType": "free", "maxPages": -1 if is_admin else 1, "startDate": None, "endDate": None}


def apply_user_plan(conn: sqlite3.Connection, user_id: str, plan_type: str) -> dict[str, Any]:
    quota = build_plan_quota(plan_type)
    conn.execute(
        """
        INSERT INTO user_page_quota (user_id, plan_type, max_pages, start_date, end_date)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            plan_type = excluded.plan_type,
            max_pages = excluded.max_pages,
            start_date = excluded.start_date,
            end_date = excluded.end_date
        """,
        (user_id, quota["planType"], quota["maxPages"], quota["startDate"], quota["endDate"]),
    )
    return quota


def get_user_by_login(login_name: str) -> dict[str, Any] | None:
    """通过用户名查询用户信息（含密码），用于登录验证。未找到时返回 None。"""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (login_name,),
        ).fetchone()
    return row_to_user(row) if row else None


def get_user_by_username(username: str) -> dict[str, Any] | None:
    """通过用户名查询用户信息（get_user_by_login 的语义别名，供 Token 解析流程调用）。"""
    return get_user_by_login(username)


def get_current_user(authorization: str | None) -> dict[str, Any]:
    """从请求头 Authorization 中解析当前登录用户。"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录或Token无效")

    token = authorization.removeprefix("Bearer ").strip()
    payload = jwt_decode(token)
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Token 无效")

    user = get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user


def is_admin_user(user: dict[str, Any]) -> bool:
    """判断用户是否具有管理员权限（角色包含 'admin' 或 'super' 时返回 True）。"""
    roles = set(user.get("roles", []))
    return "super" in roles or "admin" in roles


def xss_escape(value: str | None) -> str:
    """XSS 基础防护：对用户可控文本进行 HTML 转义。"""
    return html.escape(value) if value else ""


def check_owner(row: dict[str, Any] | None, current_user: dict[str, Any]) -> None:
    """防越权校验：仅资源所有者或管理员可操作。"""
    if not row:
        raise HTTPException(status_code=404, detail="资源不存在")
    if row.get("owner_username") != current_user["username"] and not is_admin_user(current_user):
        raise HTTPException(status_code=403, detail="无权操作")


def log_operation(
    operator: str,
    action: str,
    target: str = "",
    detail: str = "",
) -> None:
    """记录操作日志（静默失败，不影响主流程）。"""
    try:
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO operation_logs (id, operator, action, target, detail, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), operator, action, target, detail, now_iso()),
            )
    except Exception:
        pass


TRASH_RETAIN_DAYS = 0  # 0 表示永久保留，不自动过期


def trash_put(
    conn: sqlite3.Connection,
    item_type: str,
    item_id: str,
    item_data: dict,
    deleted_by: str,
) -> None:
    """将对象放入回收站，永久保留直到手动删除。"""
    from datetime import timedelta
    ts = datetime.now(timezone.utc)
    # expire_at 设置为 9999 年，视为永不过期
    expire = datetime(9999, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
    conn.execute(
        "INSERT OR REPLACE INTO trash (id, item_type, item_id, item_data, deleted_by, deleted_at, expire_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            str(uuid.uuid4()),
            item_type,
            item_id,
            json.dumps(item_data, ensure_ascii=False),
            deleted_by,
            ts.isoformat(),
            expire.isoformat(),
        ),
    )


def trash_cleanup(conn: sqlite3.Connection) -> None:
    """清理已过期的回收站条目（永久保留模式下基本不触发）。"""
    conn.execute("DELETE FROM trash WHERE expire_at < ?", (now_iso(),))


def ensure_db_schema(conn: sqlite3.Connection) -> None:
    """初始化并迁移数据库结构。"""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS site_pages (
            id VARCHAR(64) PRIMARY KEY,
            owner_username TEXT NOT NULL,
            site_path VARCHAR(255) NOT NULL UNIQUE,
            bind_domain VARCHAR(255) NOT NULL UNIQUE,
            site_name TEXT NOT NULL,
            site_description TEXT NOT NULL,
            template_id TEXT NOT NULL,
            nav_items TEXT NOT NULL,
            colors TEXT NOT NULL,
            fonts TEXT NOT NULL,
            status TEXT NOT NULL CHECK (status IN ('draft', 'published')),
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )

    columns = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(site_pages)").fetchall()
    }

    if "owner_username" not in columns:
        conn.execute(
            "ALTER TABLE site_pages ADD COLUMN owner_username TEXT NOT NULL DEFAULT 'admin'"
        )

    if "bind_domain" not in columns:
        conn.execute(
            "ALTER TABLE site_pages ADD COLUMN bind_domain TEXT NOT NULL DEFAULT ''"
        )

    rows_without_domain = conn.execute(
        "SELECT id FROM site_pages WHERE bind_domain IS NULL OR TRIM(bind_domain) = ''"
    ).fetchall()
    for row in rows_without_domain:
        page_id = row["id"]
        conn.execute(
            "UPDATE site_pages SET bind_domain = ? WHERE id = ?",
            (f"{page_id}.local", page_id),
        )


def kill_port_conflict(port: int) -> None:
    """检测指定端口是否被多个进程监听，若存在冲突的旧进程则自动终止。
    仅终止与当前进程不同的同端口监听进程，开发和生产环境均生效。
    """
    import os
    import signal
    import socket
    import sys

    current_pid = os.getpid()

    # 通过尝试绑定端口来快速判断是否有冲突（仅作预检）
    try:
        probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        probe.bind(("", port))
        probe.close()
        # 能绑定成功说明没有冲突，直接返回
        return
    except OSError:
        pass

    # 端口被占用，尝试用 psutil 找到占用进程并终止
    try:
        import psutil
        killed: list[int] = []
        for conn in psutil.net_connections(kind="tcp"):
            if conn.laddr.port == port and conn.pid and conn.pid != current_pid:
                try:
                    proc = psutil.Process(conn.pid)
                    print(
                        f"[startup] 检测到端口 {port} 被旧进程占用 "
                        f"(PID={conn.pid}, name={proc.name()})，正在终止...",
                        flush=True,
                    )
                    if sys.platform == "win32":
                        proc.kill()
                    else:
                        os.kill(conn.pid, signal.SIGTERM)
                    killed.append(conn.pid)
                except (psutil.NoSuchProcess, psutil.AccessDenied, ProcessLookupError):
                    pass
        if killed:
            import time
            time.sleep(0.8)  # 等待旧进程退出
            print(f"[startup] 已清理旧进程 PID: {killed}，端口 {port} 释放完毕。", flush=True)
    except ImportError:
        # psutil 未安装时降级处理：仅打印警告，不影响启动
        print(
            f"[startup] 警告：psutil 未安装，无法自动清理端口 {port} 的旧进程。"
            "请手动终止旧进程或安装 psutil。",
            flush=True,
        )


def init_db() -> None:
    """应用启动时初始化数据库：建表、字段迁移、注入默认用户。由 lifespan 在启动时调用。"""
    with get_conn() as conn:
        ensure_db_schema(conn)
        ensure_auth_tables(conn)
        seed_default_users(conn)


def row_to_page(row: sqlite3.Row) -> SitePageOut:
    """将 site_pages 表行数据反序列化为 SitePageOut 模型（nav_items/colors/fonts 为 JSON 字段）。"""
    return SitePageOut(
        id=row["id"],
        owner_username=row["owner_username"],
        site_path=row["site_path"],
        bind_domain=row["bind_domain"],
        site_name=row["site_name"],
        site_description=row["site_description"],
        template_id=row["template_id"],
        nav_items=json.loads(row["nav_items"]),
        colors=json.loads(row["colors"]),
        fonts=json.loads(row["fonts"]),
        status=row["status"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def check_path_unique(
    conn: sqlite3.Connection,
    site_path: str,
    exclude_id: str | None = None,
) -> None:
    """检查 site_path 唯一性，冲突时抛出 409 异常。
    exclude_id：更新场景下排除自身 ID，避免与自己冲突。
    """
    if exclude_id:
        row = conn.execute(
            "SELECT id FROM site_pages WHERE site_path = ? AND id != ?",
            (site_path, exclude_id),
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT id FROM site_pages WHERE site_path = ?",
            (site_path,),
        ).fetchone()

    if row:
        raise HTTPException(status_code=409, detail="site_path 已存在")


def check_domain_unique(
    conn: sqlite3.Connection,
    bind_domain: str,
    exclude_id: str | None = None,
) -> None:
    """检查 bind_domain 唯一性，冲突时抛出 409 异常。
    exclude_id：更新场景下排除自身 ID，避免与自己冲突。
    """
    if exclude_id:
        row = conn.execute(
            "SELECT id FROM site_pages WHERE bind_domain = ? AND id != ?",
            (bind_domain, exclude_id),
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT id FROM site_pages WHERE bind_domain = ?",
            (bind_domain,),
        ).fetchone()

    if row:
        raise HTTPException(status_code=409, detail="域名已被占用")


# ==================== 安全增强与生产配置（不改变业务语义） ====================


def safe_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False)


def _convert_sql_placeholders(query: str) -> str:
    """将 SQLite 的 ? 占位符转换为 MySQL 的 %s 占位符。"""
    return query.replace("?", "%s")


def _parse_mysql_url(url: str) -> dict[str, Any]:
    parsed = urlparse(url)
    if parsed.scheme not in {"mysql", "mysql+pymysql"}:
        raise RuntimeError("DATABASE_URL 必须使用 mysql:// 或 mysql+pymysql://")
    return {
        "host": parsed.hostname or "127.0.0.1",
        "port": parsed.port or 3306,
        "user": unquote(parsed.username or "root"),
        "password": unquote(parsed.password or "123456"),
        "database": (parsed.path or "/template_cms").lstrip("/"),
        "charset": "utf8mb4",
        "autocommit": False,
        "cursorclass": pymysql.cursors.DictCursor,
        "connect_timeout": int(os.environ.get("MYSQL_CONNECT_TIMEOUT", "5")),
        "read_timeout": int(os.environ.get("MYSQL_READ_TIMEOUT", "10")),
        "write_timeout": int(os.environ.get("MYSQL_WRITE_TIMEOUT", "10")),
    }


class DbConn:
    """兼容 SQLite 调用习惯的 MySQL 连接包装器。"""

    def __init__(self, conn: Any):
        self._conn = conn

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is None:
            self._conn.commit()
        else:
            self._conn.rollback()
        self._conn.close()

    def execute(self, query: str, params: list[Any] | tuple[Any, ...] | None = None):
        sql = _convert_sql_placeholders(query)
        cursor = self._conn.cursor()
        cursor.execute(sql, params or ())
        return cursor

    def commit(self):
        self._conn.commit()



def get_conn() -> DbConn:
    """统一数据库连接：使用 MySQL（生产可用）。"""
    cfg = _parse_mysql_url(DATABASE_URL)
    try:
        raw = pymysql.connect(**cfg)
    except Exception as e:
        logger.exception(
            "数据库连接失败 host=%s port=%s database=%s err=%s",
            cfg["host"],
            cfg["port"],
            cfg["database"],
            e,
        )
        raise
    return DbConn(raw)


def ensure_auth_tables(conn: Any) -> None:
    """创建鉴权相关表，并创建安全事件表。"""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id VARCHAR(64) PRIMARY KEY,
            username VARCHAR(64) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            real_name VARCHAR(100) NOT NULL,
            avatar VARCHAR(500) NOT NULL DEFAULT '',
            user_desc TEXT NOT NULL,
            home_path VARCHAR(255) NOT NULL DEFAULT '/analytics',
            roles TEXT NOT NULL,
            created_at VARCHAR(40) NOT NULL
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS register_keys (
            id VARCHAR(64) PRIMARY KEY,
            register_key VARCHAR(255) NOT NULL UNIQUE,
            role VARCHAR(20) NOT NULL,
            created_by VARCHAR(64) NOT NULL,
            used_by VARCHAR(64),
            used_at VARCHAR(40),
            created_at VARCHAR(40) NOT NULL,
            expires_at VARCHAR(40)
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS user_page_quota (
            user_id VARCHAR(64) PRIMARY KEY,
            max_pages INTEGER NOT NULL DEFAULT 1,
            start_date VARCHAR(40),
            end_date VARCHAR(40),
            plan_type VARCHAR(20) NOT NULL DEFAULT 'free'
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS recharge_orders (
            id VARCHAR(64) PRIMARY KEY,
            user_id VARCHAR(64) NOT NULL,
            username VARCHAR(64) NOT NULL,
            plan_type VARCHAR(20) NOT NULL,
            status VARCHAR(20) NOT NULL,
            created_at VARCHAR(40) NOT NULL
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS operation_logs (
            id VARCHAR(64) PRIMARY KEY,
            operator VARCHAR(64) NOT NULL,
            action VARCHAR(64) NOT NULL,
            target VARCHAR(255) NOT NULL DEFAULT '',
            detail TEXT NOT NULL,
            created_at VARCHAR(40) NOT NULL
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS security_events (
            id VARCHAR(64) PRIMARY KEY,
            event_type VARCHAR(64) NOT NULL,
            ip VARCHAR(64) NOT NULL,
            path VARCHAR(255) NOT NULL,
            method VARCHAR(16) NOT NULL,
            detail TEXT NOT NULL,
            ua TEXT NOT NULL,
            created_at VARCHAR(40) NOT NULL
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS trash (
            id VARCHAR(64) PRIMARY KEY,
            item_type VARCHAR(20) NOT NULL,
            item_id VARCHAR(64) NOT NULL,
            item_data LONGTEXT NOT NULL,
            deleted_by VARCHAR(64) NOT NULL,
            deleted_at VARCHAR(40) NOT NULL,
            expire_at VARCHAR(40) NOT NULL
        )
        """
    )


def ensure_db_schema(conn: Any) -> None:
    """初始化并迁移 site_pages 结构（MySQL 版本）。"""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS site_pages (
            id VARCHAR(64) PRIMARY KEY,
            owner_username VARCHAR(64) NOT NULL,
            site_path VARCHAR(255) NOT NULL UNIQUE,
            bind_domain VARCHAR(255) NOT NULL UNIQUE,
            site_name VARCHAR(255) NOT NULL,
            site_description TEXT NOT NULL,
            template_id VARCHAR(64) NOT NULL,
            nav_items LONGTEXT NOT NULL,
            colors LONGTEXT NOT NULL,
            fonts LONGTEXT NOT NULL,
            status VARCHAR(20) NOT NULL,
            created_at VARCHAR(40) NOT NULL,
            updated_at VARCHAR(40) NOT NULL
        )
        """
    )


def mysql_execute(conn: Any, query: str, params: list[Any] | tuple[Any, ...] | None = None):
    """统一执行 SQL，自动占位符转换，避免拼接 SQL 造成注入风险。"""
    sql = _convert_sql_placeholders(query)
    return conn.execute(sql, params or ())


def log_security_event(event_type: str, ip: str, path: str, method: str, detail: str = "", ua: str = "") -> None:
    """记录安全日志到文件与数据库。"""
    logger.warning(
        "security_event type=%s ip=%s path=%s method=%s detail=%s",
        event_type,
        ip,
        path,
        method,
        detail,
    )
    try:
        with get_conn() as conn:
            mysql_execute(
                conn,
                "INSERT INTO security_events (id, event_type, ip, path, method, detail, ua, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), event_type, ip, path, method, detail, ua, now_iso()),
            )
            conn.commit()
    except Exception:
        pass


def _redis_incr_window(key: str, window: int) -> int:
    """Redis 不可用时降级，避免影响接口访问（如 /docs）。"""
    try:
        n = redis_client.incr(key)
        if n == 1:
            redis_client.expire(key, window)
        return int(n)
    except Exception:
        return 1


def check_login_rate_limit(ip: str) -> None:
    """登录防暴力破解（Redis 持久化计数 + 锁定）。Redis 不可用时降级放行。"""
    try:
        lock_key = _rk(f"login:lock:{ip}")
        ttl = redis_client.ttl(lock_key)
        if ttl and ttl > 0:
            raise HTTPException(status_code=429, detail=f"登录失败过多，请 {ttl} 秒后重试")
    except HTTPException:
        raise
    except Exception:
        return


def record_login_fail(ip: str) -> None:
    fail_key = _rk(f"login:fail:{ip}")
    cnt = _redis_incr_window(fail_key, _LOGIN_WINDOW_SEC)
    if cnt >= _LOGIN_MAX_FAIL:
        try:
            redis_client.setex(_rk(f"login:lock:{ip}"), _LOGIN_LOCK_SEC, "1")
        except Exception:
            return


def clear_login_fail(ip: str) -> None:
    try:
        redis_client.delete(_rk(f"login:fail:{ip}"), _rk(f"login:lock:{ip}"))
    except Exception:
        return


def get_user_token_version(username: str) -> int:
    k = _rk(f"jwt:ver:{username}")
    try:
        v = redis_client.get(k)
        if v is None:
            redis_client.set(k, "1")
            return 1
        return int(v)
    except Exception:
        return 1


def bump_user_token_version(username: str) -> int:
    k = _rk(f"jwt:ver:{username}")
    try:
        return int(redis_client.incr(k))
    except Exception:
        return 1


def blacklist_token(token: str, exp_ts: float | None = None) -> None:
    fp = hashlib.sha256(token.encode()).hexdigest()
    ttl = JWT_BLACKLIST_TTL_SEC
    if exp_ts:
        ttl = max(1, int(exp_ts - time.time()) + 60)
    try:
        redis_client.setex(_rk(f"jwt:blacklist:{fp}"), ttl, "1")
    except Exception:
        return


def is_token_blacklisted(token: str) -> bool:
    fp = hashlib.sha256(token.encode()).hexdigest()
    try:
        return bool(redis_client.exists(_rk(f"jwt:blacklist:{fp}")))
    except Exception:
        return False


def create_access_token(username: str) -> str:
    """生成 JWT，并注入 jti/ver 以支持黑名单和强制下线。"""
    exp = time.time() + JWT_ACCESS_EXPIRE_MINUTES * 60
    return jwt_encode(
        {
            "sub": username,
            "exp": exp,
            "iat": time.time(),
            "jti": str(uuid.uuid4()),
            "ver": get_user_token_version(username),
        }
    )


def jwt_decode(token: str) -> dict:
    """验证签名、过期、黑名单、token 版本。"""
    import base64

    if is_token_blacklisted(token):
        raise HTTPException(status_code=401, detail="Token 已失效")

    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("格式错误")
        header_b, body_b, sig_b = parts
        expected_sig = hmac.new(JWT_SECRET.encode(), f"{header_b}.{body_b}".encode(), hashlib.sha256).digest()
        actual_sig = base64.urlsafe_b64decode(sig_b + "==")
        if not hmac.compare_digest(expected_sig, actual_sig):
            raise ValueError("签名无效")

        pad = lambda s: s + "=" * (-len(s) % 4)
        payload = json.loads(base64.urlsafe_b64decode(pad(body_b)).decode())
        if payload.get("exp") and time.time() > payload["exp"]:
            raise ValueError("Token 已过期")

        username = payload.get("sub")
        if username:
            current_ver = get_user_token_version(username)
            token_ver = int(payload.get("ver", 1))
            if token_ver != current_ver:
                raise ValueError("Token 已被强制下线")
        return payload
    except ValueError as e:
        raise HTTPException(status_code=401, detail=f"Token 无效：{e}")


class SecurityMiddleware(BaseHTTPMiddleware):
    """全局安全中间件：IP 限流、CC 防护、反爬、安全响应头。"""

    async def dispatch(self, request: Request, call_next):
        ip = get_client_ip(request)
        path = request.url.path
        method = request.method.upper()
        ua = request.headers.get("user-agent", "")

        # 全局接口限流（IP 维度）
        global_key = _rk(f"rl:global:{ip}")
        if _redis_incr_window(global_key, GLOBAL_RATE_WINDOW_SEC) > GLOBAL_RATE_LIMIT:
            log_security_event("rate_limit_block", ip, path, method, detail="global", ua=ua)
            return JSONResponse(status_code=429, content={"detail": "请求过于频繁，请稍后重试"})

        # 防 CC：IP + Path 高频限制
        cc_key = _rk(f"rl:cc:{ip}:{path}")
        if _redis_incr_window(cc_key, CC_PATH_RATE_WINDOW_SEC) > CC_PATH_RATE_LIMIT:
            log_security_event("cc_block", ip, path, method, detail="path", ua=ua)
            return JSONResponse(status_code=429, content={"detail": "访问过于频繁，已触发防护"})

        # 防爬虫：基础 UA 风险评分
        bot_score = 0
        ua_low = ua.lower()
        if not ua:
            bot_score += 40
        if any(k in ua_low for k in ["curl", "python", "wget", "scrapy", "spider", "bot"]):
            bot_score += 70
        if request.headers.get("accept", "") == "*/*":
            bot_score += 15
        if path.startswith("/api/public") and not request.headers.get("accept-language"):
            bot_score += 10

        if bot_score >= BOT_SCORE_BLOCK:
            log_security_event("bot_block", ip, path, method, detail=f"score={bot_score}", ua=ua)
            return JSONResponse(status_code=403, content={"detail": "请求被安全策略拦截"})

        resp = await call_next(request)

        # 安全响应头
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        resp.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        if FORCE_HTTPS:
            resp.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        return resp


# ==================== FastAPI App ====================


@asynccontextmanager
async def lifespan(_: FastAPI):
    api_host = os.environ.get("API_HOST", "127.0.0.1")
    api_port = int(os.environ.get("API_PORT", "5322"))

    kill_port_conflict(api_port)
    init_db()

    print(f"[startup] Template CMS API: http://{api_host}:{api_port}", flush=True)
    yield


app = FastAPI(
    title="Template CMS API",
    version="2.0.0",
    lifespan=lifespan,
    docs_url=None if IS_PROD else "/docs",
    redoc_url=None if IS_PROD else "/redoc",
    openapi_url=None if IS_PROD else "/openapi.json",
)

# Host 白名单 + HTTPS 重定向（生产安全）
app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)
if FORCE_HTTPS:
    app.add_middleware(HTTPSRedirectMiddleware)

# 全局安全中间件（限流/反爬/安全头）
app.add_middleware(SecurityMiddleware)

# 严格 CORS：仅允许白名单域名，限制方法和头
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)


@app.get("/health")
def health() -> dict[str, str]:
    """健康检查接口，返回服务运行状态，供负载均衡/监控系统探测使用。"""
    return {"status": "ok"}


@app.get("/api/status")
def api_status() -> dict[str, str]:
    """API 状态检查接口，功能同 /health，兼容前端路径约定。"""
    return {"status": "ok"}


# ==================== 页面管理接口（带用户权限） ====================


@app.post("/api/site-pages", response_model=ApiEnvelope)
def create_site_page(
    payload: SitePageCreate,
    authorization: str | None = Header(default=None),
) -> ApiEnvelope:
    """创建新站点页面。
    - 普通用户受配额（max_pages / 有效期）限制；admin/super 无限制。
    - 检查 site_path 和 bind_domain 唯一性，冲突返回 409。
    """
    user = get_current_user(authorization)
    owner_username = user["username"]
    site_path: str = xss_escape(payload.site_path)
    site_name: str = xss_escape(payload.site_name)
    site_description: str = xss_escape(payload.site_description)
    bind_domain = normalize_domain(payload.bind_domain)

    ts = now_iso()
    page_id = str(uuid.uuid4())

    with get_conn() as conn:
        if not is_admin_user(user):
            quota = get_user_quota(conn, user["userId"])
            max_pages = quota["maxPages"]
            start_date = quota["startDate"]
            end_date = quota["endDate"]

            # max_pages == -1 表示无限，跳过数量限制
            if max_pages != -1:
                today = today_str()
                if start_date and today < start_date:
                    raise HTTPException(status_code=403, detail="生成权限尚未开始")
                if end_date and today > end_date:
                    raise HTTPException(status_code=403, detail="生成权限已过期")

            count = conn.execute(
                "SELECT COUNT(1) AS c FROM site_pages WHERE owner_username = ?",
                (owner_username,),
            ).fetchone()["c"]
            if count >= max_pages:
                raise HTTPException(
                    status_code=403,
                    detail=f"已达到最大生成页面数量（{max_pages}）",
                )

        check_path_unique(conn, site_path)
        check_domain_unique(conn, bind_domain)

        conn.execute(
            """
            INSERT INTO site_pages (
                id, owner_username, site_path, bind_domain, site_name, site_description,
                template_id, nav_items, colors, fonts, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                page_id,
                owner_username,
                site_path,
                bind_domain,
                site_name,
                site_description,
                payload.template_id,
                json.dumps(payload.nav_items, ensure_ascii=False),
                json.dumps(payload.colors, ensure_ascii=False),
                json.dumps(payload.fonts, ensure_ascii=False),
                payload.status,
                ts,
                ts,
            ),
        )
        row = conn.execute(
            "SELECT * FROM site_pages WHERE id = ?",
            (page_id,),
        ).fetchone()

    if not row:
        raise HTTPException(status_code=500, detail="创建失败")
    return ApiEnvelope(code=0, data=row_to_page(row), message="ok")


@app.put("/api/site-pages/{page_id}", response_model=ApiEnvelope)
def update_site_page(
    page_id: str,
    payload: SitePageUpdate,
    authorization: str | None = Header(default=None),
) -> ApiEnvelope:
    """更新站点页面（支持部分字段更新）。
    - 仅页面所有者或 admin/super 可操作。
    - 若更新 bind_domain 则重新做唯一性校验和域名归一化。
    """
    user = get_current_user(authorization)

    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM site_pages WHERE id = ?",
            (page_id,),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="页面不存在")

        owner_username = row["owner_username"]
        if owner_username != user["username"] and not is_admin_user(user):
            raise HTTPException(status_code=403, detail="无权编辑该页面")

        current = dict(row)
        data = payload.model_dump(exclude_unset=True)

        if "site_path" in data:
            check_path_unique(conn, data["site_path"], exclude_id=page_id)

        next_domain = current["bind_domain"]
        if "bind_domain" in data:
            next_domain = normalize_domain(data["bind_domain"])
            check_domain_unique(conn, next_domain, exclude_id=page_id)

        merged = {
            "site_path": data.get("site_path", current["site_path"]),
            "bind_domain": next_domain,
            "site_name": data.get("site_name", current["site_name"]),
            "site_description": data.get("site_description", current["site_description"]),
            "template_id": data.get("template_id", current["template_id"]),
            "nav_items": data.get("nav_items", json.loads(current["nav_items"])),
            "colors": data.get("colors", json.loads(current["colors"])),
            "fonts": data.get("fonts", json.loads(current["fonts"])),
            "status": data.get("status", current["status"]),
            "updated_at": now_iso(),
        }

        conn.execute(
            """
            UPDATE site_pages
            SET site_path = ?, bind_domain = ?, site_name = ?, site_description = ?,
                template_id = ?, nav_items = ?, colors = ?, fonts = ?, status = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                merged["site_path"],
                merged["bind_domain"],
                merged["site_name"],
                merged["site_description"],
                merged["template_id"],
                json.dumps(merged["nav_items"], ensure_ascii=False),
                json.dumps(merged["colors"], ensure_ascii=False),
                json.dumps(merged["fonts"], ensure_ascii=False),
                merged["status"],
                merged["updated_at"],
                page_id,
            ),
        )

        updated = conn.execute(
            "SELECT * FROM site_pages WHERE id = ?",
            (page_id,),
        ).fetchone()

    if not updated:
        raise HTTPException(status_code=500, detail="更新失败")
    return ApiEnvelope(code=0, data=row_to_page(updated), message="ok")


@app.delete("/api/site-pages/{page_id}", response_model=ApiEnvelope)
def delete_site_page(
    page_id: str,
    authorization: str | None = Header(default=None),
) -> ApiEnvelope:
    """删除站点页面（软删除）。
    - 仅页面所有者或 admin/super 可操作。
    - 删除前将页面快照写入回收站，并记录操作日志。
    """
    user = get_current_user(authorization)

    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM site_pages WHERE id = ?",
            (page_id,),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="页面不存在")

        if row["owner_username"] != user["username"] and not is_admin_user(user):
            raise HTTPException(status_code=403, detail="无权删除该页面")

        trash_put(conn, "page", page_id, dict(row), user["username"])
        conn.execute("DELETE FROM site_pages WHERE id = ?", (page_id,))

    log_operation(user["username"], "delete_page", page_id, f"删除页面: {row['site_name']}")
    return ApiEnvelope(code=0, data=True, message="ok")


@app.get("/api/site-pages", response_model=ApiEnvelope)
def list_site_pages(
    status: Literal["draft", "published"] | None = Query(default=None),
    authorization: str | None = Header(default=None),
) -> ApiEnvelope:
    """获取当前登录用户自己创建的站点页面列表。
    - 所有角色只能查看自己名下的页面。
    - 可通过 status 参数过滤 draft/published。
    """
    user = get_current_user(authorization)

    with get_conn() as conn:
        # 所有角色只查看自己生成的页面
            if status:
                rows = conn.execute(
                    """
                    SELECT * FROM site_pages
                    WHERE owner_username = ? AND status = ?
                    ORDER BY created_at DESC
                    """,
                    (user["username"], status),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT * FROM site_pages
                    WHERE owner_username = ?
                    ORDER BY created_at DESC
                    """,
                    (user["username"],),
                ).fetchall()

    return ApiEnvelope(code=0, data=[row_to_page(row) for row in rows], message="ok")


@app.get("/api/site-pages/{page_id}", response_model=ApiEnvelope)
def get_site_page(
    page_id: str,
    authorization: str | None = Header(default=None),
) -> ApiEnvelope:
    """获取指定页面详情。仅页面所有者或 admin/super 可访问，否则返回 403。"""
    user = get_current_user(authorization)

    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM site_pages WHERE id = ?",
            (page_id,),
        ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="页面不存在")

    if row["owner_username"] != user["username"] and not is_admin_user(user):
        raise HTTPException(status_code=403, detail="无权访问该页面")

    return ApiEnvelope(code=0, data=row_to_page(row), message="ok")


# ==================== 公开访问接口（按路径/域名） ====================


@app.get("/api/public/site-pages/path/{site_path}", response_model=ApiEnvelope)
def get_public_site_page_by_path(site_path: str) -> ApiEnvelope:
    """公开接口：通过 site_path 获取已发布页面，无需登录。"""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM site_pages WHERE site_path = ? AND status = 'published'",
            (site_path,),
        ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="公开页面不存在或未发布")
    return ApiEnvelope(code=0, data=row_to_page(row), message="ok")


@app.get("/api/public/site-pages/domain/{domain}", response_model=ApiEnvelope)
def get_public_site_page_by_domain(domain: str) -> ApiEnvelope:
    """公开接口：通过绑定域名获取已发布页面，无需登录。域名会自动归一化处理。"""
    normalized = normalize_domain(domain)
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM site_pages WHERE bind_domain = ? AND status = 'published'",
            (normalized,),
        ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="该域名未绑定已发布页面")
    return ApiEnvelope(code=0, data=row_to_page(row), message="ok")


# 兼容旧接口（已废弃，内部转发给 get_public_site_page_by_path）
@app.get("/api/public/site-pages/{site_path}", response_model=ApiEnvelope)
def get_public_site_page(site_path: str) -> ApiEnvelope:
    """旧版公开接口，保留以兼容历史调用，内部转发给 get_public_site_page_by_path。"""
    return get_public_site_page_by_path(site_path)


# ==================== vben 管理后台鉴权接口 ====================


@app.post("/api/auth/login", response_model=ApiEnvelope)
def auth_login(payload: LoginPayload, request: Request) -> ApiEnvelope:
    """用户登录接口（Redis 持久化防暴力破解）。"""
    client_ip = get_client_ip(request)
    check_login_rate_limit(client_ip)

    user = get_user_by_login(payload.username)
    if not user or not verify_password(payload.password, user["password"]):
        record_login_fail(client_ip)
        log_security_event("login_fail", client_ip, "/api/auth/login", "POST", detail=f"username={payload.username}", ua=request.headers.get("user-agent", ""))
        return ApiEnvelope(code=10001, data=None, message="用户名或密码错误")

    clear_login_fail(client_ip)

    # 若旧密码是明文，登录成功后升级为哈希
    if user["password"] == payload.password:
        with get_conn() as conn:
            conn.execute(
                "UPDATE users SET password = ? WHERE username = ?",
                (hash_password(payload.password), payload.username),
            )

    token = create_access_token(user["username"])
    return ApiEnvelope(code=0, data={"accessToken": token}, message="ok")


@app.post("/api/auth/register", response_model=ApiEnvelope)
def auth_register(payload: RegisterPayload) -> ApiEnvelope:
    """用户注册接口。
    - 校验用户名格式（字母/数字/下划线，3-32位）。
    - 验证注册密钥有效性（不存在/已使用均拒绝）。
    - 注册成功后密码哈希存储，密钥标记为已使用。
    """
    username = payload.username.strip()
    if not re.match(r"^[a-zA-Z0-9_]{3,32}$", username):
        return ApiEnvelope(code=10002, data=None, message="用户名仅支持字母数字下划线，长度3-32")

    with get_conn() as conn:
        exists = conn.execute(
            "SELECT id FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        if exists:
            return ApiEnvelope(code=10003, data=None, message="用户名已存在")

        key_row = conn.execute(
            "SELECT * FROM register_keys WHERE register_key = ?",
            (payload.register_key.strip(),),
        ).fetchone()
        if not key_row:
            return ApiEnvelope(code=10004, data=None, message="密钥不存在")

        if key_row["used_by"]:
            return ApiEnvelope(code=10005, data=None, message="密钥已被使用")

        role = key_row["role"]
        ts = now_iso()
        user_id = str(uuid.uuid4())

        conn.execute(
            """
            INSERT INTO users (
                id, username, password, real_name, avatar, user_desc,
                home_path, roles, created_at
            ) VALUES (?, ?, ?, ?, '', '', ?, ?, ?)
            """,
            (user_id, username, hash_password(payload.password), username, "/analytics", role, ts),
        )
        conn.execute(
            "UPDATE register_keys SET used_by = ?, used_at = ? WHERE id = ?",
            (username, ts, key_row["id"]),
        )

    return ApiEnvelope(code=0, data=True, message="注册成功")


@app.post("/api/auth/register-keys", response_model=ApiEnvelope)
def create_register_key(
    payload: RegisterKeyCreatePayload,
    authorization: str | None = Header(default=None),
) -> ApiEnvelope:
    user = get_current_user(authorization)
    if not is_admin_user(user):  # 修复：admin 和 super 都可以生成密钥
        raise HTTPException(status_code=403, detail="仅管理员可生成密钥")

    register_key = f"KEY-{secrets.token_hex(8).upper()}"
    ts = now_iso()
    key_id = str(uuid.uuid4())

    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO register_keys (
                id, register_key, role, created_by, used_by, used_at, created_at
            ) VALUES (?, ?, ?, ?, NULL, NULL, ?)
            """,
            (key_id, register_key, payload.role, user["username"], ts),
        )

    return ApiEnvelope(
        code=0,
        data={
            "id": key_id,
            "registerKey": register_key,
            "role": payload.role,
            "createdBy": user["username"],
            "createdAt": ts,
        },
        message="ok",
    )


@app.get("/api/auth/register-stats", response_model=ApiEnvelope)
def register_stats(authorization: str | None = Header(default=None)) -> ApiEnvelope:
    """获取注册统计数据（总用户数、admin 和 super 各角色人数）。仅管理员可调用。"""
    user = get_current_user(authorization)
    if not is_admin_user(user):
        raise HTTPException(status_code=403, detail="仅管理员可查看")

    with get_conn() as conn:
        total = conn.execute("SELECT COUNT(1) AS c FROM users").fetchone()["c"]
        admin_count = conn.execute(
            "SELECT COUNT(1) AS c FROM users WHERE instr(',' || roles || ',', ',admin,') > 0"
        ).fetchone()["c"]
        super_count = conn.execute(
            "SELECT COUNT(1) AS c FROM users WHERE instr(',' || roles || ',', ',super,') > 0"
        ).fetchone()["c"]

    return ApiEnvelope(
        code=0,
        data={
            "totalUsers": total,
            "adminUsers": admin_count,
            "superUsers": super_count,
        },
        message="ok",
    )


@app.get("/api/auth/plans", response_model=ApiEnvelope)
def list_plans(authorization: str | None = Header(default=None)) -> ApiEnvelope:
    """获取套餐列表（登录后可查看）。"""
    _ = get_current_user(authorization)
    plans = [
        {
            "planType": k,
            "name": v["name"],
            "maxPages": v["maxPages"],
            "durationDays": v["durationDays"],
        }
        for k, v in PLAN_CONFIG.items()
    ]
    return ApiEnvelope(code=0, data=plans, message="ok")


@app.post("/api/auth/recharge-orders", response_model=ApiEnvelope)
def create_recharge_order(
    payload: CreateRechargeOrderPayload,
    authorization: str | None = Header(default=None),
) -> ApiEnvelope:
    """用户提交充值订单。
    - 演示/测试环境：创建 pending 订单并返回 mock Native 二维码链接，
      用户扫码后前端调用 mock-pay 接口模拟支付成功。
    - 生产环境：此处替换为微信 Native 下单 API，返回真实 code_url。
    """
    user = get_current_user(authorization)
    if is_admin_user(user):
        raise HTTPException(status_code=403, detail="管理员请使用用户套餐管理页面")

    ts = now_iso()
    order_id = str(uuid.uuid4())
    plan_cfg = PLAN_CONFIG.get(payload.plan_type)
    if not plan_cfg:
        raise HTTPException(status_code=400, detail="套餐类型不合法")

    # 生成 mock Native 二维码内容（格式与微信 code_url 一致，便于将来替换）
    mock_code_url = f"weixin://wxpay/bizpayurl?pr=MOCK_{order_id[:8].upper()}"

    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO recharge_orders (id, user_id, username, plan_type, status, created_at)
            VALUES (?, ?, ?, ?, 'pending', ?)
            """,
            (order_id, user["userId"], user["username"], payload.plan_type, ts),
        )

    log_operation(user["username"], "create_recharge_order", order_id, f"发起充值: {payload.plan_type}")
    return ApiEnvelope(
        code=0,
        data={
            "orderId": order_id,
            "codeUrl": mock_code_url,
            "planType": payload.plan_type,
            "planName": plan_cfg["name"],
        },
        message="订单已创建，请扫码支付",
    )


@app.post("/api/auth/recharge-orders/{order_id}/mock-pay", response_model=ApiEnvelope)
def mock_pay_order(
    order_id: str,
    authorization: str | None = Header(default=None),
) -> ApiEnvelope:
    """演示环境模拟支付成功回调。
    - 仅 pending 状态的订单可调用。
    - 支付成功后立即发放套餐权益，订单状态改为 paid。
    - 生产环境中此接口由微信服务器 POST 到 notify_url，不对外暴露。
    """
    user = get_current_user(authorization)

    with get_conn() as conn:
        order = conn.execute(
            "SELECT * FROM recharge_orders WHERE id = ? AND user_id = ?",
            (order_id, user["userId"]),
        ).fetchone()
        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")
        if order["status"] == "paid":
            # 幂等：已支付直接返回当前配额
            quota = get_user_quota(conn, user["userId"])
            return ApiEnvelope(code=0, data=quota, message="已支付")
        if order["status"] != "pending":
            raise HTTPException(status_code=400, detail="订单状态异常")

        quota = apply_user_plan(conn, user["userId"], order["plan_type"])
        conn.execute(
            "UPDATE recharge_orders SET status = 'paid' WHERE id = ?",
            (order_id,),
        )

    log_operation(user["username"], "mock_pay", order_id, f"模拟支付成功: {order['plan_type']}")
    return ApiEnvelope(code=0, data=quota, message="支付成功，套餐已生效")


@app.get("/api/auth/recharge-orders/{order_id}", response_model=ApiEnvelope)
def get_recharge_order(
    order_id: str,
    authorization: str | None = Header(default=None),
) -> ApiEnvelope:
    """查询订单状态（前端轮询用）。返回订单的 status 和套餐信息。"""
    user = get_current_user(authorization)

    with get_conn() as conn:
        order = conn.execute(
            "SELECT * FROM recharge_orders WHERE id = ? AND user_id = ?",
            (order_id, user["userId"]),
        ).fetchone()
        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")
        quota = get_user_quota(conn, user["userId"]) if order["status"] == "paid" else None

    return ApiEnvelope(
        code=0,
        data={
            "orderId": order["id"],
            "planType": order["plan_type"],
            "status": order["status"],
            "createdAt": order["created_at"],
            "quota": quota,
        },
        message="ok",
    )


@app.put("/api/auth/users/{user_id}/plan", response_model=ApiEnvelope)
def update_user_plan(
    user_id: str,
    payload: UserPlanUpdatePayload,
    authorization: str | None = Header(default=None),
) -> ApiEnvelope:
    """管理员直接修改用户套餐类型并立即生效。"""
    user = get_current_user(authorization)
    if not is_admin_user(user):
        raise HTTPException(status_code=403, detail="仅管理员可操作")

    with get_conn() as conn:
        target = conn.execute(
            "SELECT id, username FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if not target:
            raise HTTPException(status_code=404, detail="用户不存在")
        quota = apply_user_plan(conn, user_id, payload.plan_type)

    log_operation(
        user["username"],
        "update_user_plan",
        user_id,
        f"为用户 {target['username']} 设置套餐: {payload.plan_type}",
    )
    return ApiEnvelope(code=0, data=quota, message="套餐更新成功")


@app.get("/api/auth/users/{user_id}/quota", response_model=ApiEnvelope)
def get_user_quota_api(
    user_id: str,
    authorization: str | None = Header(default=None),
) -> ApiEnvelope:
    user = get_current_user(authorization)
    if not is_admin_user(user):
        raise HTTPException(status_code=403, detail="仅管理员可查看")

    with get_conn() as conn:
        row = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="用户不存在")
        quota = get_user_quota(conn, user_id)

    return ApiEnvelope(code=0, data=quota, message="ok")


@app.put("/api/auth/users/{user_id}/quota", response_model=ApiEnvelope)
def update_user_quota(
    user_id: str,
    payload: UserQuotaUpdatePayload,
    authorization: str | None = Header(default=None),
) -> ApiEnvelope:
    user = get_current_user(authorization)
    if not is_admin_user(user):
        raise HTTPException(status_code=403, detail="仅管理员可操作")

    with get_conn() as conn:
        row = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="用户不存在")

        existing = conn.execute(
            "SELECT user_id FROM user_page_quota WHERE user_id = ?", (user_id,)
        ).fetchone()

        if existing:
            conn.execute(
                """
                UPDATE user_page_quota
                SET max_pages = ?, start_date = ?, end_date = ?
                WHERE user_id = ?
                """,
                (payload.max_pages, payload.start_date, payload.end_date, user_id),
            )
        else:
            conn.execute(
                """
                INSERT INTO user_page_quota (user_id, plan_type, max_pages, start_date, end_date)
                VALUES (?, 'free', ?, ?, ?)
                """,
                (
                    user_id,
                    payload.max_pages,
                    payload.start_date or today_str(),
                    payload.end_date,
                ),
            )

    log_operation(user["username"], "update_quota", user_id, f"配额更新: maxPages={payload.max_pages}")
    return ApiEnvelope(
        code=0,
        data={
            "maxPages": payload.max_pages,
            "startDate": payload.start_date,
            "endDate": payload.end_date,
        },
        message="配额更新成功",
    )


@app.put("/api/auth/users/{user_id}/password", response_model=ApiEnvelope)
def update_user_password(
    user_id: str,
    payload: UserPasswordUpdatePayload,
    authorization: str | None = Header(default=None),
) -> ApiEnvelope:
    user = get_current_user(authorization)
    if not is_admin_user(user):
        raise HTTPException(status_code=403, detail="仅管理员可操作")

    with get_conn() as conn:
        row = conn.execute("SELECT id, username FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="用户不存在")

        conn.execute(
            "UPDATE users SET password = ? WHERE id = ?",
            (hash_password(payload.password), user_id),  # 哈希存储
        )

        # 修改密码后强制该用户所有历史 token 失效
        bump_user_token_version(row["username"])

    log_operation(user["username"], "update_password", user_id, "管理员修改用户密码")
    return ApiEnvelope(code=0, data=True, message="密码修改成功")


@app.post("/api/auth/users/{user_id}/force-logout", response_model=ApiEnvelope)
def force_logout_user(
    user_id: str,
    authorization: str | None = Header(default=None),
) -> ApiEnvelope:
    """管理员强制指定用户下线（JWT 版本号递增）。"""
    operator = get_current_user(authorization)
    if not is_admin_user(operator):
        raise HTTPException(status_code=403, detail="仅管理员可操作")

    with get_conn() as conn:
        row = conn.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="用户不存在")
        bump_user_token_version(row["username"])

    log_operation(operator["username"], "force_logout", user_id, f"强制下线用户: {row['username']}")
    return ApiEnvelope(code=0, data=True, message="已强制下线")


@app.delete("/api/auth/users/{user_id}", response_model=ApiEnvelope)
def delete_user(user_id: str, authorization: str | None = Header(default=None)) -> ApiEnvelope:
    """管理员删除指定用户（软删除，进入回收站）。不允许删除当前登录账号。"""
    user = get_current_user(authorization)
    if not is_admin_user(user):
        raise HTTPException(status_code=403, detail="仅管理员可操作")

    if user_id == user["userId"]:
        raise HTTPException(status_code=400, detail="不能删除当前登录账号")

    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="用户不存在")

        trash_put(conn, "user", user_id, dict(row), user["username"])
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))

    log_operation(user["username"], "delete_user", user_id, f"删除用户: {row['username']}")
    return ApiEnvelope(code=0, data=True, message="删除成功")


@app.get("/api/auth/users/{user_id}/pages", response_model=ApiEnvelope)
def list_user_pages(
    user_id: str,
    authorization: str | None = Header(default=None),
) -> ApiEnvelope:
    """管理员查看某用户的所有页面（含 draft/published）。"""
    operator = get_current_user(authorization)
    if not is_admin_user(operator):
        raise HTTPException(status_code=403, detail="仅管理员可查看")

    with get_conn() as conn:
        user_row = conn.execute(
            "SELECT username FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if not user_row:
            raise HTTPException(status_code=404, detail="用户不存在")

        rows = conn.execute(
            "SELECT id, site_name, bind_domain, status, created_at FROM site_pages "
            "WHERE owner_username = ? ORDER BY created_at DESC",
            (user_row["username"],),
        ).fetchall()

    return ApiEnvelope(
        code=0,
        data=[
            {
                "id": r["id"],
                "siteName": r["site_name"],
                "bindDomain": r["bind_domain"],
                "status": r["status"],
                "createdAt": r["created_at"],
            }
            for r in rows
        ],
        message="ok",
    )


@app.put("/api/auth/pages/{page_id}/status", response_model=ApiEnvelope)
def set_page_status(
    page_id: str,
    authorization: str | None = Header(default=None),
) -> ApiEnvelope:
    """管理员切换页面展示状态：published <-> draft。"""
    operator = get_current_user(authorization)
    if not is_admin_user(operator):
        raise HTTPException(status_code=403, detail="仅管理员可操作")

    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, status FROM site_pages WHERE id = ?", (page_id,)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="页面不存在")

        new_status = "draft" if row["status"] == "published" else "published"
        conn.execute(
            "UPDATE site_pages SET status = ?, updated_at = ? WHERE id = ?",
            (new_status, now_iso(), page_id),
        )

    log_operation(operator["username"], "toggle_page_status", page_id, f"页面状态切换为: {new_status}")
    return ApiEnvelope(code=0, data={"status": new_status}, message="ok")


@app.post("/api/auth/refresh", response_model=ApiEnvelope)
def auth_refresh(authorization: str | None = Header(default=None)) -> ApiEnvelope:
    """刷新 accessToken（旧 token 可过期 24h 内刷新）。"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录或Token无效")

    token = authorization.removeprefix("Bearer ").strip()
    if is_token_blacklisted(token):
        raise HTTPException(status_code=401, detail="Token 已失效")

    import base64

    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("格式错误")
        header_b, body_b, sig_b = parts
        expected_sig = hmac.new(JWT_SECRET.encode(), f"{header_b}.{body_b}".encode(), hashlib.sha256).digest()
        actual_sig = base64.urlsafe_b64decode(sig_b + "==")
        if not hmac.compare_digest(expected_sig, actual_sig):
            raise HTTPException(status_code=401, detail="Token 签名无效")

        pad = lambda s: s + "=" * (-len(s) % 4)
        payload = json.loads(base64.urlsafe_b64decode(pad(body_b)).decode())
        if payload.get("exp") and time.time() > payload["exp"] + 86400:
            raise HTTPException(status_code=401, detail="Token 已过期，请重新登录")

        username = payload.get("sub")
        if not username or not get_user_by_username(username):
            raise HTTPException(status_code=401, detail="用户不存在")

        # 刷新前校验 token 版本（被强制下线后不可刷新）
        token_ver = int(payload.get("ver", 1))
        if token_ver != get_user_token_version(username):
            raise HTTPException(status_code=401, detail="Token 已被强制下线")
    except (ValueError, Exception) as e:
        raise HTTPException(status_code=401, detail=f"Token 无效：{e}")

    # 旧 token 入黑名单，防止被复用
    blacklist_token(token, payload.get("exp"))
    new_token = create_access_token(username)
    return ApiEnvelope(code=0, data=new_token, message="ok")


@app.post("/api/auth/logout", response_model=ApiEnvelope)
def auth_logout(authorization: str | None = Header(default=None)) -> ApiEnvelope:
    """退出登录：将当前 token 拉黑，支持服务端即时失效。"""
    if authorization and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ").strip()
        try:
            payload = jwt_decode(token)
            blacklist_token(token, payload.get("exp"))
        except Exception:
            pass
    return ApiEnvelope(code=0, data=True, message="ok")


@app.get("/api/auth/codes", response_model=ApiEnvelope)
def auth_codes() -> ApiEnvelope:
    """获取当前用户权限码列表（mock 实现，返回 ['*:*:*'] 表示全部权限，用于前端按钮级权限控制）。"""
    return ApiEnvelope(code=0, data=["*:*:*"], message="ok")


# ==================== 忘记密码（用密钥重置）====================


@app.post("/api/auth/reset-password", response_model=ApiEnvelope)
def reset_password(payload: ResetPasswordPayload) -> ApiEnvelope:
    """用户凭账号+注册密钥重置密码（无需登录）。"""
    if payload.new_password != payload.confirm_password:
        return ApiEnvelope(code=10010, data=None, message="两次密码输入不一致")

    username = payload.username.strip()
    with get_conn() as conn:
        user_row = conn.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()
        if not user_row:
            return ApiEnvelope(code=10011, data=None, message="用户名不存在")

        key_row = conn.execute(
            "SELECT * FROM register_keys WHERE register_key = ?",
            (payload.register_key.strip(),),
        ).fetchone()
        if not key_row:
            return ApiEnvelope(code=10012, data=None, message="密钥不存在")
        if not key_row["used_by"] or key_row["used_by"] != username:
            return ApiEnvelope(code=10013, data=None, message="该密钥与账号不匹配")

        # 检查密钥有效期
        expires_at = key_row["expires_at"]
        if expires_at and now_iso() > expires_at:
            return ApiEnvelope(code=10014, data=None, message="密钥已过期")

        conn.execute(
            "UPDATE users SET password = ? WHERE id = ?",
            (hash_password(payload.new_password), user_row["id"]),
        )

    log_operation(username, "reset_password", username, "通过密钥重置密码")
    return ApiEnvelope(code=0, data=True, message="密码重置成功")


# ==================== 密钥列表管理 ====================


@app.get("/api/auth/register-keys", response_model=ApiEnvelope)
def list_register_keys(
    authorization: str | None = Header(default=None),
    role: str | None = Query(default=None),
    used: str | None = Query(default=None),  # "yes" / "no"
    keyword: str | None = Query(default=None),
) -> ApiEnvelope:
    """管理员查看所有密钥列表，支持筛选。"""
    user = get_current_user(authorization)
    if not is_admin_user(user):
        raise HTTPException(status_code=403, detail="仅管理员可查看")

    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM register_keys ORDER BY created_at DESC"
        ).fetchall()

    result = []
    now = now_iso()
    for r in rows:
        item = {
            "id": r["id"],
            "registerKey": r["register_key"],
            "role": r["role"],
            "createdBy": r["created_by"],
            "usedBy": r["used_by"],
            "usedAt": r["used_at"],
            "createdAt": r["created_at"],
            "expiresAt": r["expires_at"],
            "expired": bool(r["expires_at"] and now > r["expires_at"]),
        }
        # 筛选
        if role and item["role"] != role:
            continue
        if used == "yes" and not item["usedBy"]:
            continue
        if used == "no" and item["usedBy"]:
            continue
        if keyword and keyword.lower() not in (item["registerKey"] + (item["usedBy"] or "")).lower():
            continue
        result.append(item)

    return ApiEnvelope(code=0, data=result, message="ok")


@app.delete("/api/auth/register-keys/{key_id}", response_model=ApiEnvelope)
def delete_register_key(
    key_id: str,
    authorization: str | None = Header(default=None),
) -> ApiEnvelope:
    """管理员删除密钥（软删除，进入回收站）。"""
    user = get_current_user(authorization)
    if not is_admin_user(user):
        raise HTTPException(status_code=403, detail="仅管理员可操作")

    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM register_keys WHERE id = ?", (key_id,)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="密钥不存在")
        trash_put(conn, "key", key_id, dict(row), user["username"])
        conn.execute("DELETE FROM register_keys WHERE id = ?", (key_id,))

    log_operation(user["username"], "delete_key", row["register_key"], f"删除密钥（已使用: {bool(row['used_by'])}）")
    return ApiEnvelope(code=0, data=True, message="删除成功")


@app.put("/api/auth/register-keys/{key_id}/expires", response_model=ApiEnvelope)
def update_key_expires(
    key_id: str,
    payload: RegisterKeyUpdatePayload,
    authorization: str | None = Header(default=None),
) -> ApiEnvelope:
    """管理员修改密钥有效期（None 表示永不过期）。"""
    user = get_current_user(authorization)
    if not is_admin_user(user):
        raise HTTPException(status_code=403, detail="仅管理员可操作")

    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, register_key FROM register_keys WHERE id = ?", (key_id,)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="密钥不存在")
        conn.execute(
            "UPDATE register_keys SET expires_at = ? WHERE id = ?",
            (payload.expires_at, key_id),
        )

    log_operation(user["username"], "update_key_expires", row["register_key"], f"有效期设置为: {payload.expires_at or '永久'}")
    return ApiEnvelope(code=0, data={"expiresAt": payload.expires_at}, message="有效期已更新")


# ==================== 操作日志 ====================


@app.get("/api/auth/logs", response_model=ApiEnvelope)
def get_operation_logs(
    authorization: str | None = Header(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    operator: str | None = Query(default=None),
    action: str | None = Query(default=None),
) -> ApiEnvelope:
    """管理员查看操作日志。"""
    user = get_current_user(authorization)
    if not is_admin_user(user):
        raise HTTPException(status_code=403, detail="仅管理员可查看")

    # 使用参数化与白名单拼接，避免 SQL 注入
    where_sql = ""
    where_params: list[Any] = []
    if operator and action:
        where_sql = " WHERE operator LIKE ? AND action = ?"
        where_params = [f"%{operator}%", action]
    elif operator:
        where_sql = " WHERE operator LIKE ?"
        where_params = [f"%{operator}%"]
    elif action:
        where_sql = " WHERE action = ?"
        where_params = [action]

    with get_conn() as conn:
        total = conn.execute(
            f"SELECT COUNT(1) AS c FROM operation_logs{where_sql}",
            where_params,
        ).fetchone()["c"]
        rows = conn.execute(
            f"SELECT * FROM operation_logs{where_sql} ORDER BY created_at DESC LIMIT ? OFFSET ?",
            where_params + [page_size, (page - 1) * page_size],
        ).fetchall()

    return ApiEnvelope(
        code=0,
        data={
            "total": total,
            "page": page,
            "pageSize": page_size,
            "list": [
                {
                    "id": r["id"],
                    "operator": r["operator"],
                    "action": r["action"],
                    "target": r["target"],
                    "detail": r["detail"],
                    "createdAt": r["created_at"],
                }
                for r in rows
            ],
        },
        message="ok",
    )


# ==================== 用户搜索/筛选 ====================


@app.get("/api/auth/users", response_model=ApiEnvelope)
def list_users(
    authorization: str | None = Header(default=None),
    keyword: str | None = Query(default=None),
    role: str | None = Query(default=None),
) -> ApiEnvelope:
    """管理员获取用户列表，支持按关键词（用户名/姓名）和角色筛选。
    返回每个用户的页面数量和配额信息。
    """
    user = get_current_user(authorization)
    if not is_admin_user(user):
        raise HTTPException(status_code=403, detail="仅管理员可查看")

    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, username, real_name, roles, created_at FROM users ORDER BY created_at DESC"
        ).fetchall()

        result = []
        for row in rows:
            # 关键字筛选
            if keyword and keyword.lower() not in (row["username"] + row["real_name"]).lower():
                continue
            # 角色筛选
            if role and role not in parse_roles(row["roles"]):
                continue
            uid = row["id"]
            page_count = conn.execute(
                "SELECT COUNT(1) AS c FROM site_pages WHERE owner_username = ?",
                (row["username"],),
            ).fetchone()["c"]
            quota = get_user_quota(conn, uid)
            item = row_to_user_admin(row)
            item["pageCount"] = page_count
            item["quota"] = quota
            result.append(item)

    return ApiEnvelope(code=0, data=result, message="ok")


# ==================== 批量删除用户 ====================


class BatchDeleteUsersPayload(BaseModel):
    user_ids: list[str]


@app.post("/api/auth/users/batch-delete", response_model=ApiEnvelope)
def batch_delete_users(
    payload: BatchDeleteUsersPayload,
    authorization: str | None = Header(default=None),
) -> ApiEnvelope:
    """管理员批量删除用户（软删除，进入回收站）。"""
    user = get_current_user(authorization)
    if not is_admin_user(user):
        raise HTTPException(status_code=403, detail="仅管理员可操作")

    deleted = []
    skipped = []
    with get_conn() as conn:
        for uid in payload.user_ids:
            if uid == user["userId"]:
                skipped.append(uid)
                continue
            row = conn.execute("SELECT * FROM users WHERE id = ?", (uid,)).fetchone()
            if not row:
                skipped.append(uid)
                continue
            trash_put(conn, "user", uid, dict(row), user["username"])
            conn.execute("DELETE FROM users WHERE id = ?", (uid,))
            deleted.append(row["username"])

    if deleted:
        log_operation(user["username"], "batch_delete_users", ",".join(deleted), f"批量删除 {len(deleted)} 个用户")

    return ApiEnvelope(
        code=0,
        data={"deleted": deleted, "skipped": skipped},
        message=f"成功删除 {len(deleted)} 个用户",
    )


# ==================== 回收站接口 ====================


@app.get("/api/auth/trash", response_model=ApiEnvelope)
def list_trash(
    authorization: str | None = Header(default=None),
    item_type: str | None = Query(default=None),
) -> ApiEnvelope:
    """管理员查看回收站列表（仅含未过期条目）。"""
    user = get_current_user(authorization)
    if not is_admin_user(user):
        raise HTTPException(status_code=403, detail="仅管理员可查看")

    with get_conn() as conn:
        trash_cleanup(conn)
        if item_type:
            rows = conn.execute(
                "SELECT * FROM trash WHERE item_type = ? ORDER BY deleted_at DESC",
                (item_type,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM trash ORDER BY deleted_at DESC"
            ).fetchall()

    return ApiEnvelope(
        code=0,
        data=[
            {
                "id": r["id"],
                "itemType": r["item_type"],
                "itemId": r["item_id"],
                "itemData": json.loads(r["item_data"]),
                "deletedBy": r["deleted_by"],
                "deletedAt": r["deleted_at"],
                "expireAt": r["expire_at"],
            }
            for r in rows
        ],
        message="ok",
    )


@app.post("/api/auth/trash/{trash_id}/restore", response_model=ApiEnvelope)
def restore_trash(
    trash_id: str,
    authorization: str | None = Header(default=None),
) -> ApiEnvelope:
    """从回收站恢复对象。"""
    user = get_current_user(authorization)
    if not is_admin_user(user):
        raise HTTPException(status_code=403, detail="仅管理员可操作")

    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM trash WHERE id = ?", (trash_id,)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="回收站条目不存在或已过期")

        if now_iso() > row["expire_at"]:
            conn.execute("DELETE FROM trash WHERE id = ?", (trash_id,))
            raise HTTPException(status_code=410, detail="该条目已超过30天保留期，无法恢复")

        item_type = row["item_type"]
        data = json.loads(row["item_data"])

        if item_type == "user":
            # 检查用户名是否冲突
            conflict = conn.execute(
                "SELECT id FROM users WHERE username = ?", (data["username"],)
            ).fetchone()
            if conflict:
                raise HTTPException(status_code=409, detail=f"用户名 {data['username']} 已存在，无法恢复")
            conn.execute(
                """
                INSERT INTO users (id, username, password, real_name, avatar, user_desc, home_path, roles, created_at)
                VALUES (:id, :username, :password, :real_name, :avatar, :user_desc, :home_path, :roles, :created_at)
                """,
                data,
            )

        elif item_type == "page":
            conflict_path = conn.execute(
                "SELECT id FROM site_pages WHERE site_path = ?", (data["site_path"],)
            ).fetchone()
            conflict_domain = conn.execute(
                "SELECT id FROM site_pages WHERE bind_domain = ?", (data["bind_domain"],)
            ).fetchone()
            if conflict_path:
                raise HTTPException(status_code=409, detail=f"路径 {data['site_path']} 已被占用，无法恢复")
            if conflict_domain:
                raise HTTPException(status_code=409, detail=f"域名 {data['bind_domain']} 已被占用，无法恢复")
            conn.execute(
                """
                INSERT INTO site_pages
                (id, owner_username, site_path, bind_domain, site_name, site_description,
                 template_id, nav_items, colors, fonts, status, created_at, updated_at)
                VALUES (:id, :owner_username, :site_path, :bind_domain, :site_name, :site_description,
                        :template_id, :nav_items, :colors, :fonts, :status, :created_at, :updated_at)
                """,
                data,
            )

        elif item_type == "key":
            conflict = conn.execute(
                "SELECT id FROM register_keys WHERE register_key = ?", (data["register_key"],)
            ).fetchone()
            if conflict:
                raise HTTPException(status_code=409, detail="密钥已存在，无法恢复")
            conn.execute(
                """
                INSERT INTO register_keys
                (id, register_key, role, created_by, used_by, used_at, created_at, expires_at)
                VALUES (:id, :register_key, :role, :created_by, :used_by, :used_at, :created_at, :expires_at)
                """,
                data,
            )

        conn.execute("DELETE FROM trash WHERE id = ?", (trash_id,))

    log_operation(user["username"], "restore_trash", row["item_id"], f"从回收站恢复 {item_type}: {row['item_id']}")
    return ApiEnvelope(code=0, data=True, message="恢复成功")


@app.delete("/api/auth/trash/{trash_id}", response_model=ApiEnvelope)
def purge_trash(
    trash_id: str,
    authorization: str | None = Header(default=None),
) -> ApiEnvelope:
    """彻底删除回收站条目（不可恢复）。"""
    user = get_current_user(authorization)
    if not is_admin_user(user):
        raise HTTPException(status_code=403, detail="仅管理员可操作")

    with get_conn() as conn:
        row = conn.execute("SELECT id, item_type, item_id FROM trash WHERE id = ?", (trash_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="回收站条目不存在")
        conn.execute("DELETE FROM trash WHERE id = ?", (trash_id,))

    log_operation(user["username"], "purge_trash", row["item_id"], f"彻底删除 {row['item_type']}: {row['item_id']}")
    return ApiEnvelope(code=0, data=True, message="已彻底删除")


@app.delete("/api/auth/trash", response_model=ApiEnvelope)
def clear_trash(
    authorization: str | None = Header(default=None),
) -> ApiEnvelope:
    """清空整个回收站（彻底删除所有条目）。"""
    user = get_current_user(authorization)
    if not is_admin_user(user):
        raise HTTPException(status_code=403, detail="仅管理员可操作")

    with get_conn() as conn:
        count = conn.execute("SELECT COUNT(1) AS c FROM trash").fetchone()["c"]
        conn.execute("DELETE FROM trash")

    log_operation(user["username"], "clear_trash", "", f"清空回收站，共 {count} 条")
    return ApiEnvelope(code=0, data={"cleared": count}, message=f"已清空 {count} 条回收站记录")


# ==================== 域名绑定验证 ====================


@app.get("/api/public/verify-domain", response_model=ApiEnvelope)
def verify_domain(domain: str = Query(...)) -> ApiEnvelope:
    """公开接口：验证域名是否可解析及是否已被占用。
    - 先检查域名是否已被其他页面绑定（冲突返回 409）。
    - 再通过 socket.gethostbyname 检测 DNS 解析是否成功。
    - 无需登录，供前端填写域名时实时校验使用。
    """
    import socket
    try:
        normalized = normalize_domain(domain)
    except HTTPException as e:
        return ApiEnvelope(code=400, data=None, message=str(e.detail))

    # 检查该域名是否已被其他页面绑定
    with get_conn() as conn:
        existing = conn.execute(
            "SELECT site_name, owner_username FROM site_pages WHERE bind_domain = ?",
            (normalized,),
        ).fetchone()
        if existing:
            return ApiEnvelope(
                code=409,
                data={"conflict": True, "siteName": existing["site_name"]},
                message=f"域名已被 {existing['owner_username']} 的页面占用",
            )

    # 尝试 DNS 解析（检查域名是否可解析）
    try:
        addr = socket.gethostbyname(normalized)
        return ApiEnvelope(
            code=0,
            data={"domain": normalized, "resolvedIp": addr, "resolvable": True},
            message="域名可正常解析",
        )
    except socket.gaierror:
        return ApiEnvelope(
            code=0,
            data={"domain": normalized, "resolvedIp": None, "resolvable": False},
            message="域名暂时无法解析，请检查 DNS 配置后重试",
        )


@app.get("/api/user/info", response_model=ApiEnvelope)
def user_info(authorization: str | None = Header(default=None)) -> ApiEnvelope:
    user = get_current_user(authorization)
    user_data = {k: v for k, v in user.items() if k != "password"}

    with get_conn() as conn:
        quota = get_user_quota(conn, user["userId"])
        page_count = conn.execute(
            "SELECT COUNT(1) AS c FROM site_pages WHERE owner_username = ?",
            (user["username"],),
        ).fetchone()["c"]

    return ApiEnvelope(
        code=0,
        data={
            **user_data,
            "pageQuota": quota,
            "pageCount": page_count,
        },
        message="ok",
    )


@app.get("/api/menu/all", response_model=ApiEnvelope)
def menu_all(authorization: str | None = Header(default=None)) -> ApiEnvelope:
    user = get_current_user(authorization)
    menus = [
        {
            "name": "Dashboard",
            "path": "/dashboard",
            "meta": {
                "title": "仪表盘",
                "icon": "lucide:layout-dashboard",
                "order": -1,
            },
            "children": [
                {
                    "name": "Analytics",
                    "path": "/analytics",
                    "component": "/dashboard/analytics/index",
                    "meta": {
                        "title": "分析页",
                        "icon": "lucide:area-chart",
                        "affixTab": True,
                    },
                },
                {
                    "name": "Workspace",
                    "path": "/workspace",
                    "component": "/dashboard/workspace/index",
                    "meta": {
                        "title": "工作台",
                        "icon": "carbon:workspace",
                    },
                },
            ],
        }
    ]

    if is_admin_user(user):
        menus[0]["children"].extend(
            [
                {
                    "name": "RegisterKeys",
                    "path": "/register-keys",
                    "component": "/dashboard/register-keys/index",
                    "meta": {
                        "title": "生成密钥",
                        "icon": "lucide:key-round",
                    },
                },
                {
                    "name": "RegisterStats",
                    "path": "/register-stats",
                    "component": "/dashboard/register-stats/index",
                    "meta": {
                        "title": "注册统计",
                        "icon": "lucide:chart-column-big",
                    },
                },
                {
                    "name": "PlanManage",
                    "path": "/plan-manage",
                    "component": "/dashboard/plan-manage/index",
                    "meta": {
                        "title": "套餐管理",
                        "icon": "lucide:wallet-cards",
                    },
                },
                {
                    "name": "Trash",
                    "path": "/trash",
                    "component": "/dashboard/trash/index",
                    "meta": {
                        "title": "回收站",
                        "icon": "lucide:trash-2",
                    },
                },
            ]
        )
    else:
        menus[0]["children"].append(
            {
                "name": "Recharge",
                "path": "/recharge",
                "component": "/dashboard/recharge/index",
                "meta": {
                    "title": "充值中心",
                    "icon": "lucide:coins",
                },
            }
        )

    return ApiEnvelope(code=0, data=menus, message="ok")


if __name__ == "__main__":
    import uvicorn

    host = os.environ.get("API_BIND_HOST", "0.0.0.0")
    port = int(os.environ.get("API_PORT", "5322"))

    uvicorn.run("main:app", host=host, port=port, reload=not IS_PROD)
