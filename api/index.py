"""Vercel serverless entry (single function).
Serves precomputed prediction JSON + the built SPA. No heavy imports
(pandas/scipy/numpy run only at build time in backend/scripts/precompute.py).

    /api/matches      -> static precomputed matches list (merged with live store)
    /api/predict/{id} -> static prediction (patched if overlay says finished)
    /api/best-bets    -> top 8 +EV picks (filtered to drop finished)
    /api/refresh      -> fetch ESPN results + upsert into Supabase (auth required)
    /*                -> SPA (frontend/dist), index.html fallback

vercel.json bundles frontend/dist + data/processed + data/raw/sample.
"""
import json
import os
import sys
from pathlib import Path

_PATH = Path(__file__).parent
sys.path.insert(0, str(_PATH.parent / "backend" / "src"))
sys.path.insert(0, str(_PATH))

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from lib import get_fixtures, get_overlay, save_overlay, patch_finished
from wcpredictor.schemas import finished_prediction

DIST = Path(__file__).parent.parent / "frontend" / "dist"
PROCESSED = Path(__file__).parent.parent / "data" / "processed"

REFRESH_SECRET = os.getenv("REFRESH_SECRET", "")

# --- Load precomputed data at module import (cheap — small JSON files) ---
_predictions: dict[str, dict] = {}
_best_bets: list[dict] = []
_matches: list[dict] = []

for name in ("predictions.json", "best_bets.json", "matches.json"):
    path = PROCESSED / name
    if path.exists():
        data = json.loads(path.read_text())
        if name == "predictions.json":
            _predictions = data
        elif name == "best_bets.json":
            _best_bets = data
        elif name == "matches.json":
            _matches = data

app = FastAPI()


@app.get("/matches")
def get_matches():
    overlay = get_overlay()
    merged = []
    for m in _matches:
        mid = m["match_id"]
        if mid in overlay and overlay[mid].get("status") == "finished":
            m = {**m, "state": "finished"}
            ov = overlay[mid]
            if "ft_home" in ov and "ft_away" in ov:
                m["actual_score"] = f"{ov['ft_home']}-{ov['ft_away']}"
            if ov.get("winner"):
                m["result"] = ov["winner"]
        merged.append(m)
    return merged


@app.get("/predict/{match_id}")
def get_predict(match_id: str):
    overlay = get_overlay()
    # If the overlay marks this match as finished, patch the baked prediction.
    if match_id in overlay and overlay[match_id].get("status") == "finished":
        pred = _predictions.get(match_id)
        if pred is None:
            # No baked prediction (e.g. TBD slot resolved after deploy).
            fixtures = get_fixtures()
            fixture = next((f for f in fixtures if f["fixture_id"] == match_id), {})
            pred = finished_prediction(
                match_id=match_id,
                round=fixture.get("round"),
                home=fixture.get("home"),
                away=fixture.get("away"),
                kickoff=fixture.get("kickoff"),
                ft_home=fixture.get("ft_home", 0),
                ft_away=fixture.get("ft_away", 0),
                winner=fixture.get("winner"),
                pens_home=fixture.get("pens_home"),
                pens_away=fixture.get("pens_away"),
            )
        return patch_finished(pred, overlay[match_id])
    # Return baked prediction.
    pred = _predictions.get(match_id)
    if pred is not None:
        return pred

    # Check sample fixtures for finished matches known at build time.
    fixtures = get_fixtures()
    fixture = next((f for f in fixtures if f["fixture_id"] == match_id), None)
    if fixture and fixture.get("status") == "finished":
        return finished_prediction(
            match_id=match_id,
            round=fixture.get("round"),
            home=fixture.get("home"),
            away=fixture.get("away"),
            kickoff=fixture.get("kickoff"),
            ft_home=fixture.get("ft_home", 0),
            ft_away=fixture.get("ft_away", 0),
            winner=fixture.get("winner"),
            pens_home=fixture.get("pens_home"),
            pens_away=fixture.get("pens_away"),
        )

    # Unknown match ID or TBD — return a pending card so the UI renders gracefully.
    return {
        "match_id": match_id,
        "round": "R32",
        "home": "Unknown",
        "away": "Unknown",
        "state": "pending",
        "elo_home": 1500,
        "elo_away": 1500,
        "win": 0.0,
        "draw": 0.0,
        "loss": 0.0,
        "predicted_score": "",
        "btts_yes": 0.0,
    }


@app.get("/best-bets")
def get_best_bets():
    overlay = get_overlay()
    finished_ids = {fid for fid, d in overlay.items() if d.get("status") == "finished"}
    return [pick for pick in _best_bets if pick["match_id"] not in finished_ids]


@app.post("/refresh")
@app.get("/refresh")
async def post_refresh(request: Request):
    # Shared-secret auth
    secret = request.headers.get("x-refresh-secret", "")
    if not REFRESH_SECRET or secret != REFRESH_SECRET:
        return JSONResponse(status_code=403, content={"error": "forbidden"})

    from wcpredictor.clients.espn import EspnSource

    source = EspnSource()
    fixtures = source.get_fixtures()
    overlay = get_overlay()
    updated: list[str] = []

    for f in fixtures:
        if f.get("status") == "finished" or f.get("status") == "in_progress":
            eid = f["fixture_id"]
            overlay[eid] = {
                "status": f["status"],
                "ft_home": f.get("ft_home"),
                "ft_away": f.get("ft_away"),
                "pens_home": f.get("pens_home"),
                "pens_away": f.get("pens_away"),
                "winner": f.get("winner"),
            }
            updated.append(eid)

    save_overlay(overlay)
    return {"updated": updated, "resolved": []}


@app.get("/backtest")
def get_backtest():
    return {
        "log_loss_model": 0.0,
        "log_loss_market": 0.0,
        "rps": 0.0,
        "status": "not yet implemented",
    }


# --- SPA serving -----------------------------------------------------------

if (DIST / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")


@app.get("/{full_path:path}")
def _spa(full_path: str):
    if full_path:
        candidate = (DIST / full_path).resolve()
        try:
            candidate.relative_to(DIST.resolve())
        except ValueError:
            return {"error": "forbidden"}
        if candidate.is_file():
            return FileResponse(candidate)
    if (DIST / "index.html").is_file():
        return FileResponse(DIST / "index.html")
    return {"error": "frontend build missing"}
