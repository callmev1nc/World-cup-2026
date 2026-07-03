from wcpredictor.models.bracket import resolve


def test_resolve_tbd_slot():
    fixtures = [
        {"fixture_id": "a", "round": "R32", "home": "A", "away": "B", "status": "finished", "winner": "home"},
        {"fixture_id": "b", "round": "R32", "home": "C", "away": "D", "status": "finished", "winner": "away"},
        {"fixture_id": "r16-x", "round": "R16", "home": "TBD", "away": "TBD", "status": "not_started", "tbd": True,
         "links": {"home_from": "a", "away_from": "b"}},
    ]
    changed = resolve(fixtures)
    assert "r16-x" in changed
    r16 = next(f for f in fixtures if f["fixture_id"] == "r16-x")
    assert r16["home"] == "A"
    assert r16["away"] == "D"
    assert r16["tbd"] is False
