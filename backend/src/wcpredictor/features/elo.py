K_BY_TIER = {
    "friendly": 20,
    "qualifier": 30,
    "continental": 40,
    "nations_league": 40,
    "wc": 50,
}


def expected(ra: float, rb: float, h_adj: float = 0) -> float:
    return 1 / (1 + 10 ** (-(ra - rb + h_adj) / 400))


def g_factor(goal_diff: int) -> float:
    return min(5.0, (11 + abs(goal_diff)) / 10)


def update(
    ra: float, rb: float, score_a: float, goal_diff: int, k: float, h_adj: float = 0
) -> tuple[float, float]:
    e = expected(ra, rb, h_adj)
    g = g_factor(goal_diff)
    delta = k * g * (score_a - e)
    return ra + delta, rb - delta


def _get_tier(r) -> str:
    try:
        return r.tier
    except AttributeError:
        try:
            return r.tournament
        except AttributeError:
            return "friendly"


def compute_elo(df, start: float = 1500, h_adj_home: float = 80, neutral_is_wc: bool = True):
    rating: dict[str, float] = {}
    hist = []
    for r in df.itertuples():
        hs = r[4]
        a = r[5]
        ra = rating.get(r.home, start)
        rb = rating.get(r.away, start)
        tier = _get_tier(r)
        k = K_BY_TIER.get(tier, 20)
        ha = 0 if neutral_is_wc else h_adj_home
        score_a = 1.0 if hs > a else (0.5 if hs == a else 0.0)
        na, nb = update(ra, rb, score_a, hs - a, k, ha)
        rating[r.home] = na
        rating[r.away] = nb
        hist.append((r.date, r.home, na, r.away, nb))
    return rating, hist
