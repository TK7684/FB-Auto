# deploy_remote.ps1
# Automates deployment to remote Tailscale host

$REMOTE_HOST = "100.85.171.112"
$REMOTE_USER = "dplus"
$REMOTE_DIR = "C:/Users/dplus/fb-bot"
$LOCAL_BUNDLE = "bundle.tar.gz"

Write-Host "Starting Deployment to ${REMOTE_USER}@${REMOTE_HOST}..."

# 1. Clean previous bundle
if (Test-Path $LOCAL_BUNDLE) { Remove-Item $LOCAL_BUNDLE }

# 2. Bundle files
Write-Host "Bundling files..."
tar -czf $LOCAL_BUNDLE --exclude=".git" --exclude=".venv" --exclude="__pycache__" --exclude=".idea" --exclude="logs" --exclude="data/debug" .

if (-not (Test-Path $LOCAL_BUNDLE)) {
    Write-Error "Failed to create bundle."
    exit 1
}

# 3. Create remote directory
Write-Host "Ensuring remote directory exists..."
ssh ${REMOTE_USER}@${REMOTE_HOST} "mkdir -p $REMOTE_DIR"

# 4. Copy Bundle
Write-Host "Uploading bundle..."
scp $LOCAL_BUNDLE "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/${LOCAL_BUNDLE}"

# 5. Execute Remote Commands
Write-Host "Executing Docker build on remote..."
$CMD = "cd $REMOTE_DIR; tar -xzf $LOCAL_BUNDLE; docker-compose up -d --build; docker image prune -f"
ssh ${REMOTE_USER}@${REMOTE_HOST} "powershell -Command ""$CMD"""

# 6. Cleanup
if (Test-Path $LOCAL_BUNDLE) { Remove-Item $LOCAL_BUNDLE }

Write-Host "Deployment Complete."
Write-Host "Main Bot: http://${REMOTE_HOST}:8000"
Write-Host "Cleanup Runner: Background Mode"
