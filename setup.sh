#!/usr/bin/env bash
# TechDeal Finder — one-shot setup script
set -e

echo "──────────────────────────────────────"
echo "  TechDeal Finder  —  Setup"
echo "──────────────────────────────────────"

# 1. Install Python dependencies
echo ""
echo "[1/3] Installing Python packages…"
pip install -r requirements.txt --quiet

# 2. Install Playwright browsers
echo ""
echo "[2/3] Installing Playwright Chromium browser…"
playwright install chromium

# 3. Done
echo ""
echo "[3/3] Done! ✅"
echo ""
echo "  Run the app with:  python main.py"
echo ""
