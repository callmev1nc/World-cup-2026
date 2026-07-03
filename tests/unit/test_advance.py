"""Tests for knockout to-advance probabilities."""
import numpy as np

from wcpredictor.models.dixon_coles import score_matrix
from wcpredictor.models.advance import to_advance


def _params(n: int) -> np.ndarray:
    return np.r_[0.3, 0.25, -0.1, np.zeros(2 * n)]


def test_advance_sums_to_one():
    n = 4
    P = score_matrix(_params(n), n, 0, 1)
    adv = to_advance(P, _params(n), n, 0, 1)
    assert abs(adv["home"] + adv["away"] - 1.0) < 1e-9


def test_advance_ge_win90():
    n = 4
    params = _params(n)
    P = score_matrix(params, n, 0, 1)
    adv = to_advance(P, params, n, 0, 1)
    p_home_win90 = float(
        sum(P[i, j] for i in range(P.shape[0]) for j in range(P.shape[0]) if i > j)
    )
    assert adv["home"] >= p_home_win90 - 1e-9


def test_stronger_team_advances_more_often():
    n = 4
    params = _params(n)
    params[3] = 0.9  # team 0 attack boost -> home side clearly stronger
    P = score_matrix(params, n, 0, 1)
    adv = to_advance(P, params, n, 0, 1)
    assert adv["home"] > 0.5
