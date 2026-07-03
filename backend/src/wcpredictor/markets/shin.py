import numpy as np


def devig(odds: list[float]) -> list[float]:
    q = np.array([1 / o for o in odds])
    return (q / q.sum()).tolist()


def kelly(p: float, decimal_odds: float) -> float:
    b = decimal_odds - 1.0
    if b <= 0:
        return 0.0
    f = (b * p - (1 - p)) / b
    return max(0.0, f)


def quarter_kelly_stake(p: float, odds: float, bankroll: float = 1000.0, max_frac: float = 0.05) -> float:
    f = 0.25 * kelly(p, odds)
    f = max(0.0, min(f, max_frac))
    return f * bankroll


def value_bets(model_prob: float, odds: float) -> dict | None:
    if odds <= 1.0:
        return None
    implied = 1.0 / odds
    edge = model_prob - implied
    if edge <= 0:
        return None
    kelly_frac = kelly(model_prob, odds)
    if kelly_frac <= 0:
        return None
    return {
        "model_prob": model_prob,
        "odds": odds,
        "edge": edge,
        "kelly": 0.25 * kelly_frac,
        "settles": "90min",
    }
