"""Integration smoke test: SampleSource → predict() should return a valid Prediction."""

import time

from wcpredictor.clients.sample import SampleSource
from wcpredictor.pipeline import predict


def test_pipeline_returns_prediction():
    src = SampleSource()
    start = time.perf_counter()
    p = predict(src, "Spain", "Austria", match_id="spain-aut")
    elapsed = time.perf_counter() - start

    assert p.match_id == "spain-aut"
    assert p.home == "Spain"
    assert p.away == "Austria"
    assert 0 < p.win < 1
    assert 0 < p.draw < 1
    assert 0 < p.loss < 1
    assert abs(p.win + p.draw + p.loss - 1.0) < 0.02
    assert p.elo_home > 1500
    assert p.elo_away > 1500
    assert len(p.form_home) <= 5
    assert len(p.form_away) <= 5
    assert len(p.score_top) > 0
    assert "2.5" in p.ou
    assert 0 <= p.btts_yes <= 1
    assert elapsed < 2.0, f"Pipeline took {elapsed:.2f}s (should be <2s)"


def test_pipeline_r16_markets_and_always_on_pens():
    """R16 prediction: new markets populate and the pens guess shows even when
    the forecast isn't a draw (any level knockout after ET goes to pens)."""
    src = SampleSource()
    p = predict(src, "Paraguay", "France", match_id="par-fra", round_str="R16")
    assert p.round == "R16"
    assert len(p.double_chance) == 3
    assert len(p.total_goals) == 4
    assert abs(sum(p.total_goals.values()) - 1.0) < 1e-6
    assert p.win_to_nil["home"] <= p.win + 1e-6
    assert p.pens is not None
    assert p.pens["winner"] in ("home", "away")


def test_value_bets_helper_collects_positive_edge():
    from wcpredictor.pipeline import _value_bets_for

    # devig([1.5, 3.0]) ≈ [0.667, 0.333]; "No" (model 0.4) is +EV, "Yes" is not.
    bets = _value_bets_for("BTTS", [("Yes", 0.6), ("No", 0.4)], [1.5, 3.0])
    assert any(b["market"] == "BTTS No" for b in bets)
    assert not any(b["market"] == "BTTS Yes" for b in bets)
    assert all(b["edge"] > 0 and b["kelly"] > 0 for b in bets)

    # Length mismatch → safe no-op.
    assert _value_bets_for("X", [("A", 0.5)], [1.5, 2.0]) == []
