#!/usr/bin/env bash
# ============================================================
#  Astro Gates — Human Design API
#  One-command deploy: Docker + Nginx + optional SSL
#
#  Usage:
#    bash deploy.sh                    # HTTP only (port 80)
#    bash deploy.sh api.example.com    # HTTP + HTTPS with Let's Encrypt
#
#  What it does:
#    1. Installs Docker & Docker Compose
#    2. Installs Nginx
#    3. Builds and starts API container (port 9021 internal)
#    4. Configures Nginx as reverse proxy (80 → 9021)
#    5. If domain provided: installs Certbot + SSL certificate
#    6. Opens firewall ports (80, 443)
#
#  After deploy:
#    http://YOUR_IP/panel/login  (or https://your-domain.com/panel/login)
#    Login: 12345 → Settings → change token immediately
# ============================================================
set -euo pipefail

DOMAIN="${1:-}"
CONTAINER_NAME="${CONTAINER_NAME:-humandesignapi}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

info()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
step()  { echo -e "\n${CYAN}${BOLD}── $1 ──${NC}"; }
error() { echo -e "${RED}[✗]${NC} $1"; exit 1; }

# ============================================================
# 1. PRE-FLIGHT CHECKS
# ============================================================
step "Pre-flight checks"

if [[ $EUID -ne 0 ]]; then
    warn "Not running as root. Some steps may require sudo."
    SUDO="sudo"
else
    SUDO=""
fi

if [[ -f /etc/os-release ]]; then
    . /etc/os-release
    info "OS: $PRETTY_NAME"
else
    warn "Cannot detect OS"
fi

# Find project directory
if [[ ! -f "docker-compose.yml" ]]; then
    ARCHIVE=$(ls -t humandesign_api*.tar.gz 2>/dev/null | head -1)
    if [[ -n "$ARCHIVE" ]]; then
        info "Found archive: $ARCHIVE"

        # Extract and check success
        if ! tar xzf "$ARCHIVE"; then
            error "Failed to extract $ARCHIVE — file may be corrupted"
        fi

        # Auto-detect extracted directory (top-level dir inside the archive)
        EXTRACTED_DIR=$(tar tzf "$ARCHIVE" | head -1 | cut -d/ -f1)
        if [[ -z "$EXTRACTED_DIR" || ! -d "$EXTRACTED_DIR" ]]; then
            error "Cannot find extracted directory from $ARCHIVE"
        fi

        cd "$EXTRACTED_DIR"
        info "Extracted → $EXTRACTED_DIR/"
    else
        error "Run from the humandesign_api directory or place .tar.gz next to this script."
    fi
fi

[[ -f "docker-compose.yml" ]] || error "docker-compose.yml not found"
[[ -f "Dockerfile" ]]         || error "Dockerfile not found"
[[ -f ".env" ]]               || error ".env not found"
info "Project files OK"

PROJECT_DIR=$(pwd)

if [[ -n "$DOMAIN" ]]; then
    info "Domain: $DOMAIN (will configure SSL)"
else
    info "No domain provided — HTTP only (pass domain as argument for SSL)"
fi

# ============================================================
# 2. INSTALL DOCKER
# ============================================================
step "Docker"

if command -v docker &>/dev/null; then
    info "Already installed: $(docker --version)"
else
    info "Installing Docker..."
    $SUDO apt-get update -qq
    $SUDO apt-get install -y -qq ca-certificates curl gnupg lsb-release > /dev/null 2>&1

    $SUDO install -m 0755 -d /etc/apt/keyrings
    if [[ ! -f /etc/apt/keyrings/docker.gpg ]]; then
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | $SUDO gpg --dearmor -o /etc/apt/keyrings/docker.gpg
        $SUDO chmod a+r /etc/apt/keyrings/docker.gpg
    fi

    ARCH=$(dpkg --print-architecture)
    CODENAME=$(. /etc/os-release && echo "$VERSION_CODENAME")
    echo "deb [arch=$ARCH signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $CODENAME stable" | \
        $SUDO tee /etc/apt/sources.list.d/docker.list > /dev/null

    $SUDO apt-get update -qq
    $SUDO apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin > /dev/null 2>&1
    $SUDO systemctl enable docker --now 2>/dev/null || true
    info "Docker installed: $(docker --version)"
fi

# Docker Compose
if command -v docker-compose &>/dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &>/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
else
    info "Installing docker-compose..."
    $SUDO apt-get install -y -qq docker-compose > /dev/null 2>&1 || {
        $SUDO curl -fsSL "https://github.com/docker/compose/releases/download/v2.27.0/docker-compose-$(uname -s)-$(uname -m)" \
            -o /usr/local/bin/docker-compose
        $SUDO chmod +x /usr/local/bin/docker-compose
    }
    COMPOSE_CMD="docker-compose"
