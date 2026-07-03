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


class MatchSummary(BaseModel):
    match_id: str
    round: str
    home: str
    away: str
    kickoff: datetime | None = None
    state: State
