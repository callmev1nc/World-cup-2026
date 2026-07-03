from wcpredictor.schemas import finished_prediction

REQUIRED_ARRAY_KEYS = (
    "form_home", "form_away", "score_top",
    "top_scorers_home", "top_scorers_away", "value_bets",
)
REQUIRED_DICT_KEYS = ("team_stats", "ou", "double_chance", "total_goals", "win_to_nil")


def test_finished_prediction_has_all_required_keys():
    d = finished_prediction(
        match_id="760497", round="Group", home="Spain", away="Austria",
        ft_home=3, ft_away=0, winner="home",
    )
    # finished-state fields
    assert d["state"] == "finished"
    assert d["actual_score"] == "3-0"
    assert d["result"] == "home"
    # every forecast array/dict the TS type declares required is present and well-typed
    for k in REQUIRED_ARRAY_KEYS:
        assert isinstance(d[k], list), f"{k} missing or not a list: {d.get(k)!r}"
    for k in REQUIRED_DICT_KEYS:
        assert isinstance(d[k], dict), f"{k} missing or not a dict: {d.get(k)!r}"
    # scalars the TS type requires
    for k in ("elo_home", "elo_away", "win", "draw", "loss", "btts_yes", "predicted_score"):
        assert k in d, f"{k} missing"
    assert d["rank_home"] == 0 and d["rank_away"] == 0


def test_finished_prediction_includes_pens_when_given():
    d = finished_prediction(
        match_id="x", home="A", away="B", ft_home=1, ft_away=1, winner="home",
        pens_home=4, pens_away=3,
    )
    assert d["pens"] == {"score": "4-3", "winner": "home"}


def test_finished_prediction_omits_pens_when_absent():
    d = finished_prediction(match_id="x", home="A", away="B", ft_home=2, ft_away=1, winner="home")
    assert "pens" not in d or d.get("pens") is None


from lib import merge_matches


def test_merge_matches_backfills_score_from_predictions_when_no_overlay():
    baked = [{"match_id": "760497", "home": "Spain", "away": "Austria", "state": "finished"}]
    predictions = {"760497": {"actual_score": "3-0", "result": "home", "pens": None}}
    out = merge_matches(baked, overlay={}, predictions=predictions)
    assert out[0]["actual_score"] == "3-0"
    assert out[0]["result"] == "home"


def test_merge_matches_overlay_takes_priority_over_predictions():
    baked = [{"match_id": "1", "home": "A", "away": "B", "state": "scheduled"}]
    out = merge_matches(baked, overlay={"1": {"status": "finished", "ft_home": 2, "ft_away": 2, "winner": "home"}}, predictions={})
    assert out[0]["state"] == "finished"
    assert out[0]["actual_score"] == "2-2"
