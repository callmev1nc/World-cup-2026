"""Build-time precompute: run the engine once per fixture, dump static JSON.
Installed by scripts/vercel_build.sh before the SPA build. Requires the
build-requirements.txt deps (pandas/scipy/numpy/httpx/pydantic).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from wcpredictor.clients.sample import SampleSource
from wcpredictor.pipeline import predict, list_matches, refresh
from wcpredictor.schemas import Prediction

DATA = Path(__file__).parents[2] / "data"
PROCESSED = DATA / "processed"
SAMPLE_FILE = DATA / "raw" / "sample" / "spain_aus.json"


def main() -> None:
    source = SampleSource(SAMPLE_FILE)

    # Step 1: apply the current overlay + bracket resolution so any slots
    # already resolved at build time get baked into the precomputed data.
    refresh(source, feed=None)

    # Step 2: precompute predictions for every non-TBD, non-finished fixture
    fixtures = source.get_fixtures()
    predictions: dict[str, dict] = {}
    for f in fixtures:
        fid: str = f["fixture_id"]
        if f.get("tbd"):
            continue
        if f.get("status") == "finished":
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

    # Step 3: build best_bets the same way api.py does
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

    # Step 4: build matches list from list_matches output
    matches = [ms.model_dump(mode="json") for ms in list_matches(source)]

    # Step 5: write processed JSON files
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
