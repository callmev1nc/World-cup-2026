"""Tests for SampleSource data client."""

from wcpredictor.clients.sample import SampleSource


def test_get_fixtures():
    src = SampleSource()
    fixtures = src.get_fixtures()
    assert len(fixtures) >= 1
    assert fixtures[0]["fixture_id"] == "spain-aut"


def test_get_team_recent():
    src = SampleSource()
    results = src.get_team_recent("Spain")
    assert len(results) >= 1


def test_get_odds():
    src = SampleSource()
    odds = src.get_odds("spain-aut")
    assert "h2h" in odds
    assert odds["h2h"][0] == 1.70
