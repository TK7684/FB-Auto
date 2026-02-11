# Start both bots in separate windows
Write-Host "🚀 Starting D Plus Skin Bots..."

# 1. Start Fast Responder
Start-Process powershell -ArgumentList "-NoExit", "-Command", "& 'python' 'scripts/fast_reply.py'" -WindowStyle Normal
Write-Host "   + Fast Responder (Recents) started."

# 2. Start Deep Cleaner (Runs immediately then waits 4h)
Start-Process powershell -ArgumentList "-NoExit", "-Command", "& 'python' 'scripts/cleanup_runner.py'" -WindowStyle Minimized
Write-Host "   + Deep Cleaner (History) started."

Write-Host "✅ Both bots are running. Check the windows for logs."
