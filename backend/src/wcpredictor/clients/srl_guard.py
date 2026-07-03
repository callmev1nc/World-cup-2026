"""Reject Simulated Reality League (SRL) data from the real-football model.

SRL matches are virtual (Sportradar's "Simulated Reality" engine, offered by
SportyBet/Bet9ja/Betway etc.) — outcomes come from historical profiles + the
simulator's RNG, so the live signals that power real-football prediction
(form, injuries, lineups, rest) are irrelevant. Real-World-Cup prediction does
NOT transfer to SRL, so we refuse to ingest it.
"""
from __future__ import annotations

import re

_SRL_RE = re.compile(r"\bsrl\b", re.IGNORECASE)
_SRL_MARKERS = ("simulated reality", "virtual", "efootball", "esports")


class SRLRejected(ValueError):
    """Raised when SRL (simulated) data is offered to the real-football model."""


def is_srl(name: str | None) -> bool:
    """True if a competition/league name looks like a simulated-reality product."""
    if not name:
        return False
    low = name.lower()
    return bool(_SRL_RE.search(low)) or any(marker in low for marker in _SRL_MARKERS)


def assert_not_srl(name: str | None) -> None:
    """Raise SRLRejected if the name is simulated-reality data."""
    if is_srl(name):
        raise SRLRejected(f"SRL data rejected (simulated, not real football): {name!r}")
