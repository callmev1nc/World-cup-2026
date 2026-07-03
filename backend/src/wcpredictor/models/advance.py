"""Knockout "to advance / to qualify" probabilities.

Derives the probability each team advances from a 90-minute score matrix by
modelling extra time (30 min at a reduced scoring rate) and penalties (~50/50).

Invariants (unit-tested):
  p_home_advance + p_away_advance == 1.0
  p_home_advance >= p_home_win90          (advancing is always >= winning in 90)
"""
from __future__ import annotations

import numpy as np
from scipy.stats import poisson


def _lambdas(params: np.ndarray, n_teams: int, home_idx: int, away_idx: int) -> tuple[float, float]:
    mu, adv = params[0], params[1]
    atk = params[3 : 3 + n_teams]
    defence = params[3 + n_teams :]
    lh = float(np.exp(mu + adv + atk[home_idx] + defence[away_idx]))
    la = float(np.exp(mu + atk[away_idx] + defence[home_idx]))
    return lh, la


def _et_matrix(lh: float, la: float, et_factor: float = 0.55, max_goals: int = 5) -> np.ndarray:
    """Extra-time score grid: 30 min at ~55% of the per-minute 90-min rate."""
    lh_et = lh * (30 / 90) * et_factor
    la_et = la * (30 / 90) * et_factor
    P = np.array(
        [[poisson.pmf(i, lh_et) * poisson.pmf(j, la_et) for j in range(max_goals + 1)]
         for i in range(max_goals + 1)]
    )
    return P / P.sum()


def to_advance(
    P90: np.ndarray,
    params: np.ndarray,
    n_teams: int,
    home_idx: int,
    away_idx: int,
    et_factor: float = 0.55,
    pen_home: float = 0.5,
) -> dict[str, float]:
    """Return {"home": p_home_advances, "away": p_away_advances}.

    pen_home = probability the home team wins a penalty shootout (default 0.5).
    """
    lh, la = _lambdas(params, n_teams, home_idx, away_idx)
    n = P90.shape[0] - 1

    p_home_win90 = float(sum(P90[i, j] for i in range(n + 1) for j in range(n + 1) if i > j))
    p_draw90 = float(sum(P90[i, i] for i in range(n + 1)))

    PET = _et_matrix(lh, la, et_factor)
    m = PET.shape[0] - 1
    p_home_win_et = float(sum(PET[i, j] for i in range(m + 1) for j in range(m + 1) if i > j))
    p_et_draw = float(sum(PET[i, i] for i in range(m + 1)))

    p_home_advance = p_home_win90 + p_draw90 * (p_home_win_et + p_et_draw * pen_home)
    return {"home": p_home_advance, "away": 1.0 - p_home_advance}
