import os
import dash
from dash import dcc, html, Input, Output, State, ctx, ALL, MATCH
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import numpy as np

import tab_overview
import tab_morphology
import tab_acoustics
import tab_comparison

from config import PLOT_LAYOUT, AXIS_STYLE, apply_grid, mat_color
from data import (
    samples, fibers, acoustic,
    MATERIALS, FREQ_COLS, FREQ_VALS,
    _has, _empty_fig, _sub, _filter_ids,
)

BATCHES = sorted(samples["batch"].unique().tolist()) if _has(samples, "batch") else []

app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.FLATLY,
        "https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap",
    ],
    title="FiberScope — ESIEE Paris",
    suppress_callback_exceptions=True,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
server = app.server

# en-tête principal
header = html.Div(style={
    "background":  "linear-gradient(135deg, #0A1628 0%, #0F2D5E 55%, #1D4ED8 100%)",
    "padding":     "44px 32px 38px 32px",
    "textAlign":   "center",
}, children=[
    html.Div("ESIEE PARIS — PROJET E4", style={
        "color": "#60A5FA", "fontSize": "11px", "fontWeight": 700,
        "letterSpacing": "0.18em", "textTransform": "uppercase",
        "marginBottom": "12px",
    }),
    html.H1("FiberScope", style={
        "color": "white", "fontWeight": 800,
        "fontSize": "44px", "letterSpacing": "-2px",
        "marginBottom": "10px",
    }),
    html.P(
        "Caractérisation morphologique des réseaux fibreux par microtomographie X",
        style={"color": "#BAE6FD", "fontSize": "15px", "marginBottom": "20px"}
    ),
    html.Div([
        html.Span([
            html.Span(style={
                "display": "inline-block",
                "width": "11px", "height": "11px",
                "borderRadius": "50%",
                "backgroundColor": mat_color(m, i),
                "marginRight": "6px",
                "verticalAlign": "middle",
                "border": "2px solid rgba(255,255,255,0.4)",
            }),
            html.Span(m, style={
                "fontSize": "12px", "color": "white",
                "fontWeight": 600, "verticalAlign": "middle",
            }),
        ], style={"marginRight": "16px", "whiteSpace": "nowrap"})
        for i, m in enumerate(MATERIALS)
    ], style={
        "display": "flex", "flexWrap": "wrap",
        "justifyContent": "center", "gap": "6px", "marginTop": "4px",
    }) if MATERIALS else html.Span(),
])

# barre de filtres
sidebar = dbc.Row(className="mt-4 mb-3 px-3", children=[
    dbc.Col(dbc.Card(style={
        "borderRadius": "12px", "border": "1px solid #E2E8F0",
        "boxShadow": "0 2px 6px rgba(0,0,0,0.04)", "backgroundColor": "white",
    }, children=[
        dbc.CardBody(style={"padding": "16px 20px"}, children=[
            html.P(
                "Filtrez les données par matériau et par lot de fabrication. "
                "Tous les graphiques se mettent à jour instantanément.",
                style={"fontSize": "12px", "color": "#64748B", "marginBottom": "14px"},
            ),
            html.Div(style={
                "display": "flex", "gap": "16px",
                "alignItems": "flex-end", "flexWrap": "wrap",
            }, children=[
                html.Div(style={"flex": "2 1 180px"}, children=[
                    html.Label("Matériau", style={
                        "fontWeight": 700, "fontSize": "12px",
                        "color": "#334155", "marginBottom": "5px", "display": "block",
                    }),
                    dcc.Dropdown(
                        id="filter-material",
                        options=[{"label": m, "value": m} for m in MATERIALS],
                        multi=True, placeholder="Tous les matériaux",
                        style={"fontSize": "13px"},
                    ),
                ]),
                html.Div(style={"flex": "2 1 180px"}, children=[
                    html.Label("Lot de fabrication", style={
                        "fontWeight": 700, "fontSize": "12px",
                        "color": "#334155", "marginBottom": "5px", "display": "block",
                    }),
                    dcc.Dropdown(
                        id="filter-batch",
                        options=[{"label": b, "value": b} for b in BATCHES],
                        multi=True, placeholder="Tous les lots",
                        style={"fontSize": "13px"},
                    ),
                ]),
                dbc.Button("Tout afficher", id="btn-reset", style={
                    "border": "1px solid #CBD5E1", "backgroundColor": "white",
                    "color": "#475569", "fontWeight": 700, "fontSize": "12px",
                    "whiteSpace": "nowrap", "borderRadius": "8px",
                    "padding": "9px 18px", "flexShrink": 0, "alignSelf": "flex-end",
                }),
            ]),
        ]),
    ]))
])

