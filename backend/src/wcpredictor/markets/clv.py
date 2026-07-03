"""Closing Line Value (CLV) — the real quality metric for a value-betting process.

CLV compares the odds you bet at to the closing (efficient) odds. Beating the
close consistently predicts long-run profit better than hit-rate does.
"""
from __future__ import annotations


def clv_prob(bet_odds: float, closing_odds: float) -> float:
    """CLV in probability space: implied(close) - implied(bet).

    Positive => you beat the closing line. Example: bet 2.50, close 2.30 => +0.0348.
    """
    return (1.0 / closing_odds) - (1.0 / bet_odds)


def clv_pct(bet_odds: float, closing_odds: float) -> float:
    """CLV in odds-ratio form: (bet_odds / closing_odds) - 1.

    Example: bet 2.50, close 2.30 => +8.7%.
    """
    return (bet_odds / closing_odds) - 1.0
