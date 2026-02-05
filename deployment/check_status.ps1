# check_status.ps1
# Checks if the bot containers are running on AWS EC2

$REMOTE_HOST = "3.107.101.186"
$REMOTE_USER = "ubuntu"
$KEY_PATH = "G:\My Drive\Luna Backups\luna-pair.pem"

Write-Host "🔍 Checking Bot Status on AWS EC2..." -ForegroundColor Cyan

# 1. Check Docker Containers
Write-Host "`n--- Docker Containers (Should show 'Up') ---" -ForegroundColor Yellow
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "${REMOTE_USER}@${REMOTE_HOST}" "sudo docker ps"

# 2. Check Last 20 lines of Main Bot Log
Write-Host "`n--- Main Bot Logs (Last 10 lines) ---" -ForegroundColor Yellow
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "${REMOTE_USER}@${REMOTE_HOST}" "sudo docker logs --tail 10 dplus_bot_api"

# 3. Check Last 20 lines of Cleanup Runner
Write-Host "`n--- Cleanup Runner Logs (Last 10 lines) ---" -ForegroundColor Yellow
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "${REMOTE_USER}@${REMOTE_HOST}" "sudo docker logs --tail 10 dplus_cleanup_worker"

Write-Host "`n✅ Check Complete." -ForegroundColor Green
