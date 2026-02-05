# get_logs_ec2.ps1
# Downloads logs from AWS EC2 for debugging

$REMOTE_HOST = "3.107.101.186"
$REMOTE_USER = "ubuntu"
$KEY_PATH = "G:\My Drive\Luna Backups\luna-pair.pem"
$REMOTE_DIR = "/home/ubuntu/fb-bot"
$LOCAL_LOGS_DIR = "downloaded_logs"

Write-Host "📥 Fetching logs from AWS EC2..." -ForegroundColor Cyan

# Ensure local dir exists
if (-not (Test-Path $LOCAL_LOGS_DIR)) { mkdir $LOCAL_LOGS_DIR }

# 1. Fetch main application logs
Write-Host "   Downloading app logs..."
try {
    scp -i "$KEY_PATH" -o StrictHostKeyChecking=no "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/logs/*.log" "$LOCAL_LOGS_DIR/"
}
catch {
    Write-Warning "Could not fetch app logs (maybe none exist yet?)"
}

# 2. Generate Docker logs on remote
Write-Host "   Generating Docker logs..."
# Simple one-liner
$CMD = "sudo docker logs dplus_bot_api > ~/bot_docker.log 2>&1; sudo docker logs dplus_cleanup_worker > ~/cleanup_docker.log 2>&1"
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "${REMOTE_USER}@${REMOTE_HOST}" "$CMD"

# 3. Download them
Write-Host "   Downloading Docker logs..."
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no "${REMOTE_USER}@${REMOTE_HOST}:~/bot_docker.log" "$LOCAL_LOGS_DIR/"
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no "${REMOTE_USER}@${REMOTE_HOST}:~/cleanup_docker.log" "$LOCAL_LOGS_DIR/"

Write-Host "✅ Logs saved to folder: $LOCAL_LOGS_DIR" -ForegroundColor Green
Invoke-Item $LOCAL_LOGS_DIR
