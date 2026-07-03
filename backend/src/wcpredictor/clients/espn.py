from __future__ import annotations

import os
from datetime import datetime, timezone, timedelta

import httpx

from ..config import canonical

ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world"
TOURNAMENT_START = "20260611"
TOURNAMENT_END = "20260719"

ROUND_MAP: dict[str, str] = {
    "Round of 32": "R32",
    "Rd of 16": "R16",
    "Quarterfinals": "QF",
    "Semifinals": "SF",
    "3rd-Place Match": "3rd",
    "Final": "Final",
}


def _round_from_event(event: dict) -> str:
    note = (event.get("competitions") or [{}])[0].get("altGameNote", "")
    for espn_name, short in ROUND_MAP.items():
        if espn_name in note:
            return short
    if "Group" in note:
        return "Group"
    return "R32"


def _american_to_decimal(american: float) -> float:
    if american < 0:
        return round(1 + 100 / abs(american), 4)
    return round(1 + american / 100, 4)


class EspnSource:
    def __init__(self, start_date: str = TOURNAMENT_START, end_date: str = TOURNAMENT_END):
        self.start_date = start_date
        self.end_date = end_date

    def _fetch_scoreboard(self) -> dict:
        try:
            url = f"{ESPN_BASE}/scoreboard?dates={self.start_date}-{self.end_date}"
            r = httpx.get(url, timeout=30.0)
            r.raise_for_status()
            return r.json()
        except Exception:
            return {}

    def _parse_event(self, ev: dict) -> dict:
        comps = (ev.get("competitions") or [{}])[0]
        competitors = comps.get("competitors", [])
        by_side = {c.get("homeAway"): c for c in competitors}
        home = by_side.get("home", {})
        away = by_side.get("away", {})

        status_type = comps.get("status", {}).get("type", {})
        completed = status_type.get("completed", False)
        state = status_type.get("state", "pre")

        fixture: dict = {
            "fixture_id": str(ev.get("id", "")),
            "home": home.get("team", {}).get("displayName", "TBD"),
            "away": away.get("team", {}).get("displayName", "TBD"),
            "kickoff": ev.get("date", ""),
            "venue": comps.get("venue", {}).get("fullName", ""),
            "round": _round_from_event(ev),
            "status": "finished" if completed else ("in_progress" if state == "in" else "not_started"),
        }

        if completed:
            try:
                fixture["ft_home"] = int(home.get("score", 0))
                fixture["ft_away"] = int(away.get("score", 0))
            except (ValueError, TypeError):
                fixture["ft_home"] = 0
                fixture["ft_away"] = 0

            h_winner = home.get("winner", False)
            a_winner = away.get("winner", False)
            if h_winner:
                fixture["winner"] = "home"
            elif a_winner:
                fixture["winner"] = "away"
            else:
                fixture["winner"] = None

            details = comps.get("details", [])
            pen_h = pen_a = 0
            has_pens = False
            for d in details:
                if d.get("shootout"):
                    has_pens = True
                    for p in d.get("athletes", []):
                        team_side = p.get("team", {}).get("homeAway")
                        converted = int(p.get("converted", 0))
                        if team_side == "home":
                            pen_h += converted
                        elif team_side == "away":
                            pen_a += converted
            if has_pens:
                fixture["pens_home"] = pen_h
                fixture["pens_away"] = pen_a

        return fixture

    def get_fixtures(self, tournament: str = "World Cup 2026") -> list[dict]:
        data = self._fetch_scoreboard()
        events = data.get("events", [])
        return [self._parse_event(ev) for ev in events]

    def get_team_recent(self, team: str, limit: int = 10) -> list[dict]:
        return []

    def get_odds(self, match_id: str) -> dict[str, list[float]] | None:
        data = self._fetch_scoreboard()
        for ev in data.get("events", []):
            if str(ev.get("id", "")) == match_id:
                comps = (ev.get("competitions") or [{}])[0]
                odds_list = comps.get("odds")
                if not odds_list or odds_list[0] is None:
                    return None
                odds = odds_list[0]
                ml_block = odds.get("moneyline")
                if not ml_block or not isinstance(ml_block, dict):
                    return None
                def _parse_close(key: str) -> float | None:
                    side = ml_block.get(key)
                    if not isinstance(side, dict):
                        return None
                    close = side.get("close") or side.get("open", {})
                    odds_str = close.get("odds") if isinstance(close, dict) else None
                    if not odds_str:
                        return None
                    try:
                        american = int(odds_str)
                    except (ValueError, TypeError):
                        return None
                    return _american_to_decimal(american)
                home_ml = _parse_close("home")
                draw_ml = _parse_close("draw")
                away_ml = _parse_close("away")
                if home_ml is None or draw_ml is None or away_ml is None:
                    return None
                result: dict[str, list[float]] = {
                    "h2h": [home_ml, draw_ml, away_ml],
                }
                total_block = odds.get("total")
                if isinstance(total_block, dict):
                    def _parse_total_side(key: str) -> float | None:
                        side = total_block.get(key)
                        if not isinstance(side, dict):
                            return None
                        close = side.get("close") or side.get("open", {})
                        odds_str = close.get("odds") if isinstance(close, dict) else None
                        if not odds_str:
                            return None
                        try:
                            return _american_to_decimal(int(odds_str))
                        except (ValueError, TypeError):
                            return None
                    over_ml = _parse_total_side("over")
                    under_ml = _parse_total_side("under")
                    if over_ml is not None and under_ml is not None:
                        result["ou25"] = [over_ml, under_ml]
                return result
        return None
