"""Blend model probabilities with devigged bookmaker probabilities.

The market is a strong prior — your model's edge is at the margins, so the
optimal weight on the model (alpha) is usually ~0.3-0.5, tuned on a
TimeSeriesSplit validation set. We default to 0.4.
"""
from __future__ import annotations


def blend(model_probs: list[float], market_probs: list[float], alpha: float = 0.4) -> list[float]:
    """Linear blend then renormalize to a probability distribution.

    final_i = alpha * model_i + (1 - alpha) * market_i
    Returns a list that sums to 1.0. Lengths must match.
    """
    if len(model_probs) != len(market_probs):
        raise ValueError("model_probs and market_probs must have the same length")
    if not 0.0 <= alpha <= 1.0:
        raise ValueError("alpha must be in [0, 1]")

    blended = [alpha * m + (1.0 - alpha) * mk for m, mk in zip(model_probs, market_probs)]
    total = sum(blended)
    if total <= 0:
        n = len(blended)
        return [1.0 / n] * n
    return [b / total for b in blended]