# pied de page
footer = html.Div(style={
    "textAlign": "center", "padding": "24px 16px",
    "color": "#94A3B8", "fontSize": "12px",
}, children=[
    html.Hr(style={"borderColor": "#E2E8F0", "marginBottom": "14px"}),
    html.P("FiberScope — Projet E4 — ESIEE Paris — Microtomographie X & Caractérisation fibreuse",
           style={"margin": 0}),
])

app.layout = dbc.Container(fluid=True, style={
    "backgroundColor": "#F1F5F9",
    "minHeight": "100vh",
    "fontFamily": "Inter, system-ui, sans-serif",
}, children=[
    dcc.Store(id="acou-data-store"),
    dcc.Store(id="mat-vis-store", data=list(MATERIALS)),
    header,
    sidebar,
    html.Div(style={"padding": "0 16px"}, children=[
        dcc.Tabs(
            id="main-tabs", value="overview",
            style={"borderBottom": "2px solid #E2E8F0", "marginBottom": "0"},
            children=[
                tab_overview.get_tab(),
                tab_morphology.get_tab(),
                tab_acoustics.get_tab(),
                tab_comparison.get_tab(),
            ],
        ),
    ]),
    footer,
])


# callback principal : met à jour tous les graphiques selon les filtres
@app.callback(
    Output("row-kpis",                "children"),
    Output("graph-diameter",          "figure"),
    Output("graph-diameter-kde",      "figure"),
    Output("graph-orientation-polar", "figure"),
    Output("graph-resistivity",       "figure"),
    Output("graph-summary-table",     "figure"),
    Output("graph-ranking-bar",       "figure"),
    Output("graph-morph-scatter",     "figure"),
    Output("acou-data-store",         "data"),
    Input({"type": "mat-store", "graph": "graph-diameter"},          "data"),
    Input({"type": "mat-store", "graph": "graph-diameter-kde"},      "data"),
    Input({"type": "mat-store", "graph": "graph-orientation-polar"}, "data"),
    Input({"type": "mat-store", "graph": "graph-resistivity"},       "data"),
    Input("filter-batch",  "value"),
)
def update_all(mats_diam, mats_kde, mats_polar, mats_res, bat_sel):
    ids_diam,  samp_diam  = _filter_ids(mats_diam, bat_sel)
    ids_kde,   _          = _filter_ids(mats_kde, bat_sel)
    ids_polar, _          = _filter_ids(mats_polar, bat_sel)
    ids_res,   samp_res   = _filter_ids(mats_res, bat_sel)
    ids_all,   samp_all   = _filter_ids(MATERIALS, bat_sel)

    fib_diam  = _sub(fibers,   ids_diam)
    fib_kde   = _sub(fibers,   ids_kde)
    fib_polar = _sub(fibers,   ids_polar)
    aco_res   = _sub(acoustic, ids_res)
    samp_f    = samp_all
    fib_f     = _sub(fibers,   ids_all)
    aco_f     = _sub(acoustic, ids_all)


    kpis = tab_overview.build_kpis(samp_f, fib_f, aco_f)

    fig_diam    = tab_morphology.build_diameter(fib_diam)
    fig_kde     = tab_morphology.build_kde(fib_kde)
    fig_polar   = tab_morphology.build_polar(fib_polar)
    fig_res     = tab_acoustics.build_resistivity(samp_res, aco_res)
    fig_summary = tab_overview.build_summary_table(samp_f, aco_f)
    fig_ranking = tab_comparison.build_ranking(aco_f)
    fig_scatter = tab_comparison.build_scatter(aco_f)

    # préparation des données pour le graphique d'absorption
    acou_store = []
    if not aco_f.empty and all(c in aco_f.columns for c in FREQ_COLS) and _has(aco_f, "sample_id", "material"):
        cols = ["sample_id", "material"] + FREQ_COLS
        acou_store = aco_f[cols].dropna(subset=FREQ_COLS).to_dict("records")

    return (kpis, fig_diam, fig_kde, fig_polar, fig_res, fig_summary, fig_ranking, fig_scatter, acou_store)


