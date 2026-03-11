"""
Spotify API client for fetching track audio features and recommendations.
Uses the spotipy library to interact with the Spotify Web API.
"""

import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from typing import Optional


def get_spotify_client() -> spotipy.Spotify:
    """
    Initialize and return an authenticated Spotify client.
    Reads credentials from environment variables:
        SPOTIFY_CLIENT_ID
        SPOTIFY_CLIENT_SECRET
    """
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise EnvironmentError(
            "Missing Spotify credentials. Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET."
        )

    auth_manager = SpotifyClientCredentials(
        client_id=client_id,
        client_secret=client_secret
    )
    return spotipy.Spotify(auth_manager=auth_manager)


def search_track(sp: spotipy.Spotify, query: str) -> Optional[dict]:
    """
    Search for a track by name/artist and return the top result.

    Args:
        sp: Authenticated Spotify client
        query: Search string e.g. "Technasia Atom"

    Returns:
        Dict with track id, name, artist, and URI or None if not found
    """
    results = sp.search(q=query, type="track", limit=1)
    items = results.get("tracks", {}).get("items", [])

    if not items:
        return None

    track = items[0]
    return {
        "id": track["id"],
        "name": track["name"],
        "artist": track["artists"][0]["name"],
        "uri": track["uri"],
        "album": track["album"]["name"],
        "preview_url": track.get("preview_url"),
    }


def get_audio_features(sp: spotipy.Spotify, track_id: str) -> Optional[dict]:
    """
    Fetch audio features for a single track.

    Returns key DJ-relevant fields:
        - tempo (BPM)
        - key (0-11 Pitch Class notation)
        - mode (0 = minor, 1 = major)
        - energy (0.0 - 1.0)
        - danceability (0.0 - 1.0)
        - valence (0.0 - 1.0, musical positiveness)
    """
    features = sp.audio_features([track_id])

    if not features or features[0] is None:
        return None

    f = features[0]
    return {
        "tempo": round(f["tempo"], 1),
        "key": f["key"],
        "mode": f["mode"],
        "energy": round(f["energy"], 3),
        "danceability": round(f["danceability"], 3),
        "valence": round(f["valence"], 3),
        "loudness": round(f["loudness"], 2),
        "duration_ms": f["duration_ms"],
    }


def get_recommendations(
    sp: spotipy.Spotify,
    seed_track_id: str,
    target_tempo: float,
    target_energy: float,
    limit: int = 20
) -> list[dict]:
    """
    Fetch Spotify recommendations seeded from a track, targeting specific
    tempo and energy values for DJ compatibility.

    Args:
        sp: Authenticated Spotify client
        seed_track_id: Spotify track ID to seed from
        target_tempo: Desired BPM to target
        target_energy: Desired energy level (0.0 - 1.0)
        limit: Number of recommendations to return (max 100)

    Returns:
        List of track dicts with id, name, artist
    """
    results = sp.recommendations(
        seed_tracks=[seed_track_id],
        target_tempo=target_tempo,
        target_energy=target_energy,
        limit=limit
    )

    tracks = []
    for track in results.get("tracks", []):
        tracks.append({
            "id": track["id"],
            "name": track["name"],
            "artist": track["artists"][0]["name"],
            "uri": track["uri"],
            "preview_url": track.get("preview_url"),
        })

    return tracks
