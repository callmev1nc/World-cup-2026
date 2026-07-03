"""The Odds API client — pre-match multi-bookmaker odds.

Free tier: 500 credits/month. Cost = 1 credit per (bookmaker x market) returned
per call. The cheapest useful call is sport=soccer_fifa_world_cup,
regions=us, markets=h2h (~6 credits). NEVER request spreads/totals/extra
regions casually — each multiplies cost.

`h2h` for soccer settles 90 minutes (excludes extra time + penalties); that is
the market our 1X2 model probabilities compare against.
"""
from __future__ import annotations

import os
from pathlib import Path

import httpx
from diskcache import Cache

BASE = "https://api.the-odds-api.com/v4"
SPORT = "soccer_fifa_world_cup"
CACHE_DIR = Path(__file__).parents[4] / "cache" / "odds_api"
_CACHE = Cache(str(CACHE_DIR))


class OddsApiClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("ODDS_API_KEY", "")
        if not self.api_key:
            raise RuntimeError(
                "ODDS_API_KEY not set. Get a free key at https://the-odds-api.com/"
            )

    def get_odds(
        self,
        regions: str = "us",
        markets: str = "h2h",
        odds_format: str = "decimal",
        ttl: int = 3600,
    ) -> list[dict]:
        params = {
            "apiKey": self.api_key,
            "regions": regions,
            "markets": markets,
            "oddsFormat": odds_format,
        }
        key = ("odds", regions, markets, odds_format)
        cached = _CACHE.get(key)
        if cached is not None:
            return cached
        r = httpx.get(f"{BASE}/sports/{SPORT}/odds", params=params, timeout=20)
        r.raise_for_status()
        data = r.json()
        _CACHE.set(key, data, expire=ttl)
        return data