# callback : panneau de sélection des échantillons acoustiques
@app.callback(
    Output("acou-checklist", "options"),
    Output("acou-checklist", "value"),
    Input("acou-data-store",    "data"),
    Input("acou-search",        "value"),
    Input("acou-select-all",    "n_clicks"),
    Input("acou-deselect-all",  "n_clicks"),
    State("acou-checklist",     "value"),
)
def update_acoustic_options(store_data, search, _n_all, _n_none, current_val):
    records = store_data or []

    mats_idx = {}
    for idx, rec in enumerate(records):
        m = rec.get("material", "?")
        if m not in mats_idx:
            mats_idx[m] = len(mats_idx)

    all_options = []
    for rec in records:
        sid   = str(rec["sample_id"])
        mat   = rec.get("material", "?")
        color = mat_color(mat, mats_idx.get(mat, 0))
        label = html.Span([
            html.Span("■ ", style={"color": color, "fontWeight": "bold", "fontSize": "14px"}),
            html.Span(sid, style={"fontWeight": 600, "fontSize": "11px", "color": "#1E293B"}),
            html.Span(f" {mat}", style={"fontSize": "10px", "color": "#94A3B8"}),
        ])
        all_options.append({"label": label, "value": sid})

    if search:
        s = search.lower()
        filtered = [
            (o, rec) for o, rec in zip(all_options, records)
            if s in str(rec["sample_id"]).lower() or s in rec.get("material", "").lower()
        ]
        filtered_options = [o for o, _ in filtered]
    else:
        filtered_options = all_options

    all_ids      = [o["value"] for o in all_options]
    filtered_ids = [o["value"] for o in filtered_options]

    triggered_id = ctx.triggered_id if ctx.triggered_id else ""

    if triggered_id == "acou-select-all":
        new_val = filtered_ids
    elif triggered_id == "acou-deselect-all":
        new_val = []
    elif triggered_id == "acou-data-store":
        new_val = [filtered_ids[0]] if filtered_ids else []
    else:
        new_val = [v for v in (current_val or []) if v in all_ids]

    return filtered_options, new_val


# callback : graphique des courbes d'absorption par échantillon
@app.callback(
    Output("graph-absorption", "figure"),
    Input("acou-checklist",  "value"),
    Input("acou-data-store", "data"),
)
def update_absorption_graph(selected_ids, store_data):
    records      = store_data or []
    selected_ids = selected_ids or []

    if not records:
        return _empty_fig("Données d'absorption acoustique non disponibles")

    if not selected_ids:
        return _empty_fig("Sélectionnez au moins un échantillon dans la liste à droite →")

    mats_idx = {}
    for rec in records:
        m = rec.get("material", "?")
        if m not in mats_idx:
            mats_idx[m] = len(mats_idx)

    fig = go.Figure()
    for rec in records:
        sid = str(rec["sample_id"])
        if sid not in selected_ids:
            continue
        mat  = rec.get("material", "?")
        vals = [rec.get(c) for c in FREQ_COLS]
        if any(v is None or (isinstance(v, float) and np.isnan(v)) for v in vals):
            continue
        color = mat_color(mat, mats_idx.get(mat, 0))
        fig.add_trace(go.Scatter(
            x=FREQ_VALS, y=vals,
            mode="lines+markers",
            name=f"{sid} ({mat})",
            line=dict(color=color, width=2.5),
            marker=dict(size=6, line=dict(width=1, color="white")),
            hovertemplate=f"<b>{sid} ({mat})</b><br>%{{x}} Hz → α = %{{y:.3f}}<extra></extra>",
        ))

    if len(selected_ids) > 1:
        sel_recs = [r for r in records if str(r["sample_id"]) in selected_ids]
        medians  = [
            float(np.median([r[c] for r in sel_recs if r.get(c) is not None]))
            for c in FREQ_COLS
        ]
        if not any(np.isnan(m) for m in medians):
            fig.add_trace(go.Scatter(
                x=FREQ_VALS, y=medians, mode="lines",
                name="Médiane",
                line=dict(color="#0F172A", width=3, dash="dot"),
                hovertemplate="Médiane sélection<br>%{x} Hz → α = %{y:.3f}<extra></extra>",
            ))

    fig.update_layout(
        **PLOT_LAYOUT,
        xaxis=dict(
            title="Fréquence (Hz)",
            tickvals=FREQ_VALS,
            ticktext=["250 Hz", "500 Hz", "1 kHz", "2 kHz", "4 kHz"],
            **{k: v for k, v in AXIS_STYLE.items() if k != "title_font"},
            title_font=AXIS_STYLE["title_font"],
        ),
        yaxis=dict(
            title="Coefficient d'absorption α",
            range=[0, 1.05],
            **{k: v for k, v in AXIS_STYLE.items() if k != "title_font"},
            title_font=AXIS_STYLE["title_font"],
        ),
        legend=dict(
            orientation="v", x=1.01, y=1,
            font_size=10, bgcolor="rgba(248,250,252,0.9)",
            bordercolor="#CBD5E1", borderwidth=1,
        ),
    )
    apply_grid(fig)
    return fig


