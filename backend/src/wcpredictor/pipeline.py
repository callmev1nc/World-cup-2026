from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import json

from .clients.kaggle import results_for_teams, goalscorers_for_team
from .features.elo import compute_elo, K_BY_TIER
from .features.power import global_elo_ratings, elo_rank
from .config import canonical
from .models import bracket
from .models.dixon_coles import fit, score_matrix, derive_markets
from .models.ensemble import blend
from .models.advance import to_advance
from .markets.shin import devig, kelly
from .schemas import Prediction, MatchSummary
from .matchstate import state_of

STATE_FILE = Path(__file__).parents[3] / "data" / "state" / "results.json"


def _load_overlay() -> dict:
    return json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {}


def _save_overlay(o: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(o, indent=2, default=str))


def _key_for(f):
    return f"{canonical(f['home'])}-{canonical(f['away'])}"


def refresh(source, feed=None) -> dict:
    base = [dict(f) for f in source.get_fixtures()]
    overlay = _load_overlay()
    for f in base:
        f.update(overlay.get(f["fixture_id"], {}))
    updated: list[str] = []
    if feed:
        for key, res in feed().items():
            parts = key.split("-", 1)
            rev = f"{parts[1]}-{parts[0]}" if len(parts) == 2 else key
            for f in base:
                if f.get("tbd") or f.get("status") == "finished":
                    continue
                k = _key_for(f)
                if k == key or k == rev:           # order-insensitive team match
                    f.update({"status": "finished", **res})
                    overlay[f["fixture_id"]] = {"status": "finished", **res}
                    updated.append(f["fixture_id"])
                    break
    resolved = bracket.resolve(base)
    for fid in resolved:
        f = next(x for x in base if x["fixture_id"] == fid)
        overlay[fid] = {k: f[k] for k in ("home", "away", "tbd") if k in f}
    _save_overlay(overlay)
    return {"updated": updated, "resolved": resolved}


def _build_teams_list(all_results: list[dict]) -> dict[str, int]:
    teams = set()
    for r in all_results:
        teams.add(r["home"])
        teams.add(r["away"])
    return {t: i for i, t in enumerate(sorted(teams))}


def _form_from_results(results: list[dict], team: str) -> list[str]:
    team_results = [r for r in results if r["home"] == team or r["away"] == team]
    team_results.sort(key=lambda x: x["date"], reverse=True)
    form = []
    for r in team_results[:5]:
        if r["home"] == team:
            if r["hs"] > r["as"]:
                form.append("W")
            elif r["hs"] == r["as"]:
                form.append("D")
            else:
                form.append("L")
        else:
            if r["as"] > r["hs"]:
                form.append("W")
            elif r["as"] == r["hs"]:
                form.append("D")
            else:
                form.append("L")
    return form


def _pen_guess(match_id: str, winner: str) -> dict[str, str]:
    """Illustrative penalty-shootout guess. Penalties are ~50/50, so this is a
    fun guess, not a betting edge. Deterministic per match so it stays stable
    across reloads. `winner` is "home" or "away" (decided by the caller from
    advance / win probabilities)."""
    import hashlib
    h = int(hashlib.md5(match_id.encode()).hexdigest(), 16)
    base = 4 + (h % 2)           # winner scores 4 or 5
    margin = 1 + ((h >> 3) % 2)  # wins by 1 or 2
    loser = base - margin
    if winner == "home":
        return {"score": f"{base}-{loser}", "winner": "home"}
    return {"score": f"{loser}-{base}", "winner": "away"}


def _value_bets_for(market: str, outcomes, odds_list, settles: str = "90min") -> list[dict]:
    """Collect +EV picks for one market. `outcomes` is a list of (label,
    model_prob) tuples; `odds_list` the bookmaker decimals for the same order.
    Keeps an outcome only when model edge > 0 AND full Kelly > 0."""
    if not odds_list or len(odds_list) != len(outcomes):
        return []
    fair = devig(odds_list)
    out = []
    for i, (name, mp) in enumerate(outcomes):
        edge = mp - fair[i]
        fk = kelly(mp, odds_list[i])
        if edge > 0 and fk > 0:
            label = f"{market} {name}".strip()
            out.append({
                "market": label,
                "model_prob": mp,
                "odds": odds_list[i],
                "edge": edge,
                "kelly": 0.25 * fk,
                "settles": settles,
            })
    return out


