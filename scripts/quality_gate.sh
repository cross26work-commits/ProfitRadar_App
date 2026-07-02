#!/bin/bash

set +e

echo ""
echo "======================================"
echo " Profit Radar Quality Gate v1"
echo "======================================"

echo ""
echo "1. Git"
git status

echo ""
echo "2. Backend Compile"
cd backend
python -m compileall app

echo ""
echo "3. Python Security"
pip-audit

echo ""
echo "4. Bandit"
bandit -r app

echo ""
echo "5. Backend Health"
curl http://localhost:8000/health

cd ../frontend

echo ""
echo "6. ESLint"
npm run lint

echo ""
echo "7. TypeScript"
npx tsc --noEmit

echo ""
echo "8. Next Build"
npm run build

echo ""
echo "9. Dead Code"
npx knip

echo ""
echo "10. Circular Dependency"
npx madge src --circular

echo ""
echo "11. Duplicate Code"
npx jscpd src

echo ""
echo "12. Bundle Analyzer"
ANALYZE=true npm run build

echo ""
echo "======================================"
echo " Manual Checks"
echo "======================================"

echo "□ Lighthouse"
echo "□ Accessibility"
echo "□ Responsive"
echo "□ UX"
echo "□ AI"
echo "□ Gmail"
echo "□ SMS"

echo ""
echo "Finished."
