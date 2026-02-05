# deploy_tk578.ps1
# Automates deployment to tk578@100.98.140.57
# Uses ssh -t to allow Sudo password entry

$REMOTE_HOST = "100.98.140.57"
$REMOTE_USER = "tk578"
$REMOTE_DIR = "/home/tk578/fb-bot"
$LOCAL_BUNDLE = "bundle.tar.gz"

Write-Host "🚀 Starting Deployment to $REMOTE_USER@$REMOTE_HOST" -ForegroundColor Green

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

# 3. Setup & Deploy (Combined to minimize password prompts)
Write-Host "🚢 Uploading & Deploying..." -ForegroundColor Cyan
Write-Host "   (Please enter your sudo/ssh password if prompted)" -ForegroundColor Yellow

# Upload
scp $LOCAL_BUNDLE "${REMOTE_USER}@${REMOTE_HOST}:${LOCAL_BUNDLE}"

# Deploy Command
# We put everything in one script to run with a single SSH session
# 'dos2unix' behavior by stripping \r is handled by the shell interpretation usually, 
# but simply chaining commands with ; is safer than multi-line variables passed to ssh.
$DEPLOY_CMD = "mkdir -p $REMOTE_DIR; mv ~/bundle.tar.gz $REMOTE_DIR/bundle.tar.gz; cd $REMOTE_DIR; tar -xzf bundle.tar.gz; if ! command -v docker &> /dev/null; then echo 'Installing Docker...'; curl -fsSL https://get.docker.com | sudo sh; sudo usermod -aG docker $USER; fi; sudo rm -rf data/knowledge_base; sudo docker compose down --remove-orphans || true; sudo docker compose up -d --build; sudo docker image prune -f; rm bundle.tar.gz"

# Run with -t to support sudo password prompt
ssh -t "${REMOTE_USER}@${REMOTE_HOST}" "$DEPLOY_CMD"

# 4. Cleanup Local
if (Test-Path $LOCAL_BUNDLE) { Remove-Item $LOCAL_BUNDLE }

Write-Host "✅ Deployment Complete!" -ForegroundColor Green
