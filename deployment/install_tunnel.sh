#!/bin/bash
# Install Cloudflare Tunnel Service

# 1. Get Token from .env (handle quotes if present)
TOKEN=$(grep CLOUDFLARED_TOKEN ~/fb-bot/.env | cut -d= -f2 | tr -d '"' | tr -d "'")

if [ -z "$TOKEN" ]; then
    echo "❌ Error: CLOUDFLARED_TOKEN not found in ~/fb-bot/.env"
    exit 1
fi

echo "✅ Found Token: ${TOKEN:0:10}..."

# 2. Install Service (ignore error if already installed)
echo "Installing cloudflared service..."
sudo cloudflared service install "$TOKEN" 2>/dev/null || echo "⚠️ Service might already be installed"

# 3. Start Service
echo "Starting cloudflared service..."
sudo systemctl daemon-reload
sudo systemctl start cloudflared
sudo systemctl enable cloudflared

# 4. Check Status
if systemctl is-active --quiet cloudflared; then
    echo "✅ Cloudflare Tunnel is RUNNING!"
else
    echo "❌ Cloudflare Tunnel failed to start."
    systemctl status cloudflared --no-pager
    exit 1
fi
