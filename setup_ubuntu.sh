#!/usr/bin/env bash
# ============================================================
#  Human Design API — Ubuntu Setup Script
#  Tested on: Ubuntu 22.04 / 24.04 (including WSL2)
# ============================================================
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# ---- System packages ----
info "Installing system dependencies..."
sudo apt-get update -qq
sudo apt-get install -y --no-install-recommends \
    python3 python3-venv python3-dev python3-pip gcc g++ make git curl > /dev/null 2>&1
info "System packages installed."

# ---- Python version ----
PY_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)
[[ "$PY_MINOR" -lt 12 ]] && error "Python 3.12+ required, found $PY_VERSION"
info "Python $PY_VERSION — OK."

# ---- Virtual environment ----
VENV_DIR="venv"
if [[ ! -d "$VENV_DIR" ]]; then
    info "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"
pip install --upgrade pip setuptools wheel -q

# ---- Dependencies ----
info "Installing Python dependencies..."
pip install -r requirements.txt -q
pip install -e . -q
info "Dependencies installed."

# ---- .env ----
if [[ ! -f .env ]]; then
    info "Creating .env with default admin token..."
    cp .env_example .env
    ADMIN_TOKEN=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    sed -i "s/your_admin_secret_here/$ADMIN_TOKEN/" .env
    info ".env created. Admin token: $ADMIN_TOKEN"
    warn "Save this token! It's needed for /admin/* endpoints."
else
    warn ".env already exists, skipping."
fi

# ---- Verify ----
info "Verifying installation..."
python3 -c "
import os, swisseph as swe
print(f'  Swiss Ephemeris version: {swe.version}')
ephe_dir = os.path.join(os.getcwd(), 'ephe')
if os.path.isdir(ephe_dir):
    swe.set_ephe_path(ephe_dir)
    result = swe.calc_ut(2451545.0, swe.SUN)
    serr = result[2] if len(result) > 2 else ''
    mode = 'Moshier' if 'Moshier' in serr else 'Swiss Ephemeris (DE431)'
    print(f'  Ephemeris mode: {mode}')
from zoneinfo import ZoneInfo
from datetime import datetime
tz = ZoneInfo('Europe/Moscow')
dt = datetime(1990, 7, 15, 14, 30, tzinfo=tz)
print(f'  zoneinfo: OK')
from timezonefinder import TimezoneFinder
tf = TimezoneFinder(in_memory=True)
print(f'  TimezoneFinder: OK')
from fastapi import FastAPI
print(f'  FastAPI: OK')
print()
print('  All checks passed!')
"

echo ""
info "============================================"
info "  Setup complete!"
info "============================================"
echo ""
echo "  Start the API:"
echo "    source venv/bin/activate"
echo "    uvicorn humandesign.api:app --host 0.0.0.0 --port 9021 --reload"
echo ""
echo "  Or with Docker:"
echo "    docker-compose up --build -d"
echo ""
echo "  Swagger UI: http://localhost:9021/docs"
echo ""
echo "  First steps:"
echo "    1. Create a site:"
echo '       curl -X POST http://localhost:9021/admin/sites \'
echo '         -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \'
echo '         -H "Content-Type: application/json" \'
echo '         -d '"'"'{"domain": "mysite.com"}'"'"
echo ""
echo "    2. Use the returned token for calculations:"
echo '       curl "http://localhost:9021/calculate?year=1990&month=7&day=15&hour=14&minute=30&place=London&latitude=51.5074&longitude=-0.1278" \'
echo '         -H "Authorization: Bearer SITE_TOKEN"'
echo ""
