"""
DJ Set Recommender - Dash Application
"""

import os
from dash import Dash, html, dcc, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from src.spotify.client import get_spotify_client, search_track, get_audio_features, get_recommendations
from src.recommender.engine import Track, recommend_tracks, build_energy_arc
from src.camelot.wheel import get_camelot, get_key_name

# ── App Init ────────────────────────────────────────────────────────────────

app = Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.CYBORG,
        "https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;600&display=swap"
    ],
    title="DJ Set Recommender"
)

# ── Styles ───────────────────────────────────────────────────────────────────

COLORS = {
    "bg": "#0a0a0f",
    "surface": "#13131a",
    "border": "#1e1e2e",
    "accent": "#00ff88",
    "accent2": "#ff3366",
    "accent3": "#7c3aed",
    "text": "#e2e2f0",
    "muted": "#6b6b8a",
}

CARD_STYLE = {
    "backgroundColor": COLORS["surface"],
    "border": f"1px solid {COLORS['border']}",
    "borderRadius": "12px",
    "padding": "24px",
}

# ── Layout ───────────────────────────────────────────────────────────────────

app.layout = html.Div(
    style={"backgroundColor": COLORS["bg"], "minHeight": "100vh", "fontFamily": "'DM Sans', sans-serif", "color": COLORS["text"]},
    children=[
        # Header
        html.Div(
            style={"borderBottom": f"1px solid {COLORS['border']}", "padding": "24px 40px", "display": "flex", "alignItems": "center", "gap": "16px"},
            children=[
                html.Div("◈", style={"fontSize": "28px", "color": COLORS["accent"]}),
                html.H1("DJ SET RECOMMENDER", style={
                    "margin": 0, "fontSize": "20px", "fontFamily": "'Space Mono', monospace",
                    "letterSpacing": "4px", "color": COLORS["text"]
                }),
                html.Span("BETA", style={
                    "fontSize": "10px", "fontFamily": "'Space Mono', monospace",
                    "backgroundColor": COLORS["accent3"], "color": "white",
                    "padding": "2px 8px", "borderRadius": "4px", "marginLeft": "8px"
                }),
            ]
        ),

        # Main content
        html.Div(
            style={"padding": "40px", "maxWidth": "1400px", "margin": "0 auto"},
            children=[

                # Search Row
                html.Div(
                    style={"display": "grid", "gridTemplateColumns": "1fr auto", "gap": "12px", "marginBottom": "32px"},
                    children=[
                        dcc.Input(
                            id="search-input",
                            type="text",
                            placeholder="Search for a track to start your set (e.g. 'Daft Punk Around The World')...",
                            debounce=False,
                            style={
                                "backgroundColor": COLORS["surface"],
                                "border": f"1px solid {COLORS['border']}",
                                "color": COLORS["text"],
                                "padding": "14px 20px",
                                "borderRadius": "8px",
                                "fontSize": "15px",
                                "width": "100%",
                                "outline": "none",
                                "fontFamily": "'DM Sans', sans-serif",
                            }
                        ),
                        html.Button(
                            "SEARCH",
                            id="search-btn",
                            style={
                                "backgroundColor": COLORS["accent"],
                                "color": COLORS["bg"],
                                "border": "none",
                                "padding": "14px 28px",
                                "borderRadius": "8px",
                                "fontFamily": "'Space Mono', monospace",
                                "fontSize": "13px",
                                "fontWeight": "700",
                                "cursor": "pointer",
                                "letterSpacing": "2px",
                                "whiteSpace": "nowrap",
                            }
                        )
                    ]
                ),

                # Seed Track Info
                html.Div(id="seed-track-display", style={"marginBottom": "32px"}),

                # Controls Row
                html.Div(
                    style={"display": "grid", "gridTemplateColumns": "repeat(3, 1fr)", "gap": "20px", "marginBottom": "32px"},
                    children=[
                        html.Div(
                            style=CARD_STYLE,
                            children=[
                                html.Label("ARC TYPE", style={"fontFamily": "'Space Mono', monospace", "fontSize": "11px", "letterSpacing": "2px", "color": COLORS["muted"], "marginBottom": "12px", "display": "block"}),
                                dcc.Dropdown(
                                    id="arc-type",
                                    options=[
                                        {"label": "▲ Build", "value": "build"},
                                        {"label": "▲▼ Journey", "value": "journey"},
                                        {"label": "── Peak", "value": "peak"},
                                        {"label": "─── Flat", "value": "flat"},
                                    ],
                                    value="journey",
                                    clearable=False,
                                    style={"backgroundColor": COLORS["bg"], "color": COLORS["text"]},
                                )
                            ]
                        ),
                        html.Div(
                            style=CARD_STYLE,
                            children=[
                                html.Label("SET LENGTH", style={"fontFamily": "'Space Mono', monospace", "fontSize": "11px", "letterSpacing": "2px", "color": COLORS["muted"], "marginBottom": "12px", "display": "block"}),
                                dcc.Slider(
                                    id="set-length",
                                    min=5, max=20, step=1, value=10,
                                    marks={5: "5", 10: "10", 15: "15", 20: "20"},
                                    tooltip={"placement": "bottom", "always_visible": False},
                                )
                            ]
                        ),
                        html.Div(
                            style=CARD_STYLE,
                            children=[
                                html.Label("MIN SCORE", style={"fontFamily": "'Space Mono', monospace", "fontSize": "11px", "letterSpacing": "2px", "color": COLORS["muted"], "marginBottom": "12px", "display": "block"}),
                                dcc.Slider(
                                    id="min-score",
                                    min=0.1, max=0.9, step=0.05, value=0.3,
                                    marks={0.1: "0.1", 0.5: "0.5", 0.9: "0.9"},
                                    tooltip={"placement": "bottom", "always_visible": False},
                                )
                            ]
                        ),
                    ]
                ),

                # Build Set Button
                html.Button(
                    "◈  BUILD SET",
                    id="build-btn",
                    disabled=True,
                    style={
                        "backgroundColor": COLORS["accent3"],
                        "color": "white",
                        "border": "none",
                        "padding": "16px 40px",
                        "borderRadius": "8px",
                        "fontFamily": "'Space Mono', monospace",
                        "fontSize": "14px",
                        "fontWeight": "700",
                        "cursor": "pointer",
                        "letterSpacing": "3px",
                        "marginBottom": "40px",
                        "display": "block",
                    }
                ),

                # Loading spinner
                dcc.Loading(
                    id="loading",
                    type="circle",
                    color=COLORS["accent"],
                    children=[
                        # Charts Row
                        html.Div(id="charts-display", style={"marginBottom": "32px"}),

                        # Tracklist
                        html.Div(id="tracklist-display"),
                    ]
                ),

                # Hidden store for seed track data
                dcc.Store(id="seed-store"),
            ]
        )
    ]
)


