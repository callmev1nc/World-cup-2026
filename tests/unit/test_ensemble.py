"""Tests for the model/market ensemble blend."""
import pytest

from wcpredictor.models.ensemble import blend


def test_blend_midpoint_alpha_half():
    b = blend([1.0, 0.0, 0.0], [0.0, 1.0, 0.0], alpha=0.5)
    assert b == pytest.approx([0.5, 0.5, 0.0])


def test_blend_sums_to_one():
    b = blend([0.6, 0.3, 0.1], [0.5, 0.3, 0.2], alpha=0.4)
    assert abs(sum(b) - 1.0) < 1e-12


def test_blend_alpha_one_returns_model():
    b = blend([0.6, 0.3, 0.1], [0.5, 0.3, 0.2], alpha=1.0)
    assert b == pytest.approx([0.6, 0.3, 0.1])


def test_blend_alpha_zero_returns_market():
    b = blend([0.6, 0.3, 0.1], [0.5, 0.3, 0.2], alpha=0.0)
    assert b == pytest.approx([0.5, 0.3, 0.2])


def test_blend_rejects_mismatched_lengths():
    with pytest.raises(ValueError):
        blend([0.5, 0.5], [1.0], alpha=0.5)
