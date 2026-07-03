from typing import Protocol
from datetime import datetime


class Source(Protocol):
    def get_fixtures(self, tournament: str = "World Cup 2026") -> list[dict]:
        ...

    def get_team_recent(self, team: str, limit: int = 10) -> list[dict]:
        ...

    def get_odds(self, match_id: str) -> dict[str, list[float]] | None:
        ...
