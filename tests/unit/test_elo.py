"""Unit tests for International Elo ratings."""

import pandas as pd
from wcpredictor.features.elo import (
    expected,
    g_factor,
    update,
    compute_elo,
    K_BY_TIER,
)


class TestExpected:
    def test_equal_ratings(self):
        assert abs(expected(1500, 1500) - 0.5) < 1e-9

    def test_home_advantage(self):
        e = expected(1500, 1500, h_adj=80)
        assert e > 0.5

    def test_stronger_team(self):
        e = expected(2000, 1500)
        assert e > 0.9


class TestGFactor:
    def test_one_goal_diff(self):
        assert abs(g_factor(1) - 1.2) < 1e-9

    def test_cap_at_five(self):
        assert g_factor(100) == 5.0

    def test_negative_diff(self):
        assert abs(g_factor(-3) - 1.4) < 1e-9


class TestUpdate:
    def test_winner_gains_elo(self):
        na, nb = update(1500, 1500, 1.0, 2, 30)
        assert na > 1500
        assert nb < 1500

    def test_draw_small_change(self):
        na, nb = update(1500, 1500, 0.5, 0, 30)
        assert abs(na - 1500) < 1
        assert abs(nb - 1500) < 1


class TestComputeElo:
    def test_simple_match(self):
        df = pd.DataFrame([
            {"date": "2024-01-01", "home": "Spain", "away": "Australia",
             "home_goals": 3, "away_goals": 0, "tournament": "Friendly", "neutral": False},
        ])
        rating, _ = compute_elo(df)
        assert rating["Spain"] > 1500
        assert rating["Australia"] < 1500

    def test_tier_k_values(self):
        assert K_BY_TIER["friendly"] == 20.0
        assert K_BY_TIER["wc"] == 50.0
        assert K_BY_TIER["qualifier"] == 30.0

    def test_history_length(self):
        df = pd.DataFrame([
            {"date": "2024-01-01", "home": "A", "away": "B",
             "home_goals": 1, "away_goals": 0, "tournament": "Friendly", "neutral": False},
            {"date": "2024-01-02", "home": "C", "away": "D",
             "home_goals": 0, "away_goals": 0, "tournament": "WC", "neutral": True},
        ])
        _, history = compute_elo(df)
        assert len(history) == 2
