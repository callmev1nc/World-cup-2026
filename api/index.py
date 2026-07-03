"""Vercel serverless entry (single function).
Serves precomputed prediction JSON + the built SPA. No heavy imports
(pandas/scipy/numpy run only at build time in backend/scripts/precompute.py).

    /api/matches      -> static precomputed matches list
    /api/predict/{id} -> static prediction (patched if overlay says finished)
    /api/best-bets    -> top 8 +EV picks (filtered to drop finished)
    /api/refresh      -> fetch ESPN results + resolve bracket (pure dict/httpx)
    /*                -> SPA (frontend/dist), index.html fallback

vercel.json bundles frontend/dist + data/processed + data/raw/sample + data/state.
"""
import json
import sys
from pathlib import Path

_PATH = Path(__file__).parent
sys.path.insert(0, str(_PATH.parent / "backend" / "src"))
sys.path.insert(0, str(_PATH))

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from lib import get_fixtures, get_overlay, save_overlay, patch_finished

DIST = Path(__file__).parent.parent / "frontend" / "dist"
PROCESSED = Path(__file__).parent.parent / "data" / "processed"

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
    return _matches


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
            pred = {
                "match_id": match_id,
                "round": fixture.get("round", "R32"),
                "home": fixture.get("home", "Unknown"),
                "away": fixture.get("away", "Unknown"),
                "kickoff": fixture.get("kickoff"),
                "state": "finished",
                "elo_home": 1500,
                "elo_away": 1500,
                "win": 0.0,
                "draw": 0.0,
                "loss": 0.0,
                "predicted_score": "",
                "btts_yes": 0.0,
            }
        return patch_finished(pred, overlay[match_id])
    # Return baked prediction.
    pred = _predictions.get(match_id)
    if pred is not None:
        return pred

    # Check sample fixtures for finished matches known at build time.
    fixtures = get_fixtures()
    fixture = next((f for f in fixtures if f["fixture_id"] == match_id), None)
    if fixture and fixture.get("status") == "finished":
        actual = None
        if "ft_home" in fixture and "ft_away" in fixture:
            actual = f"{fixture['ft_home']}-{fixture['ft_away']}"
        result = {
            "match_id": match_id,
            "round": fixture.get("round", "R32"),
            "home": fixture.get("home", "Unknown"),
            "away": fixture.get("away", "Unknown"),
            "kickoff": fixture.get("kickoff"),
            "state": "finished",
            "elo_home": 1500,
            "elo_away": 1500,
            "win": 0.0,
            "draw": 0.0,
            "loss": 0.0,
            "predicted_score": "",
            "btts_yes": 0.0,
            "actual_score": actual,
            "result": fixture.get("winner"),
        }
        if "pens_home" in fixture and "pens_away" in fixture:
            result["pens"] = {
                "score": f"{fixture['pens_home']}-{fixture['pens_away']}",
                "winner": fixture.get("winner"),
            }
        return result

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
def get_refresh():
    from wcpredictor.config import canonical
    from wcpredictor.models.bracket import resolve as resolve_bracket
    from wcpredictor.clients.results import fetch_finished

    overlay = get_overlay()
    fixtures = get_fixtures()
    updated: list[str] = []

    # Fetch finished matches from ESPN and merge into overlay.
    feed = fetch_finished()
    for key, res in feed.items():
        parts = key.split("-", 1)
        rev = f"{parts[1]}-{parts[0]}" if len(parts) == 2 else ""
        for f in fixtures:
            if f.get("tbd") or f.get("status") == "finished":
                continue
            k = f"{canonical(f['home'])}-{canonical(f['away'])}"
            if k == key or (rev and k == rev):
                f.update({"status": "finished", **res})
                overlay[f["fixture_id"]] = {"status": "finished", **res}
                updated.append(f["fixture_id"])
                break

    # Resolve bracket TBD slots based on finished results.
    resolved = resolve_bracket(fixtures)
    for fid in resolved:
        f = next(x for x in fixtures if x["fixture_id"] == fid)
        overlay[fid] = {k: f[k] for k in ("home", "away", "tbd") if k in f}

    save_overlay(overlay)
    return {"updated": updated, "resolved": resolved}


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
        # Resolve and confirm the file is INSIDE dist (prevent ../ path traversal).
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
