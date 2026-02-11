# deploy_ec2.ps1
# Automates deployment to AWS EC2 (Ubuntu) with optimizations for Free Tier
# Fixes:
# 1. Adds 2GB Swap (prevents pip install crashes)
# 2. Prunes old Docker data (fixes "No space left on device")
# 3. Strips Windows line endings (fixes bash errors)

$REMOTE_HOST = "3.107.101.186"
$REMOTE_USER = "ubuntu"
$KEY_PATH = "G:\My Drive\Luna Backups\luna-pair.pem"
$REMOTE_DIR = "/home/ubuntu/fb-bot"
$LOCAL_BUNDLE = "bundle.tar.gz"

Write-Host "🚀 Starting Deployment to AWS EC2 ($REMOTE_HOST)..." -ForegroundColor Green

# --- Helper to sanitize commands for SSH ---
function Run-SSH {
    param([string]$Command)
    # Remove Windows Carriage Returns (\r) to prevent bash errors
    $CleanCommand = $Command -replace "`r", ""
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_HOST" "$CleanCommand"
}

# 1. Clean previous bundle
if (Test-Path $LOCAL_BUNDLE) { Remove-Item $LOCAL_BUNDLE }

# 2. Bundle files
Write-Host "📦 Bundling files..." -ForegroundColor Cyan
try {
    tar -czf $LOCAL_BUNDLE --exclude=".git" --exclude=".venv" --exclude="__pycache__" --exclude=".idea" --exclude="logs" --exclude="data/debug" .
}
catch {
    Write-Error "Failed to zip files."
    exit 1
}

# 3. Prepare Server (Swap + Prune)
Write-Host "🔧 Optimizing Server (Adding Swap & Cleaning Disk)..." -ForegroundColor Cyan
$OPTIMIZE_CMD = "
    # 1. Add 2GB Swap file if it doesn't exist (Fixes OOM kills)
    if [ ! -f /swapfile ]; then
        echo 'Creating 2GB Swap...';
        sudo fallocate -l 2G /swapfile;
        sudo chmod 600 /swapfile;
        sudo mkswap /swapfile;
        sudo swapon /swapfile;
    fi;

    # 2. Free up disk space (Fixes 'No space left on device')
    echo 'Pruning Docker...';
    sudo docker system prune -af;
    
    # 3. Create Project Dir
    mkdir -p $REMOTE_DIR;
"
Run-SSH -Command $OPTIMIZE_CMD

# 4. Upload Bundle
Write-Host "📤 Uploading bundle..." -ForegroundColor Cyan
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no $LOCAL_BUNDLE "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/${LOCAL_BUNDLE}"

# 5. Deploy
Write-Host "🚢 Deploying..." -ForegroundColor Cyan
$DEPLOY_CMD = @"
    cd $REMOTE_DIR;
    tar -xzf $LOCAL_BUNDLE;
    
    echo 'Building and Starting Containers...';
    sudo docker compose down --remove-orphans || true;
    sudo docker compose up -d --build;
    
    echo 'Cleaning up...';
    rm $LOCAL_BUNDLE;
    sudo docker image prune -f;
"@
Run-SSH -Command $DEPLOY_CMD

# 6. Cleanup Local
if (Test-Path $LOCAL_BUNDLE) { Remove-Item $LOCAL_BUNDLE }

Write-Host "✅ Deployment Complete!" -ForegroundColor Green
Write-Host "   Bot is running on the cloud."
