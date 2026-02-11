# check_status_tk578.ps1
# Checks if the bot containers are running on tk578@100.98.140.57
# Uses ssh -t for Sudo password support

$REMOTE_HOST = "100.98.140.57"
$REMOTE_USER = "tk578"

Write-Host "🔍 Checking Bot Status on $REMOTE_USER@$REMOTE_HOST..." -ForegroundColor Cyan
Write-Host "(Enter Password if asked)" -ForegroundColor Gray

# Combined check
$CMD = "echo '--- Docker Containers ---'; sudo docker ps; echo ''; echo '--- Bot Logs ---'; sudo docker logs --tail 10 dplus_bot_api"

ssh -t "${REMOTE_USER}@${REMOTE_HOST}" "$CMD"

Write-Host "`n✅ Check Complete." -ForegroundColor Green