# ── Callbacks ─────────────────────────────────────────────────────────────────

@app.callback(
    Output("seed-track-display", "children"),
    Output("seed-store", "data"),
    Output("build-btn", "disabled"),
    Input("search-btn", "n_clicks"),
    State("search-input", "value"),
    prevent_initial_call=True
)
def search_and_display_seed(n_clicks, query):
    if not query:
        return html.Div(), None, True

    try:
        sp = get_spotify_client()
        track_meta = search_track(sp, query)
        if not track_meta:
            return html.Div("No track found. Try a different search.", style={"color": COLORS["accent2"]}), None, True

        features = get_audio_features(sp, track_meta["id"])
        if not features:
            return html.Div("Could not fetch audio features for this track.", style={"color": COLORS["accent2"]}), None, True

        seed_data = {**track_meta, **features}

        card = html.Div(
            style={**CARD_STYLE, "borderLeft": f"3px solid {COLORS['accent']}"},
            children=[
                html.Div("SEED TRACK", style={"fontFamily": "'Space Mono', monospace", "fontSize": "11px", "letterSpacing": "2px", "color": COLORS["accent"], "marginBottom": "10px"}),
                html.Div(
                    style={"display": "flex", "justifyContent": "space-between", "alignItems": "flex-start"},
                    children=[
                        html.Div([
                            html.H2(track_meta["name"], style={"margin": "0 0 4px 0", "fontSize": "22px"}),
                            html.Div(track_meta["artist"], style={"color": COLORS["muted"], "fontSize": "15px"}),
                        ]),
                        html.Div(
                            style={"display": "flex", "gap": "20px"},
                            children=[
                                _stat_pill(f"{features['tempo']} BPM", COLORS["accent"]),
                                _stat_pill(get_camelot(features["key"], features["mode"]), COLORS["accent3"]),
                                _stat_pill(get_key_name(features["key"], features["mode"]), COLORS["muted"]),
                                _stat_pill(f"Energy {features['energy']}", COLORS["accent2"]),
                            ]
                        )
                    ]
                )
            ]
        )

        return card, seed_data, False

    except Exception as e:
        return html.Div(f"Error: {str(e)}", style={"color": COLORS["accent2"]}), None, True


