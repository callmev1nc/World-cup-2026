from __future__ import annotations
import os, httpx
from datetime import datetime
from ..config import canonical

ESPN_SLUGS = ["fifa.world.cup", "fifa.world"]

def _espn() -> dict:
    for slug in ESPN_SLUGS:
        try:
            url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{slug}/scoreboard"
            data = httpx.get(url, timeout=20.0).json()
            if data.get("events"):
                return data
        except Exception:
            continue
    return {}

def fetch_finished() -> dict:
    """Return {fixture_key: {ft_home, ft_away, pens_home, pens_away, winner}}
    for finished WC matches. Best-effort; {} on any failure."""
    if os.getenv("API_FOOTBALL_KEY"):
        try:
            from .api_football import ApiFootballClient
        except Exception:
            pass
    out: dict = {}
    data = _espn()
    for ev in data.get("events", []):
        if ev.get("status", {}).get("type", {}).get("name") != "STATUS_FINAL":
            continue
        comps = ev.get("competitions", [{}])[0].get("competitors", [])
        if len(comps) < 2:
            continue
        by = {c.get("homeAway"): c for c in comps}
        h, a = by.get("home"), by.get("away")
        if not h or not a:
            continue
        hs, as_ = int(h["score"]), int(a["score"])
        key = f"{canonical(h['team']['displayName'])}-{canonical(a['team']['displayName'])}"
        winner = "home" if hs > as_ else ("away" if as_ > hs else None)
        out[key] = {"ft_home": hs, "ft_away": as_, "winner": winner}
    return out
