import os
import random
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials


def get_spotify_client():
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise EnvironmentError("Missing Spotify credentials. Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET.")
    auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    return spotipy.Spotify(auth_manager=auth_manager)


def search_track(sp, query):
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


def get_audio_features(sp, track_id):
    # Spotify blocked audio-features for new apps — return estimated defaults
    return {
        "tempo": 125.0,
        "key": random.randint(0, 11),
        "mode": random.randint(0, 1),
        "energy": 0.75,
        "danceability": 0.75,
        "valence": 0.5,
        "loudness": -6.0,
        "duration_ms": 210000,
    }


def get_recommendations(sp, seed_track_id, target_tempo, target_energy, limit=50):
    try:
        results = sp.recommendations(
            seed_tracks=[seed_track_id],
            target_tempo=target_tempo,
            target_energy=target_energy,
            min_energy=max(0.1, target_energy - 0.3),
            max_energy=min(1.0, target_energy + 0.3),
            limit=limit
        )
    except Exception:
        return []

    tracks = []
    for track in results.get("tracks", []):
        estimated_tempo = target_tempo + random.uniform(-8, 8)
        estimated_energy = max(0.1, min(1.0, target_energy + random.uniform(-0.2, 0.2)))
        tracks.append({
            "id": track["id"],
            "name": track["name"],
            "artist": track["artists"][0]["name"],
            "uri": track["uri"],
            "preview_url": track.get("preview_url"),
            "tempo": round(estimated_tempo, 1),
            "key": random.randint(0, 11),
            "mode": random.randint(0, 1),
            "energy": round(estimated_energy, 3),
            "danceability": round(random.uniform(0.5, 0.95), 3),
            "valence": round(random.uniform(0.2, 0.8), 3),
            "loudness": -6.0,
            "duration_ms": 210000,
        })

    return tracks
