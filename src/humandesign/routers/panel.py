"""
Admin Panel — built-in web UI for Astro Gates.

Routes:
    /panel/login        — login page (POST accepts HD_ADMIN_TOKEN)
    /panel/dashboard    — metrics & charts
    /panel/sites        — CRUD sites with tokens
    /panel/calculator   — test HD calculation form
    /panel/logs         — live request log viewer
    /panel/logout       — destroy session

Internal JSON API (used by HTMX / fetch):
    /panel/api/sites           — POST create, GET list
    /panel/api/sites/{id}      — PUT update, DELETE remove
    /panel/api/logs            — GET filtered logs
"""
import json
import secrets
import os
from typing import Optional

from fastapi import APIRouter, Request, HTTPException, Response, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from ..auth import (
    ADMIN_TOKEN, _get_db, add_site, get_all_sites, update_site,
    delete_site, get_stats, set_admin_token, env_path as _env_path
)
from .. import auth as _auth_module
from ..utils.version import get_version

router = APIRouter()

# Templates
_templates_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
templates = Jinja2Templates(directory=_templates_dir)

# Simple in-memory session store  {session_token: True}
_sessions: dict[str, bool] = {}


# ============================================================
# Session helpers
# ============================================================

def _create_session(response: Response) -> str:
    token = secrets.token_urlsafe(32)
    _sessions[token] = True
    response.set_cookie(
        "panel_session", token,
        httponly=True, samesite="lax", max_age=86400  # 24h
    )
    return token


def _check_session(request: Request) -> bool:
    token = request.cookies.get("panel_session")
    return bool(token and _sessions.get(token))


def _require_session(request: Request):
    if not _check_session(request):
        raise HTTPException(status_code=302, headers={"Location": "/panel/login"})


# ============================================================
# Auth pages
# ============================================================

