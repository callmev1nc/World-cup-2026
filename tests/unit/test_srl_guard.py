"""Tests for the SRL (simulated reality) guard."""
import pytest

from wcpredictor.clients.srl_guard import SRLRejected, assert_not_srl, is_srl


def test_detects_simulated_reality_names():
    assert is_srl("Simulated Reality League")
    assert is_srl("Man Utd SRL vs PSV SRL")
    assert is_srl("Virtual Premier League")


def test_allows_real_competitions():
    assert not is_srl("FIFA World Cup")
    assert not is_srl("UEFA Euro")
    assert not is_srl("La Liga")


def test_assert_raises_on_srl():
    with pytest.raises(SRLRejected):
        assert_not_srl("Simulated Reality League")


def test_assert_passes_for_real_competitions():
    assert_not_srl("FIFA World Cup")  # must not raise
