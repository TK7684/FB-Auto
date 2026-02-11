# nuke_ec2.ps1
# EMERGENCY SCRIPT: Wipes all Docker data to fix "No space left on device"

$REMOTE_HOST = "3.107.101.186"
$REMOTE_USER = "ubuntu"
$KEY_PATH = "G:\My Drive\Luna Backups\luna-pair.pem"

Write-Host "☢️ STATING NUCLEAR CLEANUP ON AWS EC2..." -ForegroundColor Red

$NUKE_CMD = "
    echo 'Stopping Docker Service...';
    sudo service docker stop;
    
    echo 'Deleting ALL Docker Data (Images, Containers, Volumes)...';
    sudo rm -rf /var/lib/docker;
    
    echo 'Deleting Temp Files...';
    sudo rm -rf /tmp/*;
    sudo rm -rf /home/ubuntu/fb-bot/bundle.tar.gz;
    
    echo 'Restarting Docker (This regenerates fresh install)...';
    sudo service docker start;
    
    echo 'Checking Disk Space...';
    df -h;
"

# Remove Windows CRLF
$CleanCommand = $NUKE_CMD -replace "`r", ""

ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_HOST" "$CleanCommand"

Write-Host "✅ Server is clean. You can now deploy." -ForegroundColor Green
