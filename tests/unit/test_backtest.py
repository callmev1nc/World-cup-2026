"""Tests for backtest metrics and the quality gate."""
import pytest

from wcpredictor.backtest import rps, gate, evaluate


def test_rps_perfect_is_zero():
    probs = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]
    assert rps(probs, [0, 1]) == pytest.approx(0.0, abs=1e-12)


def test_rps_uniform_is_positive():
    assert rps([[1 / 3, 1 / 3, 1 / 3]], [0]) > 0


def test_gate_passes_when_model_not_worse():
    assert gate(log_loss_model=0.55, log_loss_market=0.57) is True


def test_gate_fails_when_model_materially_worse():
    assert gate(log_loss_model=0.60, log_loss_market=0.55) is False


def test_gate_tolerance_band():
    # Within tol of the market still passes.
    assert gate(log_loss_model=0.585, log_loss_market=0.57, tol=0.02) is True


def test_evaluate_with_market_returns_gate():
    probs = [[0.6, 0.3, 0.1], [0.2, 0.5, 0.3]]
    market = [[0.5, 0.3, 0.2], [0.3, 0.4, 0.3]]
    m = evaluate(probs, [0, 1], market)
    assert {"log_loss_model", "log_loss_market", "rps_model", "rps_market", "passes_gate"} <= set(m)
