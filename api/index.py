"""Vercel serverless entry. Mounts the existing FastAPI app under /api so the
SPA (served at root) can call /api/matches, /api/predict/<id>, etc. on the same
origin. The backend src layout isn't on the default path, so add it explicitly."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend", "src"))

from fastapi import FastAPI  # noqa: E402
from wcpredictor.api import app as _backend  # noqa: E402

app = FastAPI()
app.mount("/api", _backend)
