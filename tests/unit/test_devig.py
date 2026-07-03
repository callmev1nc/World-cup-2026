from wcpredictor.markets.shin import devig, kelly, quarter_kelly_stake, value_bets


def test_devig_sums_to_one():
    odds = [1.58, 4.0, 5.5]
    probs = devig(odds)
    assert abs(sum(probs) - 1.0) < 1e-9


def test_devig_two_way():
    odds = [2.0, 2.0]
    probs = devig(odds)
    assert abs(probs[0] - 0.5) < 1e-9
    assert abs(probs[1] - 0.5) < 1e-9


def test_kelly_exact():
    assert abs(kelly(0.6, 2.0) - 0.2) < 1e-9


def test_kelly_no_bet():
    assert kelly(0.3, 2.0) == 0.0


def test_quarter_kelly_never_exceeds_max():
    stake = quarter_kelly_stake(0.9, 1.5, bankroll=1000.0, max_frac=0.05)
    assert stake <= 50.0


def test_value_bets_no_edge():
    assert value_bets(0.3, 3.0) is None


def test_value_bets_positive_edge():
    vb = value_bets(0.6, 2.0)
    assert vb is not None
    assert vb["edge"] > 0
    assert vb["settles"] == "90min"
