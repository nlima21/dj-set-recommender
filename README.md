#  DJ Set Recommender

A data science project that builds harmonically compatible, energy-aware DJ set recommendations using the Spotify API and music theory (Camelot Wheel).

Input any track → get a full recommended set with BPM matching, harmonic key compatibility, and intelligent energy arc planning.

---

## Features

- **BPM Matching** — Finds tracks within ±6% tempo tolerance, including half-time/double-time awareness
- **Harmonic Mixing** — Uses the Camelot Wheel to recommend only harmonically compatible keys
- **Energy Arc Planning** — Build, Journey, Peak, and Flat arc modes to shape the vibe of your set
- **Composite Scoring** — Ranks candidates by a weighted score (40% BPM, 35% key, 25% energy)
- **Dash UI** — Clean, dark-mode dashboard with energy arc and BPM visualizations

---

## Tech Stack

| Layer | Library |
|---|---|
| Data | Spotify Web API via `spotipy` |
| Logic | Custom Python modules |
| UI | Dash by Plotly + Dash Bootstrap Components |
| Viz | Plotly |

---

## Project Structure

```
dj-set-recommender/
├── app.py                      # Dash application entry point
├── requirements.txt
├── .env.example                # Copy to .env and add your credentials
│
└── src/
    ├── spotify/
    │   └── client.py           # Spotify API: search, audio features, recommendations
    ├── camelot/
    │   └── wheel.py            # Camelot Wheel key mapping + harmonic compatibility
    └── recommender/
        └── engine.py           # Scoring engine + energy arc builder + set builder
```

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/dj-set-recommender.git
cd dj-set-recommender
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate      # Mac/Linux
venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Get Spotify API credentials

1. Go to [https://developer.spotify.com/dashboard](https://developer.spotify.com/dashboard)
2. Create a new app (any name, set redirect URI to `http://localhost:8050`)
3. Copy your **Client ID** and **Client Secret**

### 5. Set up environment variables

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
```

### 6. Run the app

```bash
python app.py
```

Open [http://localhost:8050](http://localhost:8050) in your browser.

---

## How It Works

### Camelot Wheel
The Camelot Wheel maps musical keys to numbered positions (1A–12B). Adjacent positions and relative major/minor pairs blend naturally. This project scores harmonic compatibility using these rules:

| Transition | Score |
|---|---|
| Same key | 1.0 |
| ±1 position or relative major/minor | 0.8 |
| Incompatible | 0.0 |

### Energy Arc Modes

| Mode | Description |
|---|---|
| **Build** | Gradually increases energy to ~0.95 |
| **Journey** | Builds to peak at 70%, then releases |
| **Peak** | Holds high energy, drops in final 20% |
| **Flat** | Maintains consistent energy throughout |

### Composite Score Formula

```
score = 0.40 × bpm_score + 0.35 × harmonic_score + 0.25 × energy_score
```

---

## Roadmap

- [ ] Last.fm integration for "people also listen to" layer
- [ ] Camelot Wheel graph visualization
- [ ] User auth to pull from personal Spotify library

---

## License

MIT
