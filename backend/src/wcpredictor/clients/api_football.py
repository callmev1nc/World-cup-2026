"""API-Football v3 client — fixtures, lineups, injuries, statistics (corners).

Free tier: 100 requests/day, 10/min, all endpoints. Sign up DIRECTLY at
https://www.api-football.com/ (NOT via RapidAPI, which caps lower).

Budget guards (the free tier's biggest risk is exhaustion):
  * per-call diskcache TTL          -> repeated calls are free
  * SQLite daily quota counter      -> hard-fails at DAILY_LIMIT (80) to leave headroom
  * client-side 10/min token bucket -> never trips the rate limit

No key is needed to import the module; constructing the client without a key
raises a clear error so the app can fall back to the SampleSource.
"""
from __future__ import annotations

import os
import sqlite3
import time
from datetime import date, datetime, timezone
from pathlib import Path

import httpx
from diskcache import Cache

BASE = "https://v3.football.api-sports.io"
CACHE_DIR = Path(__file__).parents[4] / "cache" / "api_football"
DAILY_LIMIT = 80           # hard cap below the 100/day free tier (headroom for retries)
RATE_PER_MIN = 10
YEAR = 365 * 24 * 3600

_CACHE = Cache(str(CACHE_DIR))
_QDB = sqlite3.connect(str(CACHE_DIR / "quota.db"), check_same_thread=False)
_QDB.execute("CREATE TABLE IF NOT EXISTS quota (day TEXT PRIMARY KEY, used INTEGER)")
_QDB.commit()


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _quota_used() -> int:
    row = _QDB.execute("SELECT used FROM quota WHERE day=?", (_today(),)).fetchone()
    return int(row[0]) if row else 0


def _quota_inc() -> None:
    today = _today()
    _QDB.execute("INSERT OR IGNORE INTO quota(day, used) VALUES(?,0)", (today,))
    _QDB.execute("UPDATE quota SET used = used + 1 WHERE day=?", (today,))
    _QDB.commit()


def _enforce_budget() -> None:
    if _quota_used() >= DAILY_LIMIT:
        raise RuntimeError(
            f"API-Football daily cap reached ({DAILY_LIMIT}/day). "
            "Wait for UTC midnight or raise DAILY_LIMIT."
        )


_last_calls: list[float] = []


def _rate_limit() -> None:
    global _last_calls
    now = time.time()
    _last_calls = [t for t in _last_calls if now - t < 60]
    if len(_last_calls) >= RATE_PER_MIN:
        time.sleep(max(60 - (now - _last_calls[0]) + 0.05, 0.0))
    _last_calls.append(time.time())


class ApiFootballClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("API_FOOTBALL_KEY", "")
        if not self.api_key:
            raise RuntimeError(
                "API_FOOTBALL_KEY not set. Get a free key at https://www.api-football.com/"
            )

    def _get(self, path: str, params: dict, ttl: int) -> dict:
        _enforce_budget()
        key = (path, tuple(sorted(params.items())))
        cached = _CACHE.get(key)
        if cached is not None:
            return cached
        _rate_limit()
        r = httpx.get(
            BASE + path,
            params=params,
            headers={"x-apisports-key": self.api_key},
            timeout=20,
        )
        _quota_inc()
        r.raise_for_status()
        data = r.json().get("response", [])
        _CACHE.set(key, data, expire=ttl if ttl > 0 else YEAR)
        return data

    # league=1 is the FIFA World Cup in API-Football's competition index.
    def get_fixtures(self, league: int = 1, season: int = 2026) -> list[dict]:
        return self._get("/fixtures", {"league": league, "season": season}, ttl=3600)

    def get_team_recent(self, team_id: int, last: int = 10) -> list[dict]:
        return self._get("/fixtures", {"team": team_id, "last": last}, ttl=86400)

    def get_statistics(self, fixture_id: int) -> list[dict]:
        # Immutable post-match -> cache essentially forever. (Corner Kick counts live here.)
        return self._get("/fixtures/statistics", {"fixture": fixture_id}, ttl=YEAR)

    def get_injuries(
        self, fixture_id: int | None = None, team: int | None = None, day: date | None = None
    ) -> list[dict]:
        params: dict = {}
        if fixture_id is not None:
            params["fixture"] = fixture_id
        if team is not None:
            params["team"] = team
        if day is not None:
            params["date"] = day.isoformat()
        return self._get("/injuries", params, ttl=21600)

    def get_head_to_head(self, team_a: int, team_b: int) -> list[dict]:
        return self._get("/fixtures/headtohead", {"h2h": f"{team_a}-{team_b}"}, ttl=604800)
