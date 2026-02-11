$REMOTE_HOST = "100.98.140.57"
$REMOTE_USER = "tk578"
$LOG_DIR = "logs/remote"

# Create local log dir
if (-not (Test-Path $LOG_DIR)) { New-Item -ItemType Directory -Force -Path $LOG_DIR }

Write-Host "Fetching logs from ${REMOTE_USER}@${REMOTE_HOST}..."

# Fetch Main Bot Logs
Write-Host "Fetching dplus_bot_api logs..."
ssh ${REMOTE_USER}@${REMOTE_HOST} "docker logs dplus_bot_api --tail 200" | Out-File -Encoding UTF8 "$LOG_DIR/remote_api.log"

# Fetch Sweeper Logs
Write-Host "Fetching dplus_cleanup_worker logs..."
ssh ${REMOTE_USER}@${REMOTE_HOST} "docker logs dplus_cleanup_worker --tail 200" | Out-File -Encoding UTF8 "$LOG_DIR/remote_sweeper.log"

Write-Host "Logs saved to $LOG_DIR"
Get-Content "$LOG_DIR/remote_api.log" -Tail 5
Get-Content "$LOG_DIR/remote_sweeper.log" -Tail 5
