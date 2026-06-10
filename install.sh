#!/bin/bash
# ================================================================
#  RTL-SDR Web Interface — install script
#  Tested on: Ubuntu 20.04 / 22.04, Raspberry Pi OS (Bullseye+)
# ================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
err()  { echo -e "${RED}[✗]${NC} $1"; exit 1; }

echo -e "${CYAN}"
echo "  ╔══════════════════════════════════════╗"
echo "  ║   RTL-SDR Web — install script       ║"
echo "  ╚══════════════════════════════════════╝"
echo -e "${NC}"

# ── 1. System packages ──
log "Updating system packages..."
sudo apt-get update -qq
sudo apt-get install -y -qq \
    rtl-sdr \
    python3 python3-pip python3-venv \
    apache2 \
    git curl

sudo apt-get install -y -qq libxml2-dev 2>/dev/null || true

# ── 2. Apache modules ──
log "Enabling Apache modules..."
sudo a2enmod proxy proxy_http proxy_wstunnel rewrite headers
sudo a2enmod proxy_html 2>/dev/null || warn "proxy_html not available — not required"
sudo systemctl enable apache2

# ── 3. RTL-SDR kernel driver blacklist ──
log "Blacklisting RTL-SDR kernel drivers..."
sudo tee /etc/modprobe.d/rtlsdr.conf > /dev/null << 'CONF'
blacklist dvb_usb_rtl28xxu
blacklist rtl2832
blacklist rtl2830
CONF

# ── 4. udev rules (non-root USB access) ──
log "Setting up udev rules for RTL-SDR..."
sudo tee /etc/udev/rules.d/20-rtlsdr.rules > /dev/null << 'UDEV'
SUBSYSTEM=="usb", ATTRS{idVendor}=="0bda", ATTRS{idProduct}=="2832", GROUP="plugdev", MODE="0666"
SUBSYSTEM=="usb", ATTRS{idVendor}=="0bda", ATTRS{idProduct}=="2838", GROUP="plugdev", MODE="0666"
UDEV
sudo usermod -a -G plugdev www-data
sudo udevadm control --reload-rules

# ── 5. Deploy app ──
APP_DIR="/var/www/rtlsdr-web"
log "Deploying app to $APP_DIR..."
sudo mkdir -p "$APP_DIR"

# Copy only necessary files
sudo cp app.py config.py device.py capture.py scanner.py scheduler.py sockets.py "$APP_DIR/"
sudo cp -r routes "$APP_DIR/"
sudo cp -r templates "$APP_DIR/"
sudo mkdir -p "$APP_DIR/captures" "$APP_DIR/bugreports"
sudo chown -R www-data:www-data "$APP_DIR"

# ── 6. Python virtualenv ──
log "Creating Python virtual environment..."
sudo -u www-data python3 -m venv "$APP_DIR/venv"

log "Installing Python dependencies..."
sudo -u www-data "$APP_DIR/venv/bin/pip" install --quiet \
    flask \
    flask-socketio \
    apscheduler \
    "eventlet>=0.35" \
    gunicorn

# ── 7. Systemd service ──
log "Installing systemd service..."
sudo tee /etc/systemd/system/rtlsdr-web.service > /dev/null << SYSTEMD
[Unit]
Description=RTL-SDR Web Interface
After=network.target

[Service]
User=www-data
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/venv/bin/gunicorn \
    --worker-class eventlet \
    -w 1 \
    --bind 127.0.0.1:5000 \
    "app:create_app()"
Restart=always
RestartSec=5
Environment=SECRET_KEY=$(python3 -c "import os; print(os.urandom(24).hex())")

[Install]
WantedBy=multi-user.target
SYSTEMD

sudo systemctl daemon-reload
sudo systemctl enable rtlsdr-web
sudo systemctl start rtlsdr-web

# ── 8. Apache virtual host ──
log "Configuring Apache reverse proxy..."
sudo tee /etc/apache2/sites-available/rtlsdr.conf > /dev/null << 'APACHE'
<VirtualHost *:80>
    ServerName rtlsdr.local

    ProxyPreserveHost On
    ProxyPass        /socket.io/ ws://127.0.0.1:5000/socket.io/
    ProxyPassReverse /socket.io/ ws://127.0.0.1:5000/socket.io/
    ProxyPass        / http://127.0.0.1:5000/
    ProxyPassReverse / http://127.0.0.1:5000/

    ErrorLog  ${APACHE_LOG_DIR}/rtlsdr-error.log
    CustomLog ${APACHE_LOG_DIR}/rtlsdr-access.log combined
</VirtualHost>
APACHE

sudo a2ensite rtlsdr
sudo a2dissite 000-default 2>/dev/null || true
sudo systemctl restart apache2

# ── 9. Status check ──
echo ""
log "Checking services..."
sleep 3

if systemctl is-active --quiet rtlsdr-web; then
    log "rtlsdr-web service: ${GREEN}RUNNING${NC}"
else
    warn "rtlsdr-web service not running. Check: sudo journalctl -u rtlsdr-web -n 30"
fi

if systemctl is-active --quiet apache2; then
    log "Apache: ${GREEN}RUNNING${NC}"
fi

IP=$(hostname -I | awk '{print $1}')
echo ""
echo -e "${CYAN}═══════════════════════════════════════${NC}"
echo -e "  App URL:  ${GREEN}http://${IP}${NC}"
echo -e "  Local:    ${GREEN}http://localhost${NC}"
echo -e "${CYAN}═══════════════════════════════════════${NC}"
echo ""
echo -e "Useful commands:"
echo -e "  sudo systemctl status rtlsdr-web"
echo -e "  sudo journalctl -u rtlsdr-web -f"
echo -e "  rtl_test -t    (test device)"
echo ""
