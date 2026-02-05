# monitor_tk578.ps1
# 1. Checks Status
# 2. Downloads all logs to local folder

$REMOTE_HOST = "100.98.140.57"
$REMOTE_USER = "tk578"
$REMOTE_DIR = "/home/tk578/fb-bot"
$TIMESTAMP = Get-Date -Format "yyyyMMdd-HHmm"
$LOCAL_LOG_DIR = "logs\tk578_$TIMESTAMP"

Write-Host "🕵️  Monitoring Bot on $REMOTE_USER@$REMOTE_HOST..." -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path $LOCAL_LOG_DIR | Out-Null

# 1. Get Live Status
Write-Host "`n--- LIVE STATUS ---" -ForegroundColor Yellow
ssh -t "${REMOTE_USER}@${REMOTE_HOST}" "sudo docker ps"

# 2. Collect Logs remotely
Write-Host "`n📥 Collecting logs..." -ForegroundColor Cyan
$COLLECT_CMD = "
    mkdir -p ~/tmp_logs;
    sudo docker logs dplus_bot_api > ~/tmp_logs/docker_bot.log 2>&1;
    sudo docker logs dplus_cleanup_worker > ~/tmp_logs/docker_cleanup.log 2>&1;
    cp $REMOTE_DIR/logs/*.log ~/tmp_logs/ 2>/dev/null || true;
    tar -czf ~/logs_bundle.tar.gz -C ~/tmp_logs .;
    rm -rf ~/tmp_logs;
"
ssh -t "${REMOTE_USER}@${REMOTE_HOST}" $COLLECT_CMD

# 3. Download Bundle
Write-Host "⬇️  Downloading logs to $LOCAL_LOG_DIR..."
scp "${REMOTE_USER}@${REMOTE_HOST}:~/logs_bundle.tar.gz" "$LOCAL_LOG_DIR\logs.tar.gz"

# 4. Extract
Write-Host "📦 Extracting..."
cd $LOCAL_LOG_DIR
tar -xzf logs.tar.gz
Remove-Item logs.tar.gz

# 5. Cleanup Remote
ssh -t "${REMOTE_USER}@${REMOTE_HOST}" "rm ~/logs_bundle.tar.gz"

Write-Host "`n✅ Logs Saved to: $(Get-Location)" -ForegroundColor Green
Get-ChildItem . | Select-Object Name, Length
Invoke-Item .
