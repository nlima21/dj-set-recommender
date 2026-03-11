"""
Unit tests for the Camelot Wheel and recommendation engine.
Run with: pytest tests/
"""

import pytest
from src.camelot.wheel import (
    get_camelot, get_key_name, get_compatible_keys, compatibility_score
)
from src.recommender.engine import (
    bpm_score, energy_arc_score, build_energy_arc, Track, score_candidate
)


# ── Camelot Tests ────────────────────────────────────────────────────────────

class TestCamelotWheel:

    def test_known_key_mapping(self):
        assert get_camelot(9, 0) == "8A"   # A minor
        assert get_camelot(0, 1) == "8B"   # C major
        assert get_camelot(7, 1) == "9B"   # G major

    def test_invalid_key_returns_unknown(self):
        assert get_camelot(-1, 0) == "Unknown"
        assert get_camelot(12, 1) == "Unknown"

    def test_key_name(self):
        assert get_key_name(9, 0) == "A min"
        assert get_key_name(0, 1) == "C maj"

    def test_compatible_keys_length(self):
        compatible = get_compatible_keys("8A")
        assert len(compatible) == 4

    def test_compatible_keys_includes_self(self):
        compatible = get_compatible_keys("8A")
        assert "8A" in compatible

    def test_compatible_keys_adjacent(self):
        compatible = get_compatible_keys("8A")
        assert "7A" in compatible
        assert "9A" in compatible

    def test_compatible_keys_relative(self):
        compatible = get_compatible_keys("8A")
        assert "8B" in compatible

    def test_compatibility_score_same_key(self):
        assert compatibility_score(9, 0, 9, 0) == 1.0

    def test_compatibility_score_compatible(self):
        # A minor (8A) and C major (8B) should be compatible
        score = compatibility_score(9, 0, 0, 1)
        assert score == 0.8

    def test_compatibility_score_incompatible(self):
        # A minor (8A) and F# minor (11A) are not compatible
        score = compatibility_score(9, 0, 6, 0)
        assert score == 0.0


# ── BPM Score Tests ──────────────────────────────────────────────────────────

class TestBpmScore:

    def test_exact_match(self):
        assert bpm_score(128.0, 128.0) == 1.0

    def test_within_tolerance(self):
        score = bpm_score(128.0, 132.0)
        assert 0 < score <= 1.0

    def test_outside_tolerance(self):
        assert bpm_score(128.0, 160.0) == 0.0

    def test_half_time(self):
        # 128 BPM should match a 64 BPM track (half-time)
        score = bpm_score(128.0, 64.0)
        assert score > 0.9

    def test_double_time(self):
        # 128 BPM should match a 256 BPM track (double-time)
        score = bpm_score(128.0, 256.0)
        assert score > 0.9


# ── Energy Arc Tests ─────────────────────────────────────────────────────────

class TestEnergyArc:

    def test_build_arc_increases(self):
        arc = build_energy_arc(0.5, "build", 10)
        assert arc[0] == 0.5
        assert arc[-1] > arc[0]

    def test_flat_arc_consistent(self):
        arc = build_energy_arc(0.7, "flat", 8)
        assert all(e == 0.7 for e in arc)

    def test_journey_arc_peaks_in_middle(self):
        arc = build_energy_arc(0.5, "journey", 10)
        peak_idx = arc.index(max(arc))
        assert 4 <= peak_idx <= 8  # Peak should be in middle-to-late portion

    def test_arc_length(self):
        arc = build_energy_arc(0.6, "build", 12)
        assert len(arc) == 12

    def test_energy_arc_score_exact(self):
        assert energy_arc_score(0.7, 0.7) == 1.0

    def test_energy_arc_score_within_window(self):
        score = energy_arc_score(0.7, 0.8)
        assert 0 < score < 1.0

    def test_energy_arc_score_outside(self):
        assert energy_arc_score(0.7, 0.95) == 0.0


# ── Track Scoring Tests ───────────────────────────────────────────────────────

def make_track(**kwargs) -> Track:
    defaults = dict(
        id="abc", name="Test Track", artist="Test Artist",
        tempo=128.0, key=9, mode=0, energy=0.8,
        danceability=0.7, valence=0.5, uri="spotify:track:abc"
    )
    defaults.update(kwargs)
    return Track(**defaults)


class TestScoreCandidate:

    def test_perfect_candidate_scores_high(self):
        seed = make_track()
        candidate = make_track(id="xyz", tempo=128.0, key=9, mode=0, energy=0.8)
        score = score_candidate(seed, candidate, target_energy=0.8)
        assert score >= 0.9

    def test_incompatible_candidate_scores_low(self):
        seed = make_track(tempo=128.0, key=9, mode=0, energy=0.8)
        candidate = make_track(id="xyz", tempo=160.0, key=6, mode=0, energy=0.3)
        score = score_candidate(seed, candidate, target_energy=0.8)
        assert score < 0.4

    def test_score_between_0_and_1(self):
        seed = make_track()
        candidate = make_track(id="xyz", tempo=130.0, key=0, mode=1, energy=0.75)
        score = score_candidate(seed, candidate, target_energy=0.8)
        assert 0.0 <= score <= 1.0
