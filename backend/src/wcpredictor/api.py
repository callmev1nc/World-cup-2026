from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .clients.sample import SampleSource
from .pipeline import predict, list_matches, refresh
from .clients.results import fetch_finished
from .schemas import Prediction

app = FastAPI(title="WC 2026 Watch Party Predictor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

source = SampleSource()


@app.get("/matches")
def get_matches():
    return list_matches(source)


@app.get("/predict/{match_id}")
def get_predict(match_id: str) -> Prediction:
    fixtures = source.get_fixtures()
    match = None
    for f in fixtures:
        if f["fixture_id"] == match_id:
            match = f
            break
    if match is None:
        return Prediction(
            match_id=match_id,
            round="R32",
            home="Unknown",
            away="Unknown",
            state="pending",
            elo_home=1500,
            elo_away=1500,
            win=1 / 3,
            draw=1 / 3,
            loss=1 / 3,
            predicted_score="0-0",
            btts_yes=0.5,
        )
    kickoff = datetime.fromisoformat(match["kickoff"]) if match.get("kickoff") else None
    # TBD bracket slots (e.g. "Winner A vs Winner B"): no teams decided yet, so
    # there is nothing to predict — surface a pending card instead.
    if match.get("tbd"):
        return Prediction(
            match_id=match_id,
            round=match["round"],
            home=match["home"],
            away=match["away"],
            kickoff=kickoff,
            state="pending",
            elo_home=1500,
            elo_away=1500,
            win=0.0,
            draw=0.0,
            loss=0.0,
            predicted_score="",
            btts_yes=0.0,
        )
    pred = predict(
        source,
        match["home"],
        match["away"],
        match_id=match_id,
        round_str=match["round"],
        kickoff=kickoff,
    )
    # Finished matches: show the real result (pred-vs-actual) instead of a forecast.
    if match.get("status") == "finished":
        actual = None
        if "ft_home" in match and "ft_away" in match:
            actual = f"{match['ft_home']}-{match['ft_away']}"
        update = {
            "state": "finished",
            "result": match.get("winner"),
            "actual_score": actual,
        }
        # Knockout deciders that went to penalties: record the real shootout
        # result so the UI can show "won 3-4 on pens" alongside the FT draw.
        if "pens_home" in match and "pens_away" in match:
            update["pens"] = {
                "score": f"{match['pens_home']}-{match['pens_away']}",
                "winner": match.get("winner"),
            }
        pred = pred.model_copy(update=update)
    return pred


@app.get("/best-bets")
def get_best_bets():
    """Top +EV picks across all predictable matches — the watch-party bettor's
    quick scan. Reuses predict(); cheap for the ~12 predictable fixtures."""
    picks: list[dict] = []
    for f in source.get_fixtures():
        if f.get("tbd") or f.get("status") == "finished":
            continue
        kickoff = datetime.fromisoformat(f["kickoff"]) if f.get("kickoff") else None
        try:
            pred = predict(
                source, f["home"], f["away"],
                match_id=f["fixture_id"], round_str=f["round"], kickoff=kickoff,
            )
        except Exception:
            continue
        for vb in pred.value_bets:
            picks.append({
                "match_id": f["fixture_id"],
                "home": f["home"],
                "away": f["away"],
                "round": f["round"],
                **vb.model_dump(),
            })
    picks.sort(key=lambda v: v["edge"], reverse=True)
    return picks[:8]


@app.post("/refresh")
@app.get("/refresh")
def get_refresh():
    return refresh(source, fetch_finished)


@app.on_event("startup")
def _autopoll():
    import asyncio, os
    # Off by default on Vercel (serverless: no long-lived process to host a poll).
    default = "0" if os.getenv("VERCEL") else "1"
    if os.getenv("WCPREDICTOR_AUTOPOLL", default) == "0":
        return
    async def loop():
        while True:
            try:
                refresh(source, fetch_finished)
            except Exception:
                pass
            await asyncio.sleep(900)
    asyncio.create_task(loop())


@app.get("/backtest")
def get_backtest():
    return {"log_loss_model": 0.0, "log_loss_market": 0.0, "rps": 0.0, "status": "not yet implemented"}
