"""Backtest metrics and quality gate.

Honest status: a full backtest needs (a) a historical results dataset with
known outcomes and (b) closing odds for a baseline. The plan's design is:
train on matches with date <= 2026-06-25, test frozen = the 16 already-played
R32 matches, evaluate against Shin-devigged closing odds. Drop
data/raw/kaggle/results.csv in to enable it.

This module provides the metric functions + the quality gate so they are
unit-testable on synthetic inputs without any dataset:

  GATE: fail if log_loss_model > log_loss_market_baseline + tol   (tol = 0.02)

The market is a strong baseline; a model that loses to it by more than `tol`
should increase its market-blend weight rather than ship.
"""
from __future__ import annotations

import numpy as np


def rps(probs: list[list[float]], actual_idx: list[int]) -> float:
    """Ranked Probability Score for 3-way outcomes (lower is better; 0 = perfect).

    probs[i] = [p_home, p_draw, p_away]; actual_idx[i] in {0, 1, 2}.
    """
    if not probs:
        return 0.0
    total = 0.0
    for p, a in zip(probs, actual_idx):
        cum_p = np.cumsum(p)
        cum_a = np.cumsum([1.0 if i == a else 0.0 for i in range(3)])
        total += float(np.sum((cum_p - cum_a) ** 2))
    return total / len(probs)


def gate(log_loss_model: float, log_loss_market: float, tol: float = 0.02) -> bool:
    """True if the model is NOT materially worse than the devigged market baseline."""
    return log_loss_model <= log_loss_market + tol


def evaluate(
    probs: list[list[float]],
    actual_idx: list[int],
    market_probs: list[list[float]] | None = None,
) -> dict:
    """Compute model (and optional market) scoring metrics + the gate verdict."""
    from sklearn.metrics import log_loss

    out: dict = {
        "log_loss_model": float(log_loss(actual_idx, probs, labels=[0, 1, 2])),
        "rps_model": rps(probs, actual_idx),
    }
    if market_probs is not None:
        out["log_loss_market"] = float(log_loss(actual_idx, market_probs, labels=[0, 1, 2]))
        out["rps_market"] = rps(market_probs, actual_idx)
        out["passes_gate"] = gate(out["log_loss_model"], out["log_loss_market"])
    return out
