#!/bin/bash
# Re-Install Cloudflare Tunnel Service (Clean Config)

# 1. Get Token
TOKEN=$(grep CLOUDFLARED_TOKEN ~/fb-bot/.env | cut -d= -f2 | tr -d '"' | tr -d "'")

if [ -z "$TOKEN" ]; then
    echo "❌ Error: CLOUDFLARED_TOKEN not found"
    exit 1
fi

echo "Using Token: ${TOKEN:0:10}..."

# 2. Write Unit File
echo "Writing /etc/systemd/system/cloudflared.service..."
cat <<EOF | sudo tee /etc/systemd/system/cloudflared.service
[Unit]
Description=Cloudflare Tunnel
After=network.target

[Service]
TimeoutStartSec=0
Type=notify
ExecStart=/usr/bin/cloudflared tunnel run --token $TOKEN
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
EOF

# 3. Reload and Restart
echo "Reloading systemd..."
sudo systemctl daemon-reload
sudo systemctl enable cloudflared
sudo systemctl restart cloudflared

# 4. Check Status
sleep 2
if systemctl is-active --quiet cloudflared; then
    echo "✅ Cloudflare Tunnel is RUNNING!"
else
    echo "❌ Cloudflare Tunnel failed to start."
    systemctl status cloudflared --no-pager
    exit 1
fi
