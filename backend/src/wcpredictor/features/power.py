from __future__ import annotations
import pandas as pd
from ..clients.kaggle import load_international_results
from ..config import canonical
from .elo import compute_elo

_RATINGS: dict[str, float] | None = None
_RANK: dict[str, int] | None = None

def global_elo_ratings() -> dict[str, float]:
    global _RATINGS
    if _RATINGS is not None:
        return _RATINGS
    rows = load_international_results()
    if not rows:
        _RATINGS = {}
        return _RATINGS
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    ratings, _ = compute_elo(df)
    _RATINGS = {canonical(k): v for k, v in ratings.items()}
    return _RATINGS

def elo_rank(team: str) -> int:
    global _RANK
    r = global_elo_ratings()
    if not r:
        return 0
    if _RANK is None:
        ordered = sorted(r.items(), key=lambda x: -x[1])
        _RANK = {t: i + 1 for i, (t, _) in enumerate(ordered)}
    return _RANK.get(canonical(team), 0)
