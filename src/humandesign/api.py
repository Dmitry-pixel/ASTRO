import time
import sys
import importlib.metadata
import os

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from .routers import general
from .routers.v2 import general as general_v2
from .routers import analyze as analyze_router
from .routers import admin as admin_router
from .routers import panel as panel_router
from .auth import log_request
from .utils.version import get_version

__version__ = get_version()

if __version__ == "0.0.0":
    try:
        __version__ = importlib.metadata.version("humandesign-api")
    except importlib.metadata.PackageNotFoundError:
        pass

app = FastAPI(title="Human Design API", version=__version__)

# CORS — configurable via .env: CORS_ORIGINS=https://site1.com,https://site2.com
# Default: empty (no CORS headers = same-origin only, safest default)
_cors_origins = os.getenv("CORS_ORIGINS", "")
if _cors_origins:
    from fastapi.middleware.cors import CORSMiddleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in _cors_origins.split(",")],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )

# Static files
_static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=_static_dir), name="static")

# Include Routers
app.include_router(general.router)
app.include_router(general_v2.router)
app.include_router(analyze_router.router)
app.include_router(admin_router.router)
app.include_router(panel_router.router)


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Add security headers (defense-in-depth, Nginx also sets these)."""
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.middleware("http")
async def log_requests_middleware(request: Request, call_next):
    """Log every authenticated request with response time."""
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000

    # Only log if site was authenticated (state set by verify_token)
    site_id = getattr(request.state, "site_id", None)
    if site_id:
        try:
            log_request(
                site_id=site_id,
                endpoint=request.url.path,
                method=request.method,
                status_code=response.status_code,
                response_time_ms=round(elapsed_ms, 1)
            )
        except Exception as e:
            print(f"[LOGGING ERROR] {e}", file=sys.stderr)

    return response


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "humandesign.api:app",
        host="0.0.0.0",
        port=9021,
        reload=os.getenv("ENVIRONMENT") != "production"
    )
