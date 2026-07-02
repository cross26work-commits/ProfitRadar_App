#!/bin/bash

set -e

echo "========================================"
echo " Profit Radar Health Check"
echo "========================================"

echo ""
echo "[1/12] Git Status"
git status --short

echo ""
echo "[2/12] Backend Compile"
cd backend
python -m compileall app

echo ""
echo "[3/12] Backend Health"
curl -s http://localhost:8000/health || echo "Backend Offline"

echo ""
echo "[4/12] Frontend Lint"
cd ../frontend
npm run lint

echo ""
echo "[5/12] Next Build"
npm run build

echo ""
echo "[6/12] TypeScript"
npx tsc --noEmit

echo ""
echo "[7/12] Route Structure"
find src/app -maxdepth 3 -type d | sort

echo ""
echo "[8/12] Service Structure"
find src/services -maxdepth 2 -type f | sort

echo ""
echo "[9/12] Components"
find src/components -maxdepth 2 -type d | sort

echo ""
echo "[10/12] TODO / FIXME"
grep -RInE "TODO|FIXME|HACK" src backend ../backend/app || true

echo ""
echo "[11/12] Console.log"
grep -RIn "console.log" src || true

echo ""
echo "[12/12] API Files"
find ../backend/app/api -type f | sort

echo ""
echo "========================================"
echo "Health Check Finished"
echo "========================================"