fi
info "Compose: $COMPOSE_CMD"

# ============================================================
# 3. INSTALL NGINX
# ============================================================
step "Nginx"

if command -v nginx &>/dev/null; then
    info "Already installed: $(nginx -v 2>&1)"
else
    info "Installing Nginx..."
    $SUDO apt-get update -qq
    $SUDO apt-get install -y -qq nginx > /dev/null 2>&1
    $SUDO systemctl enable nginx --now 2>/dev/null || true
    info "Nginx installed"
fi

# ============================================================
# 4. FIREWALL
# ============================================================
step "Firewall"

if command -v ufw &>/dev/null && $SUDO ufw status 2>/dev/null | grep -q "Status: active"; then
    for PORT in 80 443; do
        if ! $SUDO ufw status | grep -q "$PORT"; then
            $SUDO ufw allow $PORT/tcp > /dev/null 2>&1
            info "Port $PORT opened"
        else
            info "Port $PORT already open"
        fi
    done
    # Close direct access to 9021 from outside (Nginx handles it)
    $SUDO ufw delete allow 9021/tcp > /dev/null 2>&1 || true
    info "Port 9021 closed (Nginx proxies internally)"
else
    info "UFW not active — ensure ports 80, 443 are open in cloud firewall"
fi

# ============================================================
# 5. PREPARE PROJECT FILES
# ============================================================
step "Preparing project"

cd "$PROJECT_DIR"

# Create persistent data directory (mounted as volume in Docker)
mkdir -p data

# Copy .env into data/ if not already there (Docker reads from data/.env)
if [[ ! -f "data/.env" ]]; then
    if [[ -f ".env" ]]; then
        cp .env data/.env
        info "Copied .env → data/.env"
    else
        error ".env not found!"
    fi
else
    info "data/.env already exists"
fi

# SQLite DB will be auto-created by the app in data/api_auth.db
if [[ -f "data/api_auth.db" ]]; then
    info "data/api_auth.db exists ($(du -h data/api_auth.db | cut -f1))"
else
    info "data/api_auth.db will be created on first start"
fi

# Fix permissions: container runs as appuser (UID 1000)
# data/ must be writable for SQLite (db + journal + wal) and .env (token change)
$SUDO chown -R 1000:1000 data/
$SUDO chmod 755 data/
info "data/ permissions set (owner: UID 1000 = appuser in container)"

CURRENT_TOKEN=$(grep "^HD_ADMIN_TOKEN=" data/.env | cut -d= -f2- || echo "")
if [[ -n "$CURRENT_TOKEN" ]]; then
    info "Admin token: ${CURRENT_TOKEN:0:4}**** (${#CURRENT_TOKEN} chars)"
else
    warn "HD_ADMIN_TOKEN is empty in data/.env!"
fi

# ============================================================
# 6. BUILD & START DOCKER
# ============================================================
step "Building Docker image"

$SUDO $COMPOSE_CMD build --no-cache 2>&1 | tail -5
info "Image built"

$SUDO $COMPOSE_CMD down 2>/dev/null || true

step "Starting container"

$SUDO $COMPOSE_CMD up -d
info "Container started"

# Wait for healthy
step "Waiting for healthcheck"

MAX_WAIT=90
ELAPSED=0
while [[ $ELAPSED -lt $MAX_WAIT ]]; do
    STATUS=$($SUDO docker inspect --format='{{.State.Health.Status}}' $CONTAINER_NAME 2>/dev/null || echo "starting")
    [[ "$STATUS" == "healthy" ]] && break
    echo -ne "\r  ${ELAPSED}s... (${STATUS})  "
    sleep 3
    ELAPSED=$((ELAPSED + 3))
done
echo ""

STATUS=$($SUDO docker inspect --format='{{.State.Health.Status}}' $CONTAINER_NAME 2>/dev/null || echo "unknown")
if [[ "$STATUS" == "healthy" ]]; then
    info "API is healthy!"
else
    warn "Status: $STATUS — check: docker logs $CONTAINER_NAME"
fi

# ============================================================
# 7. CONFIGURE NGINX
# ============================================================
step "Configuring Nginx"

# Determine server_name
if [[ -n "$DOMAIN" ]]; then
    NGINX_SERVER_NAME="$DOMAIN"
else
    NGINX_SERVER_NAME="_"
fi

# Write Nginx config
$SUDO tee /etc/nginx/sites-available/astrogates > /dev/null <<NGINX_CONF
# Astro Gates — Human Design API
# Auto-generated by deploy.sh

# Rate limiting zone: 10 req/sec per IP
limit_req_zone \$binary_remote_addr zone=api_limit:10m rate=10r/s;

