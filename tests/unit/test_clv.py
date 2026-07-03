"""Tests for Closing Line Value."""
import pytest

from wcpredictor.markets.clv import clv_pct, clv_prob


def test_clv_prob_positive_when_beat_close():
    # bet 2.50 (implied .40), close 2.30 (implied .4348) => +0.0348
    assert clv_prob(2.50, 2.30) == pytest.approx(0.03478, abs=1e-4)


def test_clv_pct_positive_when_beat_close():
    # bet 2.50 / close 2.30 - 1 => +8.7%
    assert clv_pct(2.50, 2.30) == pytest.approx(0.08696, abs=1e-4)


def test_clv_negative_when_close_drifts_shorter():
    assert clv_pct(2.30, 2.50) < 0
