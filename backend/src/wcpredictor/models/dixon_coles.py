import numpy as np
from scipy.optimize import minimize
from scipy.stats import poisson


def _tau(i: int, j: int, lh: float, la: float, rho: float) -> float:
    if (i, j) == (0, 0):
        return max(1 - lh * la * rho, 0.01)
    elif (i, j) == (0, 1):
        return max(1 + lh * rho, 0.01)
    elif (i, j) == (1, 0):
        return max(1 + la * rho, 0.01)
    elif (i, j) == (1, 1):
        return max(1 - rho, 0.01)
    return 1.0


def neg_log_likelihood(
    params: np.ndarray,
    goals_h: np.ndarray,
    goals_a: np.ndarray,
    h_idx: np.ndarray,
    a_idx: np.ndarray,
    weights: np.ndarray,
    n_teams: int,
) -> float:
    mu = params[0]
    adv = params[1]
    rho = params[2]
    atk = params[3 : 3 + n_teams]
    defense = params[3 + n_teams :]

    lh = np.exp(mu + adv + atk[h_idx] + defense[a_idx])
    la = np.exp(mu + atk[a_idx] + defense[h_idx])

    gh_arr = np.asarray(goals_h, dtype=int)
    ga_arr = np.asarray(goals_a, dtype=int)

    tau_vals = np.ones_like(lh)
    mask00 = (gh_arr == 0) & (ga_arr == 0)
    mask01 = (gh_arr == 0) & (ga_arr == 1)
    mask10 = (gh_arr == 1) & (ga_arr == 0)
    mask11 = (gh_arr == 1) & (ga_arr == 1)
    tau_vals[mask00] = np.maximum(1 - lh[mask00] * la[mask00] * rho, 0.01)
    tau_vals[mask01] = np.maximum(1 + lh[mask01] * rho, 0.01)
    tau_vals[mask10] = np.maximum(1 + la[mask10] * rho, 0.01)
    tau_vals[mask11] = np.maximum(1 - rho, 0.01)

    p = tau_vals * poisson.pmf(gh_arr, lh) * poisson.pmf(ga_arr, la)
    p = np.clip(p, 1e-12, None)
    reg = 1e-3 * (np.sum(atk**2) + np.sum(defense**2))
    return -float(np.sum(weights * np.log(p))) + reg


def fit(results, n_teams: int, xi: float = 1 / 365) -> np.ndarray:
    results = results.sort_values("date")
    delta = (results["date"].max() - results["date"]).dt.days.values
    weights = np.exp(-xi * delta)

    x0 = np.r_[0.3, 0.25, -0.05, np.zeros(2 * n_teams)]
    bounds = [(None, None), (None, None), (-0.3, 0.3)] + [(None, None)] * (2 * n_teams)
    res = minimize(
        neg_log_likelihood,
        x0,
        args=(
            results.home_goals.values,
            results.away_goals.values,
            results.home_idx.values,
            results.away_idx.values,
            weights,
            n_teams,
        ),
        method="L-BFGS-B",
        bounds=bounds,
    )
    return res.x


def score_matrix(params: np.ndarray, n_teams: int, home_idx: int, away_idx: int, max_goals: int = 10) -> np.ndarray:
    mu = params[0]
    adv = params[1]
    rho = params[2]
    atk = params[3 : 3 + n_teams]
    defense = params[3 + n_teams :]

    lh = min(max(float(np.exp(mu + adv + atk[home_idx] + defense[away_idx])), 0.15), 3.0)
    la = min(max(float(np.exp(mu + atk[away_idx] + defense[home_idx])), 0.15), 3.0)

    P = np.zeros((max_goals + 1, max_goals + 1))
    for i in range(max_goals + 1):
        for j in range(max_goals + 1):
            P[i, j] = _tau(i, j, lh, la, rho) * poisson.pmf(i, lh) * poisson.pmf(j, la)

    P /= P.sum()
    return P


def derive_markets(P: np.ndarray) -> dict:
    n = P.shape[0] - 1
    rows = np.arange(n + 1)[:, None]
    cols = np.arange(n + 1)[None, :]
    goals = rows + cols  # total-goals grid

    win = float(P[rows > cols].sum())
    draw = float(np.trace(P))
    loss = float(P[rows < cols].sum())

    btts = float(P[1:, 1:].sum())

    def ou_line(line: float) -> dict[str, float]:
        # Over `line` = strictly more goals than the line (line 2.5 -> i+j >= 3).
        over_cut = int(np.floor(line)) + 1
        over = float(P[goals >= over_cut].sum())
        return {"over": over, "under": 1.0 - over}

    double_chance = {
        "1x": win + draw,            # home or draw
        "x2": draw + loss,           # draw or away
        "12": win + loss,            # home or away (not a draw)
    }

    total_goals = {
        "0-1": float(P[goals <= 1].sum()),
        "2-3": float(P[(goals >= 2) & (goals <= 3)].sum()),
        "4-5": float(P[(goals >= 4) & (goals <= 5)].sum()),
        "6+": float(P[goals >= 6].sum()),
    }

    win_to_nil = {
        "home": float(P[1:, 0].sum()),   # home scores, away nil
        "away": float(P[0, 1:].sum()),   # away scores, home nil
    }

    score_top = []
    for i in range(n + 1):
        for j in range(n + 1):
            if P[i, j] > 0.01:
                score_top.append((f"{i}-{j}", float(P[i, j])))
    score_top.sort(key=lambda x: -x[1])
    score_top = score_top[:8]

    predicted_i = int(np.argmax(np.sum(P, axis=1)))
    predicted_j = int(np.argmax(np.sum(P, axis=0)))
    predicted_score = f"{predicted_i}-{predicted_j}"

    return {
        "win": win,
        "draw": draw,
        "loss": loss,
        "predicted_score": predicted_score,
        "score_top": score_top,
        "ou": {"1.5": ou_line(1.5), "2.5": ou_line(2.5), "3.5": ou_line(3.5)},
        "btts_yes": btts,
        "double_chance": double_chance,
        "total_goals": total_goals,
        "win_to_nil": win_to_nil,
    }