server {
    listen 80;
    server_name ${NGINX_SERVER_NAME};

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Max request body (for POST /v2/calculate)
    client_max_body_size 1m;

    # Gzip
    gzip on;
    gzip_types application/json text/html text/css application/javascript;
    gzip_min_length 256;

    # API proxy
    location / {
        limit_req zone=api_limit burst=20 nodelay;

        proxy_pass http://127.0.0.1:9021;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # Timeouts (HD calculations can take a few seconds)
        proxy_connect_timeout 10s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;

        # Buffering
        proxy_buffering on;
        proxy_buffer_size 8k;
        proxy_buffers 8 8k;
    }

    # Static files (proxied via FastAPI — only favicon.ico, CSS/JS load from CDN)
    # Aggressive caching: browsers won't re-request for 30 days
    location /static/ {
        proxy_pass http://127.0.0.1:9021/static/;
        proxy_cache_valid 200 30d;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000, immutable";
    }

    # Block direct access to .env, .db, .git
    location ~ /\. {
        deny all;
        return 404;
    }
}
NGINX_CONF

# Enable site
$SUDO ln -sf /etc/nginx/sites-available/astrogates /etc/nginx/sites-enabled/astrogates

# Remove default site if it conflicts
if [[ -f /etc/nginx/sites-enabled/default ]]; then
    $SUDO rm -f /etc/nginx/sites-enabled/default
    info "Removed default Nginx site"
fi

# Test and reload
$SUDO nginx -t 2>&1 | tail -2
$SUDO systemctl reload nginx
info "Nginx configured: ${NGINX_SERVER_NAME} :80 → :9021"

# ============================================================
# 8. SSL (if domain provided)
# ============================================================
if [[ -n "$DOMAIN" ]]; then
    step "SSL certificate (Let's Encrypt)"

    if command -v certbot &>/dev/null; then
        info "Certbot already installed"
    else
        info "Installing Certbot..."
        $SUDO apt-get install -y -qq certbot python3-certbot-nginx > /dev/null 2>&1
        info "Certbot installed"
    fi

    info "Requesting SSL certificate for $DOMAIN..."
    echo ""
    $SUDO certbot --nginx \
        -d "$DOMAIN" \
        --non-interactive \
        --agree-tos \
        --redirect \
        --register-unsafely-without-email \
        2>&1 | tail -5

    # Verify auto-renewal timer
    if $SUDO systemctl is-active certbot.timer &>/dev/null; then
        info "Auto-renewal timer active"
    else
        $SUDO systemctl enable certbot.timer --now 2>/dev/null || true
        info "Auto-renewal timer enabled"
    fi

    info "SSL configured! HTTPS is active."
else
    warn "No domain → no SSL. To add later: bash deploy.sh your-domain.com"
fi

# ============================================================
# 9. DONE
# ============================================================
SERVER_IP=$(curl -s --max-time 5 ifconfig.me 2>/dev/null || hostname -I 2>/dev/null | awk '{print $1}' || echo "YOUR_SERVER_IP")

step "Deploy complete!"

echo ""
if [[ -n "$DOMAIN" ]]; then
    echo -e "  ${BOLD}API endpoint:${NC}    https://${DOMAIN}"
    echo -e "  ${BOLD}Admin panel:${NC}     https://${DOMAIN}/panel/login"
    echo -e "  ${BOLD}Swagger docs:${NC}    https://${DOMAIN}/docs"
else
    echo -e "  ${BOLD}API endpoint:${NC}    http://${SERVER_IP}"
    echo -e "  ${BOLD}Admin panel:${NC}     http://${SERVER_IP}/panel/login"
    echo -e "  ${BOLD}Swagger docs:${NC}    http://${SERVER_IP}/docs"
fi
echo -e "  ${BOLD}Login token:${NC}     ${YELLOW}12345${NC}"
echo ""
echo -e "  ${RED}${BOLD}⚠  FIRST THING: go to Settings and change the admin token!${NC}"
echo ""
echo -e "  ${CYAN}Architecture:${NC}"
echo "    Client → Nginx (:80/:443) → Docker (:9021) → uvicorn → FastAPI"
echo ""
echo -e "  ${CYAN}Useful commands:${NC}"
echo "    docker logs -f $CONTAINER_NAME              # API logs"
echo "    sudo tail -f /var/log/nginx/access.log     # Nginx access log"
echo "    sudo tail -f /var/log/nginx/error.log      # Nginx errors"
echo "    docker restart $CONTAINER_NAME              # restart API"
echo "    sudo nginx -t && sudo systemctl reload nginx  # reload Nginx"
echo "    sudo certbot renew --dry-run               # test SSL renewal"
echo ""
echo -e "  ${CYAN}Config files:${NC}"
echo "    Nginx:   /etc/nginx/sites-available/astrogates"
echo "    .env:    ${PROJECT_DIR}/data/.env"
echo "    DB:      ${PROJECT_DIR}/data/api_auth.db"
echo "    Docker:  ${PROJECT_DIR}/docker-compose.yml"
echo ""
