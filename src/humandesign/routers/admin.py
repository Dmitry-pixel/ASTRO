"""
Admin router for managing sites and viewing statistics.
All endpoints require HD_ADMIN_TOKEN.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional

from ..auth import (
    verify_admin, add_site, get_all_sites, update_site,
    delete_site, get_stats
)

router = APIRouter(prefix="/admin", tags=["admin"])


class SiteCreate(BaseModel):
    domain: str = Field(..., min_length=3, description="Domain name (e.g. mysite.com)")
    token: Optional[str] = Field(None, description="Custom token (auto-generated if empty)")


class SiteUpdate(BaseModel):
    domain: Optional[str] = Field(None, description="New domain name")
    token: Optional[str] = Field(None, description="New token")
    is_active: Optional[bool] = Field(None, description="Enable/disable site")


@router.post("/sites")
def create_site(body: SiteCreate, authorized: bool = Depends(verify_admin)):
    """Register a new site with API access."""
    try:
        site = add_site(body.domain, body.token)
        return {
            "status": "created",
            "site": {
                "id": site["id"],
                "domain": site["domain"],
                "token": site["token"],
                "is_active": bool(site["is_active"]),
                "created_at": site["created_at"]
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/sites")
def list_sites(authorized: bool = Depends(verify_admin)):
    """List all registered sites (tokens hidden)."""
    sites = get_all_sites()
    return {"sites": sites, "total": len(sites)}


@router.put("/sites/{site_id}")
def edit_site(site_id: int, body: SiteUpdate, authorized: bool = Depends(verify_admin)):
    """Update site domain, token, or active status."""
    try:
        site = update_site(
            site_id,
            domain=body.domain,
            token=body.token,
            is_active=body.is_active
        )
        return {
            "status": "updated",
            "site": {
                "id": site["id"],
                "domain": site["domain"],
                "token": site["token"],
                "is_active": bool(site["is_active"]),
                "created_at": site["created_at"]
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/sites/{site_id}")
def remove_site(site_id: int, authorized: bool = Depends(verify_admin)):
    """Delete site and all its request logs."""
    if delete_site(site_id):
        return {"status": "deleted", "site_id": site_id}
    raise HTTPException(status_code=404, detail=f"Site id={site_id} not found")


@router.get("/stats")
def view_stats(
    site_id: Optional[int] = Query(None, description="Filter by site ID"),
    days: int = Query(30, description="Period in days"),
    authorized: bool = Depends(verify_admin)
):
    """View request statistics per site, daily breakdown, and endpoint usage."""
    return get_stats(site_id=site_id, days=days)
