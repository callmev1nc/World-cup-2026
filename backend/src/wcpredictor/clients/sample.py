import json
from pathlib import Path

DATA_DIR = Path(__file__).parents[4] / "data" / "raw" / "sample"
STATE_FILE = Path(__file__).parents[4] / "data" / "state" / "results.json"


class SampleSource:
    def __init__(self, path: Path | None = None):
        self.path = path or DATA_DIR / "spain_aus.json"
        with open(self.path) as f:
            self._data = json.load(f)

    def get_fixtures(self, tournament: str = "World Cup 2026") -> list[dict]:
        base = [dict(f) for f in self._data["fixtures"]]
        if STATE_FILE.exists():
            ov = json.loads(STATE_FILE.read_text())
            for f in base:
                f.update(ov.get(f["fixture_id"], {}))
        return base

    def get_team_recent(self, team: str, limit: int = 10) -> list[dict]:
        results = self._data["recent_results"].get(team, [])
        return results[:limit]

    def get_odds(self, match_id: str) -> dict[str, list[float]] | None:
        return self._data["odds"].get(match_id)
