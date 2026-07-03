"""Build-time precompute: run the engine once per fixture, dump static JSON.
Installed by scripts/vercel_build.sh before the SPA build. Requires the
build-requirements.txt deps (pandas/scipy/numpy/httpx/pydantic).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from wcpredictor.clients.espn import EspnSource
from wcpredictor.clients.sample import SampleSource
from wcpredictor.pipeline import predict, list_matches
from wcpredictor.schemas import Prediction, finished_prediction

DATA = Path(__file__).parents[2] / "data"
PROCESSED = DATA / "processed"


def main() -> None:
    # Try ESPN first; fall back to sample data for dev/offline.
    try:
        source = EspnSource()
        fixtures = source.get_fixtures()
        if not fixtures:
            raise ValueError("empty ESPN response")
        print(f"  source: ESPN ({len(fixtures)} fixtures)")
    except Exception as e:
        print(f"  ESPN unavailable ({e}), falling back to SampleSource")
        source = SampleSource()
        fixtures = source.get_fixtures()

    # Step 1: precompute predictions for every non-TBD, non-finished fixture
    predictions: dict[str, dict] = {}
    for f in fixtures:
        fid: str = f["fixture_id"]
        if f.get("tbd"):
            continue
        if f.get("status") == "finished":
            from datetime import datetime
            kickoff = datetime.fromisoformat(f["kickoff"]) if f.get("kickoff") else None
            predictions[fid] = finished_prediction(
                match_id=fid,
                round=f.get("round", "R32"),
                home=f.get("home"),
                away=f.get("away"),
                kickoff=kickoff,
                ft_home=f.get("ft_home", 0),
                ft_away=f.get("ft_away", 0),
                winner=f.get("winner"),
                pens_home=f.get("pens_home"),
                pens_away=f.get("pens_away"),
            )
            print(f"  baked finished {fid}: {f.get('home')} vs {f.get('away')}")
            continue
        from datetime import datetime
        kickoff = datetime.fromisoformat(f["kickoff"]) if f.get("kickoff") else None
        try:
            pred = predict(
                source,
                f["home"],
                f["away"],
                match_id=fid,
                round_str=f["round"],
                kickoff=kickoff,
            )
            predictions[fid] = pred.model_dump(mode="json")
            print(f"  precomputed {fid}: {f['home']} vs {f['away']}")
        except Exception as e:
            print(f"  SKIP {fid}: {e}")

    # Step 2: build best_bets the same way api.py does
    picks: list[dict] = []
    for fid, pred in predictions.items():
        fixture = next((f for f in fixtures if f["fixture_id"] == fid), {})
        for vb in pred.get("value_bets", []):
            picks.append({
                "match_id": fid,
                "home": fixture.get("home", ""),
                "away": fixture.get("away", ""),
                "round": fixture.get("round", ""),
                **vb,
            })
    picks.sort(key=lambda v: v["edge"], reverse=True)
    best_bets = picks[:8]

    # Step 3: build matches list from list_matches output
    matches = [ms.model_dump(mode="json") for ms in list_matches(source)]

    # Step 4: write processed JSON files
    PROCESSED.mkdir(parents=True, exist_ok=True)
    for name, data in [
        ("predictions.json", predictions),
        ("best_bets.json", best_bets),
        ("matches.json", matches),
    ]:
        path = PROCESSED / name
        path.write_text(json.dumps(data, indent=2, default=str))
        print(f"  wrote {path} ({len(data) if isinstance(data, dict) else len(data)} entries)")


if __name__ == "__main__":
    main()
