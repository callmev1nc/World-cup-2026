#!/usr/bin/env bash
# Vercel build: install backend deps, pre-download the historical CSVs (bundled
# into the serverless function via includeFiles so cold-starts don't hit the
# network), then build the Vite SPA.
set -e
echo "=== install backend deps (for build-time data prep) ==="
pip install -r requirements.txt
echo "=== pre-download historical results + goalscorers ==="
python -c "import sys; sys.path.insert(0,'backend/src'); from wcpredictor.clients.kaggle import load_international_results as R, load_goalscorers as G; n=R(); g=G(); print(f'results={len(n)} goalscorers={len(g)}')"
echo "=== build frontend ==="
cd frontend && npm install && npm run build