@router.get("/panel/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if _check_session(request):
        return RedirectResponse("/panel/dashboard", status_code=302)
    return templates.TemplateResponse("panel/login.html", {"request": request, "error": None})


@router.post("/panel/login", response_class=HTMLResponse)
async def login_submit(request: Request, token: str = Form(...)):
    if not _auth_module.ADMIN_TOKEN:
        return templates.TemplateResponse("panel/login.html", {
            "request": request,
            "error": "HD_ADMIN_TOKEN не настроен в .env"
        })
    if token != _auth_module.ADMIN_TOKEN:
        return templates.TemplateResponse("panel/login.html", {
            "request": request,
            "error": "Неверный токен"
        })
    response = RedirectResponse("/panel/dashboard", status_code=302)
    _create_session(response)
    return response


@router.get("/panel/logout")
async def logout(request: Request):
    token = request.cookies.get("panel_session")
    if token:
        _sessions.pop(token, None)
    response = RedirectResponse("/panel/login", status_code=302)
    response.delete_cookie("panel_session")
    return response


# ============================================================
# Dashboard
# ============================================================

@router.get("/panel/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, days: int = Query(30, ge=1, le=365)):
    _require_session(request)
    
    stats = get_stats(days=days)
    
    # Compute aggregates
    total_requests = sum(s.get("total_requests", 0) or 0 for s in stats["sites"])
    total_success = sum(s.get("success", 0) or 0 for s in stats["sites"])
    total_errors = sum(s.get("errors", 0) or 0 for s in stats["sites"])
    
    # Active sites count
    all_sites = get_all_sites()
    active_sites = sum(1 for s in all_sites if s.get("is_active", 0))
    
    success_rate = round(total_success / total_requests * 100, 1) if total_requests > 0 else 0
    
    avg_times = [s.get("avg_response_ms") for s in stats["sites"] if s.get("avg_response_ms")]
    avg_response_ms = round(sum(avg_times) / len(avg_times), 1) if avg_times else 0
    
    # Reverse daily for chronological order
    daily = list(reversed(stats.get("daily", [])))
    
    return templates.TemplateResponse("panel/dashboard.html", {
        "request": request,
        "active_page": "dashboard",
        "version": get_version(),
        "stats": stats,
        "total_requests": total_requests,
        "active_sites": active_sites,
        "total_sites": len(all_sites),
        "success_rate": success_rate,
        "avg_response_ms": avg_response_ms,
        "daily_json": json.dumps(daily),
        "endpoint_json": json.dumps(stats.get("endpoints", [])),
    })


# ============================================================
# Sites
# ============================================================

@router.get("/panel/sites", response_class=HTMLResponse)
async def sites_page(request: Request):
    _require_session(request)
    
    # Get sites WITH tokens for the panel
    conn = _get_db()
    rows = conn.execute(
        "SELECT id, domain, token, is_active, created_at FROM sites ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    sites = [dict(r) for r in rows]
    
    return templates.TemplateResponse("panel/sites.html", {
        "request": request,
        "active_page": "sites",
        "version": get_version(),
        "sites": sites,
    })


# ============================================================
# Test Calculator
# ============================================================

@router.get("/panel/calculator", response_class=HTMLResponse)
async def calculator_page(request: Request):
    _require_session(request)
    
    # Get sites with tokens for the dropdown
    conn = _get_db()
    rows = conn.execute(
        "SELECT id, domain, token FROM sites WHERE is_active = 1 ORDER BY domain"
    ).fetchall()
    conn.close()
    sites = [dict(r) for r in rows]
    
    return templates.TemplateResponse("panel/calculator.html", {
        "request": request,
        "active_page": "calculator",
        "version": get_version(),
        "sites": sites,
    })


# ============================================================
# Live Logs
# ============================================================

@router.get("/panel/logs", response_class=HTMLResponse)
async def logs_page(request: Request):
    _require_session(request)
    
    sites = get_all_sites()
    
    return templates.TemplateResponse("panel/logs.html", {
        "request": request,
        "active_page": "logs",
        "version": get_version(),
        "sites": sites,
    })


# ============================================================
# Internal JSON API (for HTMX / fetch calls from panel pages)
# ============================================================

@router.post("/panel/api/sites")
async def api_create_site(request: Request):
    _require_session(request)
    body = await request.json()
    try:
        site = add_site(body["domain"], body.get("token"))
        return {
            "status": "created",
            "site": {
                "id": site["id"],
                "domain": site["domain"],
                "token": site["token"],
                "is_active": bool(site["is_active"]),
                "created_at": site["created_at"],
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put("/panel/api/sites/{site_id}")
async def api_update_site(request: Request, site_id: int):
    _require_session(request)
    body = await request.json()
    try:
        site = update_site(
            site_id,
            domain=body.get("domain"),
            token=body.get("token"),
            is_active=body.get("is_active"),
        )
        return {"status": "updated", "site": dict(site) if hasattr(site, '__getitem__') else site}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/panel/api/sites/{site_id}")
async def api_delete_site(request: Request, site_id: int):
    _require_session(request)
    if delete_site(site_id):
        return {"status": "deleted", "site_id": site_id}
    raise HTTPException(status_code=404, detail=f"Site id={site_id} not found")


@router.get("/panel/api/logs")
async def api_get_logs(
    request: Request,
    site_id: Optional[int] = Query(None),
    endpoint: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
):
    _require_session(request)
    
    conn = _get_db()
    
    where_clauses = []
    params = []
    
    if site_id:
        where_clauses.append("r.site_id = ?")
        params.append(site_id)
    if endpoint:
        where_clauses.append("r.endpoint LIKE ?")
        params.append(f"%{endpoint}%")
    if status == "200":
        where_clauses.append("r.status_code = 200")
    elif status == "error":
        where_clauses.append("r.status_code != 200")
    
    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
    
    rows = conn.execute(f"""
        SELECT r.id, r.site_id, s.domain, r.endpoint, r.method,
               r.status_code, r.response_time_ms, r.created_at
        FROM request_log r
        LEFT JOIN sites s ON r.site_id = s.id
        {where_sql}
        ORDER BY r.created_at DESC
        LIMIT ?
    """, params + [limit]).fetchall()
    
    conn.close()
    
    return {"logs": [dict(r) for r in rows]}


# ============================================================
# Settings
# ============================================================

@router.get("/panel/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    _require_session(request)
    
    current_token = _auth_module.ADMIN_TOKEN or ""
    token_masked = current_token[:6] + "••••••••••••" if len(current_token) > 6 else "••••••"
    
    return templates.TemplateResponse("panel/settings.html", {
        "request": request,
        "active_page": "settings",
        "version": get_version(),
        "token_masked": token_masked,
        "token_full": current_token,
        "token_length": len(current_token),
        "env_path": os.path.abspath(_env_path),
    })


@router.put("/panel/api/settings/token")
async def api_change_token(request: Request):
    _require_session(request)
    body = await request.json()
    
    current_token = body.get("current_token", "")
    new_token = body.get("new_token", "")
    
    if not new_token or len(new_token) < 8:
        raise HTTPException(status_code=400, detail="Новый токен должен быть не менее 8 символов")
    
    if current_token != _auth_module.ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Неверный текущий токен")
    
    if new_token == _auth_module.ADMIN_TOKEN:
        raise HTTPException(status_code=400, detail="Новый токен совпадает с текущим")
    
    try:
        set_admin_token(new_token)
        return {"status": "updated", "token_length": len(new_token)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка записи: {str(e)}")


# ============================================================
# Redirect /panel → /panel/dashboard
# ============================================================

@router.get("/panel")
async def panel_root():
    return RedirectResponse("/panel/dashboard", status_code=302)