# callback : toggle visibilité des matériaux par graphique
@app.callback(
    Output({"type": "mat-store", "graph": MATCH}, "data"),
    Input({"type": "mat-g-cb",  "graph": MATCH, "mat": ALL}, "n_clicks"),
    Input({"type": "mat-g-all", "graph": MATCH}, "n_clicks"),
    State({"type": "mat-store", "graph": MATCH}, "data"),
    prevent_initial_call=True,
)
def toggle_per_graph(mat_clicks, _all_click, current):
    triggered = ctx.triggered_id
    vis = list(current if current is not None else MATERIALS)
    if isinstance(triggered, dict):
        if triggered.get("type") == "mat-g-cb":
            mat = triggered["mat"]
            if mat in vis:
                vis.remove(mat)
            else:
                vis.append(mat)
        elif triggered.get("type") == "mat-g-all":
            vis = [] if set(vis) == set(MATERIALS) else list(MATERIALS)
    return vis


# callback : synchronisation des classes CSS des cases à cocher
@app.callback(
    Output({"type": "mat-g-cb",  "graph": MATCH, "mat": ALL}, "className"),
    Output({"type": "mat-g-all", "graph": MATCH}, "className"),
    Input({"type": "mat-store",  "graph": MATCH}, "data"),
)
def sync_per_graph_classes(vis_data):
    vis = set(vis_data or [])
    mat_classes = [
        "mat-cb-item mat-cb-item--on" if spec["id"]["mat"] in vis
        else "mat-cb-item mat-cb-item--off"
        for spec in ctx.outputs_list[0]
    ]
    all_class = (
        "mat-cb-item mat-cb-item--on" if vis == set(MATERIALS)
        else "mat-cb-item mat-cb-item--off"
    )
    return mat_classes, [all_class] * len(ctx.outputs_list[1])


# callback : réinitialisation des filtres
@app.callback(
    Output("mat-vis-store",   "data",  allow_duplicate=True),
    Output("filter-batch",    "value"),
    Output("filter-material", "value"),
    Input("btn-reset", "n_clicks"),
    prevent_initial_call=True,
)
def reset_filters(_):
    return list(MATERIALS), None, None


# callback : graphique de robustesse (données independantes)
@app.callback(
    Output("graph-robustness", "figure"),
    Input("filter-batch", "value"),
)
def update_robustness(bat_sel):
    from data import _load
    rob = _load("robustness.csv")
    if rob.empty:
        return _empty_fig("Données de robustesse non disponibles (robustness.csv)")

    if bat_sel and "sample_id" in rob.columns and _has(samples, "batch", "sample_id"):
        ids_in_batch = samples[samples["batch"].isin(bat_sel)]["sample_id"].tolist()
        rob = rob[rob["sample_id"].isin(ids_in_batch)]

    if rob.empty:
        return _empty_fig("Aucune donnée après filtrage")

    fig = go.Figure()
    palette = ["#3B82F6", "#EF4444", "#22C55E", "#F59E0B", "#8B5CF6", "#10B981"]

    if "noise_level" in rob.columns and "downsampling_factor" in rob.columns and "quality_score" in rob.columns:
        noise_levels = sorted(rob["noise_level"].dropna().unique())
        for i, nl in enumerate(noise_levels):
            grp = rob[rob["noise_level"] == nl].sort_values("downsampling_factor")
            if grp.empty:
                continue
            grp_agg = grp.groupby("downsampling_factor")["quality_score"].mean().reset_index()
            label = f"Bruit {nl:.0%}" if 0 < nl < 1 else f"Bruit = {nl:.2f}"
            fig.add_trace(go.Scatter(
                x=grp_agg["downsampling_factor"],
                y=grp_agg["quality_score"],
                mode="lines+markers",
                name=label,
                line=dict(color=palette[i % len(palette)], width=2.2),
                marker=dict(size=8, line=dict(width=1.5, color="white")),
                hovertemplate=f"<b>{label}</b><br>Sous-éch. × %{{x}}<br>Score qualité = %{{y:.1f}}<extra></extra>",
            ))
        from config import _legend_v
        fig.update_layout(
            **PLOT_LAYOUT,
            xaxis_title="Facteur de sous-échantillonnage",
            yaxis_title="Score de qualité",
            legend=_legend_v(),
            showlegend=len(noise_levels) > 1,
        )
        apply_grid(fig)
    else:
        fig = _empty_fig("Colonnes 'downsampling_factor', 'noise_level' ou 'quality_score' manquantes")

    return fig


if __name__ == "__main__":
    PORT  = int(os.environ.get("PORT", 8050))
    DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=PORT, debug=DEBUG)
