from wcpredictor.markets.shin import kelly, quarter_kelly_stake


def test_kelly_half():
    assert abs(kelly(0.6, 2.0) - 0.2) < 1e-9


def test_kelly_zero_when_unfavorable():
    assert kelly(0.4, 2.0) == 0.0


def test_quarter_kelly_fraction():
    stake = quarter_kelly_stake(0.6, 2.0, bankroll=1000.0)
    assert abs(stake - 50.0) < 1e-6


def test_quarter_kelly_never_negative():
    stake = quarter_kelly_stake(0.3, 2.0, bankroll=1000.0)
    assert stake >= 0.0


def test_quarter_kelly_respects_max_frac():
    stake = quarter_kelly_stake(0.99, 1.1, bankroll=1000.0, max_frac=0.05)
    assert stake <= 50.0
