#!/usr/bin/env bash
# Vercel build. The SPA MUST build (the function serves it); the historical CSVs
# are a best-effort fetch using stdlib only (pandas/httpx aren't in the build
# image — the function runtime installs them from requirements.txt and parses
# the bundled CSVs there).
set -e
echo "=== build SPA ==="
( cd frontend && npm install && npm run build )
echo "=== fetch historical CSVs (stdlib; parsed at runtime) ==="
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
