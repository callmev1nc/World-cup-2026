#!/usr/bin/env bash
# Vercel build.
# Order: install build deps → fetch historical CSVs → precompute predictions → build SPA.
set -e
echo "=== install build deps ==="
pip install -r build-requirements.txt
echo "=== fetch historical CSVs ==="
python - <<'PY'
import urllib.request, os
os.makedirs('data/raw/kaggle', exist_ok=True)
base = 'https://raw.githubusercontent.com/martj42/international_results/master/'
for name in ('results.csv', 'goalscorers.csv'):
    out = os.path.join('data/raw/kaggle', name)
    if os.path.exists(out):
        continue
    try:
        urllib.request.urlretrieve(base + name, out)
        print('fetched', name)
    except Exception as e:
        print('SKIP', name, '-', e)
PY
echo "=== precompute predictions ==="
python backend/scripts/precompute.py
echo "=== build SPA ==="
( cd frontend && npm install && npm run build )
