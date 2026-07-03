from datetime import datetime
from typing import Literal
from pydantic import BaseModel

State = Literal["predictable", "scheduled", "waiting_result", "finished", "pending"]


class ValueBet(BaseModel):
    market: str
    model_prob: float
    odds: float
    edge: float
    kelly: float
    settles: Literal["90min", "advance"]


class Prediction(BaseModel):
    match_id: str
    round: str
    home: str
    away: str
    kickoff: datetime | None = None
    state: State
    elo_home: int
    elo_away: int
    rank_home: int = 0
    rank_away: int = 0
    form_home: list[str] = []
    form_away: list[str] = []
    win: float
    draw: float
    loss: float
    predicted_score: str
    score_top: list[tuple[str, float]] = []
    ou: dict[str, dict[str, float]] = {}
    btts_yes: float
    double_chance: dict[str, float] = {}  # {"1x","x2","12"}
    total_goals: dict[str, float] = {}    # {"0-1","2-3","4-5","6+"}
    win_to_nil: dict[str, float] = {}     # {"home","away"}
    corners_over_95: float | None = None
    advance: dict[str, float] | None = None
    pens: dict[str, str] | None = None  # {"score":"4-3","winner":"home"} drawn-knockout shootout guess
    team_stats: dict[str, dict[str, float]] = {}
    top_scorers_home: list[dict] = []
    top_scorers_away: list[dict] = []
    value_bets: list[ValueBet] = []
    actual_score: str | None = None
    result: Literal["home", "draw", "away"] | None = None
    clv: dict[str, float] | None = None


def finished_prediction(
    *,
    match_id: str,
    round: str | None = None,
    home: str | None = None,
    away: str | None = None,
    kickoff: datetime | None = None,
    ft_home: int = 0,
    ft_away: int = 0,
    winner: str | None = None,
    pens_home: int | None = None,
    pens_away: int | None = None,
    round_default: str = "R32",
) -> dict:
    """Build a complete, schema-valid finished-match prediction dict.

    Construction goes through the Prediction model so every field with a
    default (form_home=[], score_top=[], value_bets=[], team_stats={}, ...)
    is filled — finished cards never omit keys that MarqueeMatch and the TS
    Prediction type assume are present.
    """
    actual = f"{ft_home}-{ft_away}"
    pred = Prediction(
        match_id=match_id,
        round=round or round_default,
        home=home or "Unknown",
        away=away or "Unknown",
        kickoff=kickoff,
        state="finished",
        elo_home=1500,
        elo_away=1500,
        win=0.0,
        draw=0.0,
        loss=0.0,
        predicted_score=actual,
        btts_yes=0.0,
        actual_score=actual,
        result=winner,
    )
    d = pred.model_dump(mode="json")
    if pens_home is not None and pens_away is not None:
        d["pens"] = {"score": f"{pens_home}-{pens_away}", "winner": winner}
    return d


class MatchSummary(BaseModel):
    match_id: str
    round: str
    home: str
    away: str
    kickoff: datetime | None = None
    state: State
