# Cloudflare Tunnel Setup Script for Windows
# This script helps set up Cloudflare Tunnel for the Facebook bot

Write-Host "=== D Plus Skin Facebook Bot - Cloudflare Tunnel Setup ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check if cloudflared is installed
Write-Host "[1/5] Checking for cloudflared..." -ForegroundColor Yellow
$cloudflaredPath = "$env:LOCALAPPDATA\Microsoft\WindowsApps\cloudflared.exe"
if (Test-Path $cloudflaredPath) {
    Write-Host "✓ cloudflared found at: $cloudflaredPath" -ForegroundColor Green
} else {
    Write-Host "✗ cloudflared not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install cloudflared:" -ForegroundColor Yellow
    Write-Host "1. Download from: https://github.com/cloudflare/cloudflared/releases" -ForegroundColor White
    Write-Host "2. Look for: cloudflared-windows-amd64.exe" -ForegroundColor White
    Write-Host "3. Rename to: cloudflared.exe" -ForegroundColor White
    Write-Host "4. Move to: $env:LOCALAPPDATA\Microsoft\WindowsApps\" -ForegroundColor White
    Write-Host ""
    Write-Host "Or use Windows Package Manager:" -ForegroundColor Cyan
    Write-Host "winget install Cloudflare.cloudflared" -ForegroundColor White
    exit 1
}

Write-Host ""

# Step 2: Check if bot is running
Write-Host "[2/5] Checking if bot is running..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "✓ Bot is running on http://localhost:8000" -ForegroundColor Green
    }
} catch {
    Write-Host "✗ Bot is not running!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please start the bot first:" -ForegroundColor Yellow
    Write-Host "uvicorn main:app --reload --host 0.0.0.0 --port 8000" -ForegroundColor White
    exit 1
}

Write-Host ""

# Step 3: Login to Cloudflare
Write-Host "[3/5] Login to Cloudflare (skip if already logged in)..." -ForegroundColor Yellow
Write-Host "Run this command if you haven't logged in yet:" -ForegroundColor Cyan
Write-Host "cloudflared tunnel login" -ForegroundColor White
Write-Host ""

# Step 4: Create tunnel
Write-Host "[4/5] Creating Cloudflare Tunnel..." -ForegroundColor Yellow
$tunnelName = "dplus-skin-bot"
Write-Host "Tunnel name: $tunnelName" -ForegroundColor Cyan
Write-Host ""
Write-Host "Run this command to create the tunnel:" -ForegroundColor Yellow
Write-Host "cloudflared tunnel create $tunnelName" -ForegroundColor White
Write-Host ""

# Step 5: Set up config file
Write-Host "[5/5] Creating configuration file..." -ForegroundColor Yellow
$configPath = "config.yml"
$configContent = @"
tunnel: <TUNNEL_ID>
credentials-file: C:\Users\ttapk\.cloudflared\<TUNNEL_ID>.json

ingress:
  - hostname: <YOUR_SUBDOMAIN>.your-domain.com
    service: http://localhost:8000
    path: /webhook/*
  - service: http_status:404
"@

Write-Host "Creating $configPath ..." -ForegroundColor Cyan
$configContent | Out-File -FilePath $configPath -Encoding UTF8
Write-Host "✓ Config file created" -ForegroundColor Green
Write-Host ""

# Summary
Write-Host "=== Setup Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Replace <TUNNEL_ID> in config.yml with your actual tunnel ID" -ForegroundColor White
Write-Host "2. Replace <YOUR_SUBDOMAIN>.your-domain.com with your URL" -ForegroundColor White
Write-Host "   You can use any trycloudflare.com subdomain for free" -ForegroundColor White
Write-Host "3. Run the tunnel:" -ForegroundColor White
Write-Host "   cloudflared tunnel --config config.yml run" -ForegroundColor White
Write-Host ""
Write-Host "Your webhook URL will be:" -ForegroundColor Cyan
Write-Host "https://<YOUR_SUBDOMAIN>.trycloudflare.com/webhook" -ForegroundColor White
Write-Host ""
Write-Host "Verify token for Facebook: six_dragon_dildos_88" -ForegroundColor White
