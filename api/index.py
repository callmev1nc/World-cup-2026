"""Vercel serverless entry (single function).

Vercel zero-config detects this as a Python functions project (no root
package.json), so there is no separate static host. To keep one deploy/URL we
serve BOTH concerns from this function:
  - /api/*  -> the existing FastAPI app (mounted)
  - /*      -> the built SPA (frontend/dist), with an index.html fallback

vercel.json routes everything here via a catch-all rewrite, and bundles
frontend/dist + the historical CSVs into the function via includeFiles.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "src"))

from fastapi import FastAPI  # noqa: E402
from fastapi.responses import FileResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402

from wcpredictor.api import app as _backend  # noqa: E402

DIST = Path(__file__).parent.parent / "frontend" / "dist"

app = FastAPI()
app.mount("/api", _backend)

if (DIST / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")


@app.get("/{full_path:path}")
def _spa(full_path: str):
    """Serve a real static file if it exists, else index.html (SPA fallback)."""
    candidate = DIST / full_path
    if full_path and candidate.is_file():
        return FileResponse(candidate)
    if (DIST / "index.html").is_file():
        return FileResponse(DIST / "index.html")
    return {"error": "frontend build missing — buildCommand did not produce frontend/dist"}
