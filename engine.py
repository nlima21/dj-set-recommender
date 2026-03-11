"""
DJ Recommendation Engine

Scores candidate tracks against a seed track using:
    - BPM compatibility (tempo matching with tolerance)
    - Harmonic compatibility (Camelot Wheel)
    - Energy arc planning (gradual energy progression)

Builds a scored, ordered tracklist optimized for DJ mixing.
"""

from dataclasses import dataclass
from typing import Optional
from src.camelot.wheel import compatibility_score, get_camelot, get_key_name


@dataclass
class Track:
    """Represents a track with all DJ-relevant metadata."""
    id: str
    name: str
    artist: str
    tempo: float
    key: int
    mode: int
    energy: float
    danceability: float
    valence: float
    uri: str
    preview_url: Optional[str] = None

    @property
    def camelot(self) -> str:
        return get_camelot(self.key, self.mode)

    @property
    def key_name(self) -> str:
        return get_key_name(self.key, self.mode)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "artist": self.artist,
            "tempo": self.tempo,
            "key_name": self.key_name,
            "camelot": self.camelot,
            "energy": self.energy,
            "danceability": self.danceability,
            "valence": self.valence,
            "uri": self.uri,
            "preview_url": self.preview_url,
        }


def bpm_score(seed_tempo: float, candidate_tempo: float, tolerance: float = 0.06) -> float:
    """
    Score BPM compatibility. Returns 1.0 for exact match, scaling down
    to 0.0 outside the tolerance window.

    Also handles half-time / double-time matching (e.g. 128 BPM ↔ 64 BPM).

    Args:
        seed_tempo: BPM of the seed track
        candidate_tempo: BPM of the candidate track
        tolerance: Max fractional difference allowed (default ±6%)
    """
    ratios = [1.0, 2.0, 0.5]  # Normal, double-time, half-time
    best = 0.0

    for ratio in ratios:
        adjusted = candidate_tempo * ratio
        diff = abs(seed_tempo - adjusted) / seed_tempo
        if diff <= tolerance:
            score = 1.0 - (diff / tolerance)
            best = max(best, score)

    return round(best, 3)


def energy_arc_score(
    target_energy: float,
    candidate_energy: float,
    arc_window: float = 0.15
) -> float:
    """
    Score how well a candidate's energy fits the target energy level
    in the set arc.

    Args:
        target_energy: Desired energy level at this point in the arc
        candidate_energy: Energy of the candidate track
        arc_window: Acceptable energy deviation (default ±0.15)
    """
    diff = abs(target_energy - candidate_energy)
    if diff <= arc_window:
        return round(1.0 - (diff / arc_window), 3)
    return 0.0


def score_candidate(
    seed: Track,
    candidate: Track,
    target_energy: float,
    weights: dict = None
) -> float:
    """
    Compute a composite DJ compatibility score for a candidate track
    relative to the seed track and desired energy level.

    Weights:
        bpm: 0.4       Tempo is critical for mixing
        harmonic: 0.35 Key compatibility is very important
        energy: 0.25   Energy arc fit

    Returns:
        Float score between 0.0 and 1.0
    """
    if weights is None:
        weights = {"bpm": 0.40, "harmonic": 0.35, "energy": 0.25}

    bpm = bpm_score(seed.tempo, candidate.tempo)
    harmonic = compatibility_score(seed.key, seed.mode, candidate.key, candidate.mode)
    energy = energy_arc_score(target_energy, candidate.energy)

    total = (
        weights["bpm"] * bpm
        + weights["harmonic"] * harmonic
        + weights["energy"] * energy
    )

    return round(total, 3)


def build_energy_arc(
    start_energy: float,
    arc_type: str = "build",
    num_tracks: int = 10
) -> list[float]:
    """
    Generate a list of target energy values representing the desired
    arc of a DJ set.

    Arc types:
        build:    Gradually increases from start_energy to ~0.95
        peak:     Starts high, sustains peak, then drops
        journey:  Build → peak → release curve
        flat:     Maintain consistent energy level throughout

    Args:
        start_energy: Energy level of the seed/first track
        arc_type: One of 'build', 'peak', 'journey', 'flat'
        num_tracks: Total tracks in the set (including seed)

    Returns:
        List of float energy targets, one per track position
    """
    steps = num_tracks - 1  # Exclude seed

    if arc_type == "build":
        step_size = (0.95 - start_energy) / max(steps, 1)
        return [round(start_energy + i * step_size, 3) for i in range(num_tracks)]

    elif arc_type == "peak":
        # Start near top, sustain, then drop last 20%
        drop_at = int(num_tracks * 0.8)
        arc = [0.90] * drop_at
        drop_steps = num_tracks - drop_at
        for i in range(drop_steps):
            arc.append(round(0.90 - (i + 1) * (0.30 / drop_steps), 3))
        return arc

    elif arc_type == "journey":
        # Build to peak at 70% then release
        peak_at = int(num_tracks * 0.7)
        build = [round(start_energy + i * ((0.95 - start_energy) / peak_at), 3)
                 for i in range(peak_at)]
        release_steps = num_tracks - peak_at
        release = [round(0.95 - i * (0.35 / release_steps), 3)
                   for i in range(1, release_steps + 1)]
        return build + release

    else:  # flat
        return [start_energy] * num_tracks


def recommend_tracks(
    seed: Track,
    candidates: list[Track],
    arc_type: str = "build",
    num_tracks: int = 10,
    min_score: float = 0.3
) -> list[dict]:
    """
    Build a recommended DJ set from candidate tracks.

    Args:
        seed: The starting track
        candidates: Pool of candidate tracks with audio features
        arc_type: Energy arc shape ('build', 'peak', 'journey', 'flat')
        num_tracks: Desired set length including seed
        min_score: Minimum composite score to include a track

    Returns:
        List of dicts with track info + score + arc position
    """
    arc = build_energy_arc(seed.energy, arc_type, num_tracks)
    set_tracks = [{"track": seed.to_dict(), "score": 1.0, "position": 0,
                   "target_energy": arc[0]}]

    used_ids = {seed.id}
    current = seed

    for position in range(1, num_tracks):
        target_energy = arc[position]
        best_score = -1
        best_candidate = None

        for candidate in candidates:
            if candidate.id in used_ids:
                continue

            score = score_candidate(current, candidate, target_energy)
            if score > best_score and score >= min_score:
                best_score = score
                best_candidate = candidate

        if best_candidate:
            set_tracks.append({
                "track": best_candidate.to_dict(),
                "score": best_score,
                "position": position,
                "target_energy": target_energy,
            })
            used_ids.add(best_candidate.id)
            current = best_candidate

    return set_tracks
