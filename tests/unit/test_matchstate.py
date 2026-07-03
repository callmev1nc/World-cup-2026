from datetime import datetime, timezone
from wcpredictor.matchstate import state_of


def test_pending_no_teams():
    assert state_of(None, False, None, datetime.now(timezone.utc), False, False) == "pending"


def test_finished():
    assert state_of("finished", True, None, datetime.now(timezone.utc), True, True) == "finished"


def test_waiting_result():
    kickoff = datetime(2025, 1, 1, tzinfo=timezone.utc)
    assert state_of("played", True, kickoff, datetime.now(timezone.utc), False, True) == "waiting_result"


def test_scheduled_no_data():
    kickoff = datetime(2099, 1, 1, tzinfo=timezone.utc)
    assert state_of("not_started", False, kickoff, datetime.now(timezone.utc), False, True) == "scheduled"


def test_predictable():
    kickoff = datetime(2099, 1, 1, tzinfo=timezone.utc)
    assert state_of("not_started", True, kickoff, datetime.now(timezone.utc), False, True) == "predictable"
