import numpy as np
import pandas as pd
from wcpredictor.models.dixon_coles import _tau, fit, score_matrix, derive_markets


def test_tau_00():
    result = _tau(0, 0, 2.0, 1.5, -0.1)
    assert result == max(1 - 2.0 * 1.5 * (-0.1), 0.01)


def test_tau_01():
    result = _tau(0, 1, 2.0, 1.5, -0.1)
    assert result == max(1 + 2.0 * (-0.1), 0.01)


def test_tau_10():
    result = _tau(1, 0, 2.0, 1.5, -0.1)
    assert result == max(1 + 1.5 * (-0.1), 0.01)


def test_tau_11():
    result = _tau(1, 1, 2.0, 1.5, -0.1)
    assert result == max(1 - (-0.1), 0.01)


def test_score_matrix_sums_to_one():
    params = np.r_[0.3, 0.25, -0.1, np.zeros(4)]
    P = score_matrix(params, 2, 0, 1)
    assert abs(P.sum() - 1.0) < 1e-9


def test_derive_markets_sums_to_one():
    params = np.r_[0.3, 0.25, -0.1, np.zeros(4)]
    P = score_matrix(params, 2, 0, 1)
    m = derive_markets(P)
    assert abs(m["win"] + m["draw"] + m["loss"] - 1.0) < 1e-6


def test_derive_markets_ou25():
    params = np.r_[0.3, 0.25, -0.1, np.zeros(4)]
    P = score_matrix(params, 2, 0, 1, max_goals=5)
    m = derive_markets(P)
    over_manual = float(sum(P[i, j] for i in range(6) for j in range(6) if i + j >= 3))
    assert abs(m["ou"]["2.5"]["over"] - over_manual) < 1e-3


def test_derive_markets_new_markets_invariants():
    params = np.r_[0.3, 0.25, -0.1, np.zeros(4)]
    P = score_matrix(params, 2, 0, 1, max_goals=5)
    m = derive_markets(P)

    dc = m["double_chance"]
    # 1x=w+d, x2=d+l, 12=w+l → trio sums to 2·(w+d+l) = 2
    assert abs(dc["1x"] + dc["x2"] + dc["12"] - 2.0) < 1e-6
    assert abs(dc["1x"] - (m["win"] + m["draw"])) < 1e-6
    assert abs(dc["12"] - (m["win"] + m["loss"])) < 1e-6

    tg = m["total_goals"]
    assert abs(sum(tg.values()) - 1.0) < 1e-6

    # Every O/U line sums to 1, and "over" is monotonic non-increasing in the line.
    for line in ("1.5", "2.5", "3.5"):
        ou = m["ou"][line]
        assert abs(ou["over"] + ou["under"] - 1.0) < 1e-6
    assert m["ou"]["1.5"]["over"] >= m["ou"]["2.5"]["over"] - 1e-9
    assert m["ou"]["2.5"]["over"] >= m["ou"]["3.5"]["over"] - 1e-9

    # Win-to-nil is a subset of the corresponding win.
    assert m["win_to_nil"]["home"] <= m["win"] + 1e-9
    assert m["win_to_nil"]["away"] <= m["loss"] + 1e-9


def test_predicted_score_never_extreme():
    params = np.r_[3.0, 2.0, -0.1, np.zeros(4)]  # deliberately huge mu/adv
    P = score_matrix(params, 2, 0, 1)
    m = derive_markets(P)
    hi = max(int(s.split("-")[0]) for s, _ in m["score_top"])
    assert hi <= 4


def test_fit_on_synthetic_data():
    n_teams = 4
    true_mu, true_adv, true_rho = 0.2, 0.3, -0.08
    true_atk = np.array([0.2, -0.1, 0.3, -0.4])
    true_def = np.array([-0.2, 0.1, -0.3, 0.4])

    np.random.seed(42)
    matches = []
    dates = []
    for i in range(100):
        h = np.random.randint(0, n_teams)
        a = np.random.randint(0, n_teams)
        if h == a:
            continue
        lh = np.exp(true_mu + true_adv + true_atk[h] + true_def[a])
        la = np.exp(true_mu + true_atk[a] + true_def[h])
        gh = np.random.poisson(lh)
        ga = np.random.poisson(la)
        matches.append((h, a, gh, ga))
        dates.append(pd.Timestamp("2026-01-01") + pd.Timedelta(days=i))

    df = pd.DataFrame({
        "date": dates,
        "home_idx": [m[0] for m in matches],
        "away_idx": [m[1] for m in matches],
        "home_goals": [m[2] for m in matches],
        "away_goals": [m[3] for m in matches],
    })

    params = fit(df, n_teams)
    assert len(params) == 3 + 2 * n_teams
    assert abs(params[2]) < 0.3  # rho bounded