def predict(source, home: str, away: str, match_id: str | None = None, round_str: str = "R32", kickoff: datetime | None = None) -> Prediction:
    all_results = []
    for team in [home, away]:
        all_results.extend(source.get_team_recent(team, limit=20))
    # Augment with real international history when the Kaggle CSV is present
    # (biggest quality lever). No-op until data/raw/kaggle/results.csv exists.
    all_results.extend(results_for_teams([home, away]))

    # Canonicalize team names so sample ("USA") + history ("United States") merge
    # into one Dixon-Coles node — otherwise alias-mismatched teams only get their
    # handful of sample rows in the fit instead of their full international history.
    for r in all_results:
        r["home"] = canonical(r["home"])
        r["away"] = canonical(r["away"])

    seen: set = set()
    deduped: list[dict] = []
    for r in all_results:
        key = (r["date"], r["home"], r["away"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(r)
    all_results = deduped

    df = pd.DataFrame(all_results)
    now = datetime.now(timezone.utc)
    if df.empty:
        return Prediction(
            match_id=match_id or f"{home.lower()}-{away.lower()}",
            round=round_str,
            home=home,
            away=away,
            kickoff=kickoff,
            state=state_of(None, False, kickoff, now, False, True),
            elo_home=1500,
            elo_away=1500,
            win=1 / 3,
            draw=1 / 3,
            loss=1 / 3,
            predicted_score="1-1",
            btts_yes=0.5,
        )

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    df["tier"] = df["tier"].map(lambda t: t if t in K_BY_TIER else "friendly")
    if "neutral" not in df.columns:
        df["neutral"] = False

    g_ratings = global_elo_ratings()
    elo_ratings = g_ratings if g_ratings else compute_elo(df)[0]
    ch, ca = canonical(home), canonical(away)
    elo_home = int(round(elo_ratings.get(ch, elo_ratings.get(home, 1500))))
    elo_away = int(round(elo_ratings.get(ca, elo_ratings.get(away, 1500))))
    rank_home = elo_rank(home)
    rank_away = elo_rank(away)

    teams_idx = _build_teams_list(all_results)
    n_teams = len(teams_idx)

    df["home_idx"] = df["home"].map(teams_idx)
    df["away_idx"] = df["away"].map(teams_idx)
    df["home_goals"] = df["hs"]
    df["away_goals"] = df["as"]

    params = fit(df, n_teams)

    home_idx = teams_idx.get(ch, 0)
    away_idx = teams_idx.get(ca, 0)

    P = score_matrix(params, n_teams, home_idx, away_idx)
    markets = derive_markets(P)

    odds_data = source.get_odds(match_id or f"{home.lower()}-{away.lower()}")
    odds_1x2 = odds_data.get("h2h") if odds_data else None

    if odds_1x2 and len(odds_1x2) == 3:
        devigged = devig(odds_1x2)
    else:
        devigged = [1 / 3, 1 / 3, 1 / 3]

    # Blend the Dixon-Coles 1X2 with the devigged market. The market is a strong
    # prior; alpha is the weight on our model (0.4 default — tune on validation).
    b_win, b_draw, b_loss = blend(
        [markets["win"], markets["draw"], markets["loss"]], devigged, alpha=0.4
    )

    # To-advance (knockout "to qualify"). Every round except the Final has one.
    # Blend with a market-implied advance (win + half the draws) so it stays
    # consistent with the blended 1X2 rather than reflecting raw DC alone.
    advance = None
    if round_str != "Final":
        dc_adv = to_advance(P, params, n_teams, home_idx, away_idx)
        if odds_1x2 and len(odds_1x2) == 3:
            mkt_home = devigged[0] + 0.5 * devigged[1]
            mkt_away = devigged[2] + 0.5 * devigged[1]
            ah = 0.4 * dc_adv["home"] + 0.6 * mkt_home
            aa = 0.4 * dc_adv["away"] + 0.6 * mkt_away
            s = ah + aa
            s = s if s > 0 else 1.0
            advance = {"home": ah / s, "away": aa / s}
        else:
            advance = dc_adv

    # Blend secondary markets (O/U 2.5, BTTS, Double Chance) with their devigged
    # market priors — same rationale as 1X2, so a tiny DC fit (few friendlies)
    # can't produce wild +EV edges vs the bookmaker. Lines/markets without odds
    # keep their raw model value.
    ou = markets["ou"]
    ou_odds = odds_data.get("ou25") if odds_data else None
    if ou_odds and len(ou_odds) == 2:
        bo = 0.4 * ou["2.5"]["over"] + 0.6 * devig(ou_odds)[0]
        ou = {**ou, "2.5": {"over": bo, "under": 1.0 - bo}}
    btts_yes = markets["btts_yes"]
    btts_odds = odds_data.get("btts") if odds_data else None
    if btts_odds and len(btts_odds) == 2:
        btts_yes = 0.4 * btts_yes + 0.6 * devig(btts_odds)[0]
    # Double Chance is fully determined by 1X2 (1x=win+draw, x2=draw+loss,
    # 12=win+loss), so derive it from the BLENDED 1X2 — never from raw DC odds,
    # whose three outcomes overlap and so cannot be devigged as a simplex.
    dc = {
        "1x": b_win + b_draw,
        "x2": b_draw + b_loss,
        "12": b_win + b_loss,
    }

    # Penalty-shootout guess — any level knockout after ET goes to pens, so show
    # it on every card regardless of the predicted score. Winner from advance,
    # else from the blended 1X2, else home by default.
    mid = match_id or f"{home.lower()}-{away.lower()}"
    if advance is not None:
        pen_winner = "home" if advance["home"] >= 0.5 else "away"
    else:
        pen_winner = "home" if b_win >= b_loss else "away"
    pens = _pen_guess(mid, pen_winner)

    # Value bets across every market we have bookmaker prices for. Each line is
    # model prob vs Shin-devigged fair, kept only at +EV.
    value_list: list[dict] = []
    if odds_data:
        if odds_data.get("h2h") and len(odds_data["h2h"]) == 3:
            value_list += _value_bets_for(
                "1X2", [("Home", b_win), ("Draw", b_draw), ("Away", b_loss)], odds_data["h2h"]
            )
        if ou_odds and len(ou_odds) == 2:
            value_list += _value_bets_for(
                "Over/Under 2.5", [("Over", ou["2.5"]["over"]), ("Under", ou["2.5"]["under"])], ou_odds
            )
        if btts_odds and len(btts_odds) == 2:
            value_list += _value_bets_for(
                "BTTS", [("Yes", btts_yes), ("No", 1 - btts_yes)], btts_odds
            )
    value_list.sort(key=lambda v: v["edge"], reverse=True)

    def _team_stats(results, team):
        rows = [r for r in results if r["home"] == team or r["away"] == team][-12:]
        if not rows:
            return {}
        gf = ga = cs = fs = 0
        for r in rows:
            if r["home"] == team:
                s, c = r["hs"], r["as"]
            else:
                s, c = r["as"], r["hs"]
            gf += s; ga += c
            if c == 0: cs += 1
            if s == 0: fs += 1
        n = len(rows)
        return {"gfpg": round(gf / n, 2), "gapg": round(ga / n, 2),
                "clean_sheet": round(cs / n, 3), "fail_score": round(fs / n, 3)}

    return Prediction(
        match_id=match_id or f"{home.lower()}-{away.lower()}",
        round=round_str,
        home=home,
        away=away,
        kickoff=kickoff,
        state=state_of("not_started", True, kickoff, now, False, True),
        elo_home=elo_home,
        elo_away=elo_away,
        rank_home=rank_home,
        rank_away=rank_away,
        form_home=_form_from_results(all_results, ch),
        form_away=_form_from_results(all_results, ca),
        win=b_win,
        draw=b_draw,
        loss=b_loss,
        predicted_score=markets["predicted_score"],
        score_top=markets["score_top"],
        ou=ou,
        btts_yes=btts_yes,
        double_chance=dc,
        total_goals=markets["total_goals"],
        win_to_nil=markets["win_to_nil"],
        advance=advance,
        pens=pens,
        team_stats={"home": _team_stats(all_results, ch), "away": _team_stats(all_results, ca)},
        top_scorers_home=goalscorers_for_team(ch),
        top_scorers_away=goalscorers_for_team(ca),
        value_bets=value_list,
    )


def list_matches(source) -> list[MatchSummary]:
    fixtures = source.get_fixtures()
    now = datetime.now(timezone.utc)
    summaries = []
    for f in fixtures:
        kickoff = datetime.fromisoformat(f["kickoff"]) if f.get("kickoff") else None
        if f.get("tbd"):
            state = "pending"
        else:
            # A match is only "predictable" if we actually have recent form for
            # at least one side; otherwise it's "scheduled" until data arrives.
            has_data = bool(source.get_team_recent(f["home"])) or bool(source.get_team_recent(f["away"]))
            state = state_of(
                f.get("status"), has_data, kickoff, now,
                f.get("status") == "finished", True,
            )
        summaries.append(MatchSummary(
            match_id=f["fixture_id"],
            round=f["round"],
            home=f["home"],
            away=f["away"],
            kickoff=kickoff,
            state=state,
        ))
    return summaries
