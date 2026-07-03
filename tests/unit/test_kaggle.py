"""Tests for the Kaggle international-results loader."""
from wcpredictor.clients.kaggle import (
    load_international_results,
    results_for_teams,
    tier_for,
)

_CSV = (
    "date,home_team,away_team,home_score,away_score,tournament,city,country,neutral\n"
    "2024-01-01,Spain,France,2,1,Friendly,Madrid,Spain,False\n"
    "2024-02-01,Spain,Portugal,1,1,UEFA Euro,Lisbon,Portugal,True\n"
    "2026-03-01,Brazil,Argentina,3,0,FIFA World Cup,Rio,Brazil,True\n"
    "2025-09-01,Germany,Italy,0,0,UEFA Nations League,Berlin,Germany,False\n"
)


def test_returns_empty_when_absent(tmp_path):
    assert load_international_results(tmp_path / "missing.csv") == []


def test_results_for_teams_empty_when_no_history():
    assert results_for_teams(["Spain"], history=[]) == []


def test_load_parses_and_tiers(tmp_path):
    p = tmp_path / "results.csv"
    p.write_text(_CSV, encoding="utf-8")
    rows = load_international_results(p)
    assert len(rows) == 4

    spain_fra = next(r for r in rows if r["home"] == "Spain" and r["away"] == "France")
    assert spain_fra["hs"] == 2 and spain_fra["as"] == 1
    assert spain_fra["tier"] == "friendly"
    assert spain_fra["neutral"] is False

    euro = next(r for r in rows if r["away"] == "Portugal")
    assert euro["tier"] == "continental"
    assert euro["neutral"] is True

    wc = next(r for r in rows if r["home"] == "Brazil")
    assert wc["tier"] == "wc"

    nations = next(r for r in rows if r["home"] == "Germany")
    assert nations["tier"] == "nations_league"


def test_results_for_teams_filters_to_requested_teams(tmp_path):
    p = tmp_path / "results.csv"
    p.write_text(_CSV, encoding="utf-8")
    history = load_international_results(p)
    sel = results_for_teams(["Spain"], history=history)
    assert all((r["home"] == "Spain" or r["away"] == "Spain") for r in sel)
    assert len(sel) == 2


def test_tier_for_unknown_defaults_friendly():
    assert tier_for("Some New Invitational") == "friendly"
