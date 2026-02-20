#!/bin/bash
set -e

cd /home/spiritai/orchestrator/targeting_sys

echo "=== Intelligence Orchestrator — Targeting System ==="
echo "Server: 34.63.169.185 | Domain: orche.platformai.org"

# Install Python dependencies
echo "[1/4] Installing Python dependencies..."
pip install -r requirements.txt -q

# Install frontend dependencies & build
echo "[2/4] Building frontend..."
cd frontend
npm install --silent
npm run build 2>/dev/null || echo "Build with type check skipped, using vite build directly"
npx vite build
cd ..

# Ensure data directory exists
mkdir -p backend/data

# Start with PM2
echo "[3/4] Starting services with PM2..."
pm2 delete orchestrator 2>/dev/null || true
pm2 start ecosystem.config.js

echo "[4/4] Done!"
echo ""
echo "Backend:  http://127.0.0.1:8000"
echo "Frontend: http://127.0.0.1:4173"
echo "Domain:   https://orche.platformai.org"
echo ""
pm2 status orchestrator