@app.callback(
    Output("charts-display", "children"),
    Output("tracklist-display", "children"),
    Input("build-btn", "n_clicks"),
    State("seed-store", "data"),
    State("arc-type", "value"),
    State("set-length", "value"),
    State("min-score", "value"),
    prevent_initial_call=True
)
def build_set(n_clicks, seed_data, arc_type, set_length, min_score):
    if not seed_data:
        return html.Div(), html.Div()

    try:
        sp = get_spotify_client()
        seed = Track(
            id=seed_data["id"],
            name=seed_data["name"],
            artist=seed_data["artist"],
            tempo=seed_data["tempo"],
            key=seed_data["key"],
            mode=seed_data["mode"],
            energy=seed_data["energy"],
            danceability=seed_data["danceability"],
            valence=seed_data["valence"],
            uri=seed_data["uri"],
            preview_url=seed_data.get("preview_url"),
        )

        # Fetch candidate pool
        raw_candidates = get_recommendations(
            sp, seed.id, seed.tempo, seed.energy, limit=50
        )

        candidates = []
        for c in raw_candidates:
            f = get_audio_features(sp, c["id"])
            if f:
                candidates.append(Track(
                    id=c["id"], name=c["name"], artist=c["artist"],
                    tempo=f["tempo"], key=f["key"], mode=f["mode"],
                    energy=f["energy"], danceability=f["danceability"],
                    valence=f["valence"], uri=c["uri"],
                    preview_url=c.get("preview_url")
                ))

        set_tracks = recommend_tracks(seed, candidates, arc_type, set_length, min_score)

        charts = _build_charts(set_tracks, arc_type, set_length, seed.energy)
        tracklist = _build_tracklist(set_tracks)

        return charts, tracklist

    except Exception as e:
        return html.Div(f"Error building set: {str(e)}", style={"color": COLORS["accent2"]}), html.Div()


# ── Chart Builders ────────────────────────────────────────────────────────────

def _build_charts(set_tracks, arc_type, set_length, seed_energy):
    positions = [t["position"] + 1 for t in set_tracks]
    energies = [t["track"]["energy"] for t in set_tracks]
    targets = build_energy_arc(seed_energy, arc_type, set_length)[:len(set_tracks)]
    names = [f"{t['track']['name'][:20]}..." if len(t['track']['name']) > 20 else t['track']['name'] for t in set_tracks]
    bpms = [t["track"]["tempo"] for t in set_tracks]
    scores = [t["score"] for t in set_tracks]
    camelots = [t["track"]["camelot"] for t in set_tracks]

    # Energy Arc Chart
    energy_fig = go.Figure()
    energy_fig.add_trace(go.Scatter(
        x=positions, y=targets,
        mode="lines",
        name="Target Arc",
        line=dict(color=COLORS["muted"], dash="dot", width=1),
    ))
    energy_fig.add_trace(go.Scatter(
        x=positions, y=energies,
        mode="lines+markers",
        name="Actual Energy",
        line=dict(color=COLORS["accent"], width=2),
        marker=dict(size=8, color=COLORS["accent"]),
        text=names,
        hovertemplate="<b>%{text}</b><br>Energy: %{y}<extra></extra>"
    ))
    energy_fig.update_layout(
        title="Energy Arc", paper_bgcolor=COLORS["surface"],
        plot_bgcolor=COLORS["surface"], font_color=COLORS["text"],
        font_family="'Space Mono', monospace",
        xaxis=dict(gridcolor=COLORS["border"], title="Track Position"),
        yaxis=dict(gridcolor=COLORS["border"], title="Energy", range=[0, 1]),
        legend=dict(bgcolor=COLORS["bg"]),
        margin=dict(t=50, b=40, l=50, r=20),
    )

    # BPM Chart
    bpm_fig = go.Figure(go.Bar(
        x=names, y=bpms,
        marker_color=[COLORS["accent3"] if i == 0 else COLORS["accent"] for i in range(len(bpms))],
        text=[f"{b} BPM" for b in bpms],
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>%{y} BPM<extra></extra>"
    ))
    bpm_fig.update_layout(
        title="BPM Progression", paper_bgcolor=COLORS["surface"],
        plot_bgcolor=COLORS["surface"], font_color=COLORS["text"],
        font_family="'Space Mono', monospace",
        xaxis=dict(gridcolor=COLORS["border"], tickangle=-30),
        yaxis=dict(gridcolor=COLORS["border"], title="BPM"),
        margin=dict(t=50, b=80, l=50, r=20),
    )

    return html.Div(
        style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "20px", "marginBottom": "32px"},
        children=[
            html.Div(style=CARD_STYLE, children=[dcc.Graph(figure=energy_fig, config={"displayModeBar": False})]),
            html.Div(style=CARD_STYLE, children=[dcc.Graph(figure=bpm_fig, config={"displayModeBar": False})]),
        ]
    )


