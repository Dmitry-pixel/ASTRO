"""
Multi-site authentication and request logging.

Sites are stored in SQLite (api_auth.db):
  - sites: domain, token, is_active, created_at
  - request_log: site_id, endpoint, timestamp, response_time_ms

Admin manages sites via:
  - .env: HD_ADMIN_TOKEN (master admin token)
  - API: POST/GET/DELETE /admin/sites
"""
import os
import sqlite3
import time
import secrets
from datetime import datetime
from typing import Optional
from contextlib import contextmanager

from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv

# --- Load .env ---
# In Docker: .env is mounted at /app/.env
# Without Docker: .env is relative to src/humandesign/../../.env
_this_dir = os.path.dirname(__file__)
env_path = os.environ.get("AG_ENV_PATH", os.path.join(_this_dir, "../../.env"))
load_dotenv(dotenv_path=env_path, override=True)

ADMIN_TOKEN = os.getenv("HD_ADMIN_TOKEN", "")

# Database path: use AG_DATA_DIR env var or default to ../../ (project root)
_data_dir = os.environ.get("AG_DATA_DIR", os.path.join(_this_dir, "../.."))
DB_PATH = os.path.join(_data_dir, "api_auth.db")

security = HTTPBearer()


def set_admin_token(new_token: str):
    """Update HD_ADMIN_TOKEN in memory and persist to .env file."""
    global ADMIN_TOKEN
    ADMIN_TOKEN = new_token
    os.environ["HD_ADMIN_TOKEN"] = new_token

    # Update .env file
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            lines = f.readlines()
        found = False
        for i, line in enumerate(lines):
            if line.strip().startswith("HD_ADMIN_TOKEN"):
                lines[i] = f"HD_ADMIN_TOKEN={new_token}\n"
                found = True
                break
        if not found:
            lines.append(f"\nHD_ADMIN_TOKEN={new_token}\n")
        with open(env_path, "w") as f:
            f.writelines(lines)
    else:
        with open(env_path, "w") as f:
            f.write(f"HD_ADMIN_TOKEN={new_token}\n")


# ============================================================
# Database
# ============================================================

