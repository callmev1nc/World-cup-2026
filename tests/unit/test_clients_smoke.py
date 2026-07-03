"""Smoke tests: live API clients import and guard their keys without network."""
import pytest

from wcpredictor.clients.api_football import ApiFootballClient, DAILY_LIMIT
from wcpredictor.clients.odds_api import OddsApiClient


def test_api_football_imports_and_budget_is_below_free_tier():
    # The hard cap must leave headroom under the 100/day free tier.
    assert DAILY_LIMIT < 100


def test_api_football_requires_key(monkeypatch):
    monkeypatch.delenv("API_FOOTBALL_KEY", raising=False)
    with pytest.raises(RuntimeError):
        ApiFootballClient()


def test_odds_api_requires_key(monkeypatch):
    monkeypatch.delenv("ODDS_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        OddsApiClient()