def _build_tracklist(set_tracks):
    rows = []
    for i, item in enumerate(set_tracks):
        t = item["track"]
        score_color = COLORS["accent"] if item["score"] >= 0.7 else COLORS["accent3"] if item["score"] >= 0.4 else COLORS["accent2"]

        rows.append(html.Div(
            style={
                "display": "grid",
                "gridTemplateColumns": "40px 1fr 100px 80px 80px 80px 60px",
                "alignItems": "center",
                "gap": "16px",
                "padding": "14px 20px",
                "borderBottom": f"1px solid {COLORS['border']}",
                "backgroundColor": COLORS["surface"] if i % 2 == 0 else COLORS["bg"],
            },
            children=[
                html.Div(str(i + 1), style={"color": COLORS["muted"], "fontFamily": "'Space Mono', monospace", "fontSize": "13px"}),
                html.Div([
                    html.Div(t["name"], style={"fontWeight": "600", "fontSize": "14px"}),
                    html.Div(t["artist"], style={"color": COLORS["muted"], "fontSize": "12px", "marginTop": "2px"}),
                ]),
                html.Div(f"{t['tempo']} BPM", style={"fontFamily": "'Space Mono', monospace", "fontSize": "13px", "color": COLORS["accent"]}),
                html.Div(t["camelot"], style={"fontFamily": "'Space Mono', monospace", "fontSize": "13px", "color": COLORS["accent3"]}),
                html.Div(t["key_name"], style={"fontSize": "12px", "color": COLORS["muted"]}),
                html.Div(f"E: {t['energy']}", style={"fontSize": "13px", "color": COLORS["text"]}),
                html.Div(
                    f"{round(item['score'] * 100)}%",
                    style={"fontFamily": "'Space Mono', monospace", "fontSize": "12px", "color": score_color, "fontWeight": "700"}
                ),
            ]
        ))

    header = html.Div(
        style={
            "display": "grid",
            "gridTemplateColumns": "40px 1fr 100px 80px 80px 80px 60px",
            "gap": "16px",
            "padding": "12px 20px",
            "borderBottom": f"2px solid {COLORS['border']}",
        },
        children=[html.Div(col, style={"fontFamily": "'Space Mono', monospace", "fontSize": "10px", "letterSpacing": "2px", "color": COLORS["muted"]})
                  for col in ["#", "TRACK", "TEMPO", "KEY", "SCALE", "ENERGY", "SCORE"]]
    )

    return html.Div([
        html.Div("RECOMMENDED SET", style={"fontFamily": "'Space Mono', monospace", "fontSize": "12px", "letterSpacing": "3px", "color": COLORS["muted"], "marginBottom": "16px"}),
        html.Div(style={**CARD_STYLE, "padding": "0", "overflow": "hidden"}, children=[header] + rows)
    ])


def _stat_pill(text, color):
    return html.Div(
        text,
        style={
            "backgroundColor": COLORS["bg"],
            "border": f"1px solid {color}",
            "color": color,
            "padding": "6px 14px",
            "borderRadius": "20px",
            "fontFamily": "'Space Mono', monospace",
            "fontSize": "12px",
            "whiteSpace": "nowrap",
        }
    )


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True)
