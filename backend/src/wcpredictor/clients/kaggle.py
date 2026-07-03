"""Load historical international results.

Canonical source: Kaggle `martj42/international-football-results` (1872-present).
Download the CSV and place it at data/raw/kaggle/results.csv — this becomes the
trusted base for international Elo + Dixon-Coles training (the single biggest
prediction-quality lever; the bundled sample only has a handful of friendlies).

Gracefully returns [] when the file is absent, so the app still runs on sample
data until the CSV is dropped in.
"""
from __future__ import annotations

import csv
from pathlib import Path

import httpx

from ..config import TOURNAMENT_TIER, canonical

DATA_FILE = Path(__file__).parents[4] / "data" / "raw" / "kaggle" / "results.csv"
_CACHE: list[dict] | None = None

RESULTS_URL = "https://raw.githubusercontent.com/martj42/international_results/master/results.csv"
GOALSCORERS_URL = "https://raw.githubusercontent.com/martj42/international_results/master/goalscorers.csv"
_GOALS_CACHE: list[dict] | None = None

DATA_DIR = DATA_FILE.parent


def _ensure(filename: str, url: str) -> Path | None:
    """Download a CSV into DATA_DIR on first use. Returns path or None on failure."""
    p = DATA_DIR / filename
    if p.exists():
        return p
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        r = httpx.get(url, timeout=90.0, follow_redirects=True)
        r.raise_for_status()
        p.write_bytes(r.content)
        return p
    except Exception:
        return None


def tier_for(tournament: str) -> str:
    """Map a raw tournament name to an Elo K-factor tier."""
    t = (tournament or "").strip()
    if t in TOURNAMENT_TIER:
        return TOURNAMENT_TIER[t]
    low = t.lower()
    if "friendly" in low:
        return "friendly"
    if "qualif" in low:
        return "qualifier"
    if "nations league" in low:
        return "nations_league"
    if "world cup" in low:
        return "wc"
    if any(c in low for c in ("euro", "copa", "cup of nations", "asian cup", "gold cup", "nations cup", "confederations")):
        return "continental"
    return "friendly"


def load_international_results(path: Path | None = None) -> list[dict]:
    """Return normalized match dicts: {date, home, away, hs, as, tier, neutral}.

    Empty list if the CSV is absent. Caches the default-path load.
    """
    global _CACHE
    if path is None and _CACHE is not None:
        return _CACHE
    p = path if path is not None else _ensure("results.csv", RESULTS_URL)
    if p is None or not p.exists():
        return []
    rows: list[dict] = []
    with open(p, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            try:
                rows.append({
                    "date": r["date"],
                    "home": r["home_team"],
                    "away": r["away_team"],
                    "hs": int(r["home_score"]),
                    "as": int(r["away_score"]),
                    "tier": tier_for(r.get("tournament", "")),
                    "neutral": str(r.get("neutral", "False")).lower() in ("true", "1", "yes"),
                })
            except (KeyError, ValueError):
                continue
    if path is None:
        _CACHE = rows
    return rows


def load_goalscorers(path: Path | None = None) -> list[dict]:
    global _GOALS_CACHE
    if path is None and _GOALS_CACHE is not None:
        return _GOALS_CACHE
    p = path if path is not None else _ensure("goalscorers.csv", GOALSCORERS_URL)
    if p is None or not p.exists():
        return []
    rows = []
    with open(p, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append({
                "date": r.get("date", ""), "team": r.get("team", ""),
                "scorer": r.get("scorer", ""),
                "own_goal": str(r.get("own_goal", "False")).lower() in ("true", "1"),
                "penalty": str(r.get("penalty", "False")).lower() in ("true", "1"),
            })
    if path is None:
        _GOALS_CACHE = rows
    return rows


def results_for_teams(
    teams: list[str], history: list[dict] | None = None, limit_per_team: int = 40
) -> list[dict]:
    """Recent matches involving any of the given teams (for Elo/DC training)."""
    hist = history if history is not None else load_international_results()
    if not hist:
        return []
    wanted = {canonical(t) for t in teams}
    sel = [r for r in hist if canonical(r["home"]) in wanted or canonical(r["away"]) in wanted]
    sel.sort(key=lambda x: x["date"])
    cap = max(limit_per_team * len(teams), 1)
    return sel[-cap:]


def goalscorers_for_team(team: str, since: str = "2024-01-01", top_n: int = 3) -> list[dict]:
    rows = load_goalscorers()
    if not rows:
        return []
    want = canonical(team)
    counts: dict[str, int] = {}
    for r in rows:
        if r["date"] < since or r["own_goal"]:
            continue
        if canonical(r["team"]) == want:
            counts[r["scorer"]] = counts.get(r["scorer"], 0) + 1
    top = sorted(counts.items(), key=lambda x: -x[1])[:top_n]
    return [{"name": s, "goals": g} for s, g in top]