def _get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = _get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT NOT NULL UNIQUE,
            token TEXT NOT NULL UNIQUE,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS request_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER NOT NULL,
            endpoint TEXT NOT NULL,
            method TEXT NOT NULL DEFAULT 'GET',
            status_code INTEGER DEFAULT 200,
            response_time_ms REAL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (site_id) REFERENCES sites(id)
        );
        CREATE INDEX IF NOT EXISTS idx_request_log_site ON request_log(site_id);
        CREATE INDEX IF NOT EXISTS idx_request_log_date ON request_log(created_at);
    """)
    conn.close()


# Initialize on import
init_db()


# ============================================================
# Site CRUD
# ============================================================

def add_site(domain: str, token: Optional[str] = None) -> dict:
    """Add a new site. Auto-generates token if not provided."""
    if not token:
        token = secrets.token_urlsafe(32)
    conn = _get_db()
    try:
        conn.execute(
            "INSERT INTO sites (domain, token) VALUES (?, ?)",
            (domain.lower().strip(), token)
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM sites WHERE domain = ?", (domain.lower().strip(),)
        ).fetchone()
        return dict(row)
    except sqlite3.IntegrityError:
        raise ValueError(f"Site '{domain}' already exists or token is duplicate")
    finally:
        conn.close()


def get_all_sites() -> list:
    """List all registered sites (without tokens)."""
    conn = _get_db()
    try:
        rows = conn.execute(
            "SELECT id, domain, is_active, created_at FROM sites ORDER BY created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_site_by_token(token: str) -> Optional[dict]:
    """Find active site by token."""
    conn = _get_db()
    try:
        row = conn.execute(
            "SELECT * FROM sites WHERE token = ? AND is_active = 1", (token,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def update_site(site_id: int, domain: Optional[str] = None,
                token: Optional[str] = None, is_active: Optional[bool] = None) -> dict:
    """Update site fields."""
    conn = _get_db()
    try:
        updates = []
        params = []
        if domain is not None:
            updates.append("domain = ?")
            params.append(domain.lower().strip())
        if token is not None:
            updates.append("token = ?")
            params.append(token)
        if is_active is not None:
            updates.append("is_active = ?")
            params.append(1 if is_active else 0)
        if not updates:
            raise ValueError("Nothing to update")
        params.append(site_id)
        conn.execute(f"UPDATE sites SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
        row = conn.execute("SELECT * FROM sites WHERE id = ?", (site_id,)).fetchone()
        if not row:
            raise ValueError(f"Site id={site_id} not found")
        return dict(row)
    finally:
        conn.close()


def delete_site(site_id: int) -> bool:
    """Delete site and its logs."""
    conn = _get_db()
    try:
        conn.execute("DELETE FROM request_log WHERE site_id = ?", (site_id,))
        result = conn.execute("DELETE FROM sites WHERE id = ?", (site_id,))
        conn.commit()
        return result.rowcount > 0
    finally:
        conn.close()


# ============================================================
# Request logging
# ============================================================

def log_request(site_id: int, endpoint: str, method: str = "GET",
                status_code: int = 200, response_time_ms: float = 0):
    """Log an API request."""
    conn = _get_db()
    try:
        conn.execute(
            "INSERT INTO request_log (site_id, endpoint, method, status_code, response_time_ms) "
            "VALUES (?, ?, ?, ?, ?)",
            (site_id, endpoint, method, status_code, response_time_ms)
        )
        conn.commit()
    finally:
        conn.close()


def get_stats(site_id: Optional[int] = None, days: int = 30) -> dict:
    """Get request statistics, optionally filtered by site."""
    conn = _get_db()
    try:
        where = "WHERE r.created_at >= datetime('now', ?)"
        params = [f"-{days} days"]
        if site_id:
            where += " AND r.site_id = ?"
            params.append(site_id)

        # Total requests per site
        rows = conn.execute(f"""
            SELECT s.id, s.domain,
                   COUNT(r.id) as total_requests,
                   SUM(CASE WHEN r.status_code = 200 THEN 1 ELSE 0 END) as success,
                   SUM(CASE WHEN r.status_code != 200 THEN 1 ELSE 0 END) as errors,
                   ROUND(AVG(r.response_time_ms), 1) as avg_response_ms
            FROM sites s
            LEFT JOIN request_log r ON s.id = r.site_id AND r.created_at >= datetime('now', ?)
            {"WHERE s.id = ?" if site_id else ""}
            GROUP BY s.id, s.domain
            ORDER BY total_requests DESC
        """, [f"-{days} days", site_id] if site_id else [f"-{days} days"]).fetchall()

        sites_stats = [dict(r) for r in rows]

        # Daily breakdown
        daily_rows = conn.execute(f"""
            SELECT DATE(r.created_at) as date, COUNT(*) as requests
            FROM request_log r
            {where}
            GROUP BY DATE(r.created_at)
            ORDER BY date DESC
            LIMIT 30
        """, params).fetchall()

        # Endpoint breakdown
        endpoint_rows = conn.execute(f"""
            SELECT r.endpoint, COUNT(*) as requests
            FROM request_log r
            {where}
            GROUP BY r.endpoint
            ORDER BY requests DESC
        """, params).fetchall()

        return {
            "period_days": days,
            "sites": sites_stats,
            "daily": [dict(r) for r in daily_rows],
            "endpoints": [dict(r) for r in endpoint_rows]
        }
    finally:
        conn.close()


# ============================================================
# FastAPI dependencies
# ============================================================

def verify_token(request: Request,
                 credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify Bearer token against registered sites. Logs the request."""
    token = credentials.credentials
    site = get_site_by_token(token)
    if not site:
        raise HTTPException(status_code=401, detail="Invalid or inactive API token.")
    # Store site info in request state for logging
    request.state.site_id = site["id"]
    request.state.site_domain = site["domain"]
    return True


def verify_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify admin token from .env (HD_ADMIN_TOKEN)."""
    # Read from module-level var (updated by set_admin_token at runtime)
    current_token = globals().get("ADMIN_TOKEN", "")
    if not current_token:
        raise HTTPException(status_code=503, detail="Admin token not configured. Set HD_ADMIN_TOKEN in .env")
    if credentials.credentials != current_token:
        raise HTTPException(status_code=401, detail="Invalid admin token.")
    return True
