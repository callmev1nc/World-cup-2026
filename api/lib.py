"""Pure-stdlib helpers for the slim serverless function.
No imports from wcpredictor.pipeline — that would pull pandas/scipy at module
load and defeat the whole point of the build-time precompute.
"""
import json
import os
from pathlib import Path

import httpx

BASE = Path(__file__).parent.parent

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")


def _supabase_headers() -> dict[str, str]:
    return {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }


def get_overlay() -> dict:
    """Read overlay from Supabase wc_results table. Falls back to {} on error or missing env."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return {}
    try:
        url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/wc_results"
        r = httpx.get(url, headers=_supabase_headers(), timeout=10.0)
        r.raise_for_status()
        rows = r.json()
        overlay: dict = {}
        for row in rows:
            eid = row.get("event_id")
            if not eid:
                continue
            entry: dict = {"status": row.get("status", "not_started")}
            if row.get("ft_home") is not None:
                entry["ft_home"] = row["ft_home"]
            if row.get("ft_away") is not None:
                entry["ft_away"] = row["ft_away"]
            if row.get("pens_home") is not None:
                entry["pens_home"] = row["pens_home"]
            if row.get("pens_away") is not None:
                entry["pens_away"] = row["pens_away"]
            if row.get("winner"):
                entry["winner"] = row["winner"]
            overlay[eid] = entry
        return overlay
    except Exception:
        return {}


def save_overlay(overlay: dict) -> None:
    """Upsert overlay rows into Supabase wc_results table. No-op if env unset."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return
    try:
        url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/wc_results"
        for event_id, data in overlay.items():
            status = data.get("status", "not_started")
            body = {
                "event_id": event_id,
                "status": status,
                "ft_home": data.get("ft_home"),
                "ft_away": data.get("ft_away"),
                "pens_home": data.get("pens_home"),
                "pens_away": data.get("pens_away"),
                "winner": data.get("winner"),
            }
            r = httpx.post(
                url,
                headers={**_supabase_headers(), "Prefer": "resolution=merge-duplicates"},
                json=body,
                timeout=10.0,
            )
            r.raise_for_status()
    except Exception:
        pass


def get_fixtures() -> list[dict]:
    """Load sample fixtures + apply overlay (pure dict logic)."""
    SAMPLE_PATH = BASE / "data" / "raw" / "sample" / "spain_aus.json"
    raw: dict = dict(load_json(SAMPLE_PATH)) if SAMPLE_PATH.exists() else {}
    base = [dict(f) for f in raw.get("fixtures", [])]
    overlay = get_overlay()
    for f in base:
        f.update(overlay.get(f["fixture_id"], {}))
    return base


def load_json(path: Path) -> dict | list:
    return json.loads(path.read_text()) if path.exists() else {}


def merge_matches(baked: list[dict], overlay: dict, predictions: dict) -> list[dict]:
    """Merge live overlay (Supabase) and baked predictions onto the matches list.

    Overlay wins when present (live). Otherwise, for finished matches with no
    overlay, backfill actual_score/result/pens from the baked prediction so the
    no-Supabase fallback path still shows scores.
    """
    merged: list[dict] = []
    for m in baked:
        mid = m["match_id"]
        ov = overlay.get(mid)
        if ov and ov.get("status") == "finished":
            m = {**m, "state": "finished"}
            if "ft_home" in ov and "ft_away" in ov:
                m["actual_score"] = f"{ov['ft_home']}-{ov['ft_away']}"
            if ov.get("winner"):
                m["result"] = ov["winner"]
            if ov.get("pens_home") is not None and ov.get("pens_away") is not None:
                m["pens"] = {"score": f"{ov['pens_home']}-{ov['pens_away']}", "winner": ov.get("winner")}
        elif m.get("state") == "finished" and mid in predictions:
            p = predictions[mid]
            if p.get("actual_score"):
                m = {**m, "actual_score": p["actual_score"]}
            if p.get("result"):
                m = {**m, "result": p["result"]}
            if p.get("pens"):
                m = {**m, "pens": p["pens"]}
        merged.append(m)
    return merged


def patch_finished(pred: dict, fixture: dict) -> dict:
    """If the fixture overlay marks this match as finished, patch the
    precomputed prediction with the real result."""
    if fixture.get("status") != "finished":
        return pred
    actual: str | None = None
    if "ft_home" in fixture and "ft_away" in fixture:
        actual = f"{fixture['ft_home']}-{fixture['ft_away']}"
    update: dict = {
        "state": "finished",
        "result": fixture.get("winner"),
        "actual_score": actual,
    }
    if "pens_home" in fixture and "pens_away" in fixture:
        update["pens"] = {
            "score": f"{fixture['pens_home']}-{fixture['pens_away']}",
            "winner": fixture.get("winner"),
        }
    return {**pred, **update}
