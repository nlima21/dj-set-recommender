from dataclasses import dataclass
from typing import Optional
from src.camelot.wheel import compatibility_score, get_camelot, get_key_name

@dataclass
class Track:
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
    def camelot(self):
        return get_camelot(self.key, self.mode)

    @property
    def key_name(self):
        return get_key_name(self.key, self.mode)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "artist": self.artist, "tempo": self.tempo, "key_name": self.key_name, "camelot": self.camelot, "energy": self.energy, "danceability": self.danceability, "valence": self.valence, "uri": self.uri, "preview_url": self.preview_url}

def bpm_score(seed_tempo, candidate_tempo, tolerance=0.06):
    best = 0.0
    for ratio in [1.0, 2.0, 0.5]:
        adjusted = candidate_tempo * ratio
        diff = abs(seed_tempo - adjusted) / seed_tempo
        if diff <= tolerance:
            best = max(best, round(1.0 - (diff / tolerance), 3))
    return best

def energy_arc_score(target_energy, candidate_energy, arc_window=0.15):
    diff = abs(target_energy - candidate_energy)
    return round(1.0 - (diff / arc_window), 3) if diff <= arc_window else 0.0

def build_energy_arc(start_energy, arc_type="build", num_tracks=10):
    if arc_type == "build":
        step_size = (0.95 - start_energy) / max(num_tracks - 1, 1)
        return [round(start_energy + i * step_size, 3) for i in range(num_tracks)]
    elif arc_type == "peak":
        drop_at = int(num_tracks * 0.8)
        arc = [0.90] * drop_at
        drop_steps = num_tracks - drop_at
        for i in range(drop_steps):
            arc.append(round(0.90 - (i + 1) * (0.30 / drop_steps), 3))
        return arc
    elif arc_type == "journey":
        peak_at = int(num_tracks * 0.7)
        build = [round(start_energy + i * ((0.95 - start_energy) / peak_at), 3) for i in range(peak_at)]
        release_steps = num_tracks - peak_at
        release = [round(0.95 - i * (0.35 / release_steps), 3) for i in range(1, release_steps + 1)]
        return build + release
    else:
        return [start_energy] * num_tracks

def score_candidate(seed, candidate, target_energy, weights=None):
    if weights is None:
        weights = {"bpm": 0.40, "harmonic": 0.35, "energy": 0.25}
    bpm = bpm_score(seed.tempo, candidate.tempo)
    harmonic = compatibility_score(seed.key, seed.mode, candidate.key, candidate.mode)
    energy = energy_arc_score(target_energy, candidate.energy)
    return round(weights["bpm"] * bpm + weights["harmonic"] * harmonic + weights["energy"] * energy, 3)

def recommend_tracks(seed, candidates, arc_type="build", num_tracks=10, min_score=0.3):
    arc = build_energy_arc(seed.energy, arc_type, num_tracks)
    set_tracks = [{"track": seed.to_dict(), "score": 1.0, "position": 0, "target_energy": arc[0]}]
    used_ids = {seed.id}
    current = seed
    for position in range(1, num_tracks):
        target_energy = arc[position]
        best_score, best_candidate = -1, None
        for candidate in candidates:
            if candidate.id in used_ids:
                continue
            score = score_candidate(current, candidate, target_energy)
            if score > best_score and score >= min_score:
                best_score, best_candidate = score, candidate
        if best_candidate:
            set_tracks.append({"track": best_candidate.to_dict(), "score": best_score, "position": position, "target_energy": target_energy})
            used_ids.add(best_candidate.id)
            current = best_candidate
    return set_tracks
