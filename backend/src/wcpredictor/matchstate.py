from datetime import datetime


def state_of(
    fixture_status: str | None,
    has_prediction_data: bool,
    kickoff: datetime | None,
    now: datetime,
    result_known: bool,
    teams_set: bool,
) -> str:
    if not teams_set:
        return "pending"
    if result_known:
        return "finished"
    if kickoff and kickoff < now and not result_known:
        return "waiting_result"
    if not has_prediction_data:
        return "scheduled"
    return "predictable"
