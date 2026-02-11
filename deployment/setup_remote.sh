#!/bin/bash
set -e

BOT_DIR="/tmp/fb-bot"
BUNDLE="/tmp/bundle.tar.gz"

echo "=== [1/5] Setup directory ==="
mkdir -p "$BOT_DIR"
cd "$BOT_DIR"
tar -xzf "$BUNDLE"
rm -f "$BUNDLE"
echo "Extracted OK"

echo "=== [2/5] Install pip ==="
if ! python3 -m pip --version 2>/dev/null; then
    curl -sS https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
    python3 /tmp/get-pip.py --user --break-system-packages 2>/dev/null || python3 /tmp/get-pip.py --user
    echo "pip installed"
fi
python3 -m pip --version

echo "=== [3/5] Create venv ==="
if [ ! -d "$BOT_DIR/.venv" ]; then
    python3 -m venv "$BOT_DIR/.venv"
    echo "venv created"
else
    echo "venv exists"
fi

echo "=== [4/5] Install dependencies ==="
source "$BOT_DIR/.venv/bin/activate"
pip install --upgrade pip
pip install -r requirements.txt
echo "deps installed"

echo "=== [5/5] Create directories ==="
mkdir -p logs data

echo "========================================="
echo "SETUP COMPLETE!"
echo "Python: $(python --version)"
echo "Dir: $BOT_DIR"
echo "========================================="
