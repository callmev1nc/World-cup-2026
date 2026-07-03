"""Pure-stdlib helpers for the slim serverless function.
No imports from wcpredictor.pipeline — that would pull pandas/scipy at module
load and defeat the whole point of the build-time precompute.
"""
import json
import os
from pathlib import Path

BASE = Path(__file__).parent.parent
SAMPLE_PATH = BASE / "data" / "raw" / "sample" / "spain_aus.json"

# Vercel's deployed bundle is read-only; only /tmp is writable. Use it for the
# runtime overlay so /refresh doesn't crash. (Per-instance + ephemeral — see notes.)
if os.getenv("VERCEL"):
    STATE_FILE = Path("/tmp") / "wc_results_overlay.json"
else:
    STATE_FILE = BASE / "data" / "state" / "results.json"


def load_json(path: Path) -> dict | list:
    return json.loads(path.read_text()) if path.exists() else {}


def get_overlay() -> dict:
    return dict(load_json(STATE_FILE))


def save_overlay(overlay: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(overlay, indent=2, default=str))


def get_fixtures() -> list[dict]:
    """Load sample fixtures + apply overlay (pure dict logic)."""
    raw: dict = dict(load_json(SAMPLE_PATH))
    base = [dict(f) for f in raw.get("fixtures", [])]
    overlay = get_overlay()
    for f in base:
        f.update(overlay.get(f["fixture_id"], {}))
    return base


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
