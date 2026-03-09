"""
FiberScope — Dashboard Microtomographie Fibres
Projet E4 MSME — Page unique, visualisations essentielles
"""

import os
import dash
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

# ─── Données ──────────────────────────────────────────────────────────────────
BASE = os.path.dirname(__file__)

samples = pd.read_csv(os.path.join(BASE, "data/samples.csv"))
fibers  = pd.read_csv(os.path.join(BASE, "data/fibers.csv"))
contacts = pd.read_csv(os.path.join(BASE, "data/contacts.csv"))
acoustic = pd.read_csv(os.path.join(BASE, "data/acoustic_thermal.csv"))

# Enrichissement : matériau + lot sur chaque fibre / contact
fibers_m   = fibers.merge(samples[["sample_id","material","batch"]], on="sample_id", how="left")
contacts_m = contacts.merge(samples[["sample_id","material","batch"]], on="sample_id", how="left")
acoustic_m = acoustic.merge(samples[["sample_id","material","batch"]], on="sample_id", how="left")

MATERIALS = sorted(samples["material"].unique().tolist())
BATCHES   = sorted(samples["batch"].unique().tolist())

MAT_COLORS = {
    "Nylon":       "#2563EB",
    "Carbone":     "#DC2626",
    "Verre":       "#16A34A",
    "Cuivre":      "#D97706",
    "PET recyclé": "#7C3AED",
    "Chanvre":     "#059669",
}

PLOT_CONFIG = {"displayModeBar": False, "responsive": True}

PLOT_LAYOUT = dict(
    paper_bgcolor="white",
    plot_bgcolor="#F8FAFC",
    font=dict(family="Inter, sans-serif", size=12, color="#1E293B"),
    margin=dict(l=50, r=20, t=40, b=50),
)

def mat_color_list(mat_series):
    return [MAT_COLORS.get(m, "#94A3B8") for m in mat_series]

# ─── App ──────────────────────────────────────────────────────────────────────
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY, dbc.icons.BOOTSTRAP],
    title="FiberScope — MSME",
    suppress_callback_exceptions=True,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
server = app.server

# ─── Layout ───────────────────────────────────────────────────────────────────
app.layout = dbc.Container(fluid=True, style={"backgroundColor": "#F1F5F9", "minHeight": "100vh"}, children=[

    # ── HEADER ──────────────────────────────────────────────────────────────
    dbc.Row(className="mb-0", children=[
        dbc.Col([
            html.Div(style={
                "background": "linear-gradient(135deg, #1E3A5F 0%, #2563EB 100%)",
                "padding": "24px 32px",
                "borderRadius": "0 0 12px 12px",
            }, children=[
                html.H1("FiberScope", style={"color": "white", "margin": 0, "fontWeight": 700, "fontSize": "28px"}),
                html.P(
                    "Caractérisation morphologique des réseaux fibreux par microtomographie X",
                    style={"color": "#93C5FD", "margin": 0, "fontSize": "14px"}
                ),
            ])
        ])
    ]),

    # ── FILTRES ─────────────────────────────────────────────────────────────
    dbc.Row(className="my-3 px-3", children=[
        dbc.Col(width=12, children=[
            dbc.Card(body=True, style={"borderRadius": "10px", "border": "1px solid #E2E8F0"}, children=[
                dbc.Row([
                    dbc.Col([
                        html.Label("Matériau", style={"fontWeight": 600, "fontSize": "12px", "color": "#64748B", "marginBottom": "4px"}),
                        dcc.Dropdown(
                            id="filter-material",
                            options=[{"label": m, "value": m} for m in MATERIALS],
                            multi=True,
                            placeholder="Tous les matériaux",
                            style={"fontSize": "13px"},
                        )
                    ], md=4),
                    dbc.Col([
                        html.Label("Lot", style={"fontWeight": 600, "fontSize": "12px", "color": "#64748B", "marginBottom": "4px"}),
                        dcc.Dropdown(
                            id="filter-batch",
                            options=[{"label": b, "value": b} for b in BATCHES],
                            multi=True,
                            placeholder="Tous les lots",
                            style={"fontSize": "13px"},
                        )
                    ], md=3),
                    dbc.Col([
                        html.Label(" ", style={"display": "block", "fontSize": "12px", "marginBottom": "4px"}),
                        dbc.Button(
                            [html.I(className="bi bi-arrow-counterclockwise me-1"), "Réinitialiser"],
                            id="btn-reset",
                            color="secondary",
                            outline=True,
                            size="sm",
                        )
                    ], md=2, className="d-flex align-items-end"),
                ])
            ])
        ])
    ]),

    # ── KPIs ────────────────────────────────────────────────────────────────
    dbc.Row(id="row-kpis", className="px-3 mb-3"),

    # ── SECTION 1 : Morphologie des fibres ──────────────────────────────────
    dbc.Row(className="px-3 mb-2", children=[
        dbc.Col([html.H5("Morphologie des fibres", style={"color": "#1E3A5F", "fontWeight": 700, "borderLeft": "4px solid #2563EB", "paddingLeft": "12px"})])
    ]),
    dbc.Row(className="px-3 mb-3", children=[
        dbc.Col(dbc.Card(body=True, style={"borderRadius": "10px"}, children=[
            html.H6("Distribution des diamètres par matériau", style={"color": "#475569", "fontWeight": 600}),
            dcc.Graph(id="graph-diameter", config=PLOT_CONFIG, style={"height": "300px"}),
        ]), md=6),
        dbc.Col(dbc.Card(body=True, style={"borderRadius": "10px"}, children=[
            html.H6("Distribution des longueurs par matériau", style={"color": "#475569", "fontWeight": 600}),
            dcc.Graph(id="graph-length", config=PLOT_CONFIG, style={"height": "300px"}),
        ]), md=6),
    ]),
    dbc.Row(className="px-3 mb-3", children=[
        dbc.Col(dbc.Card(body=True, style={"borderRadius": "10px"}, children=[
            html.H6("Distribution des orientations angulaires θ", style={"color": "#475569", "fontWeight": 600}),
            html.P("Angle polaire θ ∈ [0°, 90°] — 0° = dans le plan, 90° = hors plan", style={"fontSize": "11px", "color": "#94A3B8", "margin": 0}),
            dcc.Graph(id="graph-orientation", config=PLOT_CONFIG, style={"height": "300px"}),
        ]), md=6),
        dbc.Col(dbc.Card(body=True, style={"borderRadius": "10px"}, children=[
            html.H6("Courbure des fibres par matériau", style={"color": "#475569", "fontWeight": 600}),
            html.P("Courbure κ = 1/R (mm⁻¹) — mesure de la rectitude des fibres", style={"fontSize": "11px", "color": "#94A3B8", "margin": 0}),
            dcc.Graph(id="graph-curvature", config=PLOT_CONFIG, style={"height": "300px"}),
        ]), md=6),
    ]),

    # ── SECTION 2 : Liaisons inter-fibres ───────────────────────────────────
    dbc.Row(className="px-3 mb-2", children=[
        dbc.Col([html.H5("Liaisons inter-fibres", style={"color": "#1E3A5F", "fontWeight": 700, "borderLeft": "4px solid #16A34A", "paddingLeft": "12px"})])
    ]),
    dbc.Row(className="px-3 mb-3", children=[
        dbc.Col(dbc.Card(body=True, style={"borderRadius": "10px"}, children=[
            html.H6("Distribution des aires de contact", style={"color": "#475569", "fontWeight": 600}),
            html.P("Surface de contact fibre-fibre (µm²)", style={"fontSize": "11px", "color": "#94A3B8", "margin": 0}),
            dcc.Graph(id="graph-contact-area", config=PLOT_CONFIG, style={"height": "300px"}),
        ]), md=6),
        dbc.Col(dbc.Card(body=True, style={"borderRadius": "10px"}, children=[
            html.H6("Densité de connexions vs Porosité", style={"color": "#475569", "fontWeight": 600}),
            html.P("Nombre de liaisons par unité de volume en fonction de la porosité", style={"fontSize": "11px", "color": "#94A3B8", "margin": 0}),
            dcc.Graph(id="graph-density-porosity", config=PLOT_CONFIG, style={"height": "300px"}),
        ]), md=6),
    ]),

    # ── SECTION 3 : Propriétés acoustiques ──────────────────────────────────
    dbc.Row(className="px-3 mb-2", children=[
        dbc.Col([html.H5("Propriétés acoustiques", style={"color": "#1E3A5F", "fontWeight": 700, "borderLeft": "4px solid #D97706", "paddingLeft": "12px"})])
    ]),
    dbc.Row(className="px-3 mb-3", children=[
        dbc.Col(dbc.Card(body=True, style={"borderRadius": "10px"}, children=[
            html.H6("Coefficient d'absorption acoustique par fréquence", style={"color": "#475569", "fontWeight": 600}),
            html.P("17 échantillons avec mesures acoustiques validées", style={"fontSize": "11px", "color": "#94A3B8", "margin": 0}),
            dcc.Graph(id="graph-absorption", config=PLOT_CONFIG, style={"height": "320px"}),
        ]), md=7),
        dbc.Col(dbc.Card(body=True, style={"borderRadius": "10px"}, children=[
            html.H6("Résistivité au flux vs Porosité", style={"color": "#475569", "fontWeight": 600}),
            html.P("Lien micro-structure → propriété acoustique clé", style={"fontSize": "11px", "color": "#94A3B8", "margin": 0}),
            dcc.Graph(id="graph-resistivity", config=PLOT_CONFIG, style={"height": "320px"}),
        ]), md=5),
    ]),

    # ── FOOTER ──────────────────────────────────────────────────────────────
    dbc.Row(className="px-3 pb-4", children=[
        dbc.Col([
            html.Hr(style={"borderColor": "#E2E8F0"}),
            html.P(
                "FiberScope · Projet E4 MSME · Analyse par microtomographie X",
                style={"textAlign": "center", "color": "#94A3B8", "fontSize": "12px"}
            )
        ])
    ]),
])


# ─── Helpers ──────────────────────────────────────────────────────────────────
def _filter(mat_sel, bat_sel):
    """Retourne les IDs d'échantillons correspondant aux filtres."""
    mask = pd.Series([True] * len(samples))
    if mat_sel:
        mask &= samples["material"].isin(mat_sel)
    if bat_sel:
        mask &= samples["batch"].isin(bat_sel)
    return samples[mask]["sample_id"].tolist(), samples[mask]


def _boxplot(df, y_col, color_col="material", title_y=""):
    """Boxplot groupé par matériau."""
    fig = go.Figure()
    mats = df[color_col].dropna().unique()
    for mat in sorted(mats):
        vals = df[df[color_col] == mat][y_col].dropna()
        if len(vals) == 0:
            continue
        fig.add_trace(go.Box(
            y=vals,
            name=mat,
            marker_color=MAT_COLORS.get(mat, "#94A3B8"),
            boxpoints="outliers",
            line_width=1.5,
        ))
    fig.update_layout(**PLOT_LAYOUT, yaxis_title=title_y, showlegend=False)
    return fig


# ─── Callback principal ───────────────────────────────────────────────────────
@app.callback(
    Output("row-kpis",          "children"),
    Output("graph-diameter",    "figure"),
    Output("graph-length",      "figure"),
    Output("graph-orientation", "figure"),
    Output("graph-curvature",   "figure"),
    Output("graph-contact-area","figure"),
    Output("graph-density-porosity", "figure"),
    Output("graph-absorption",  "figure"),
    Output("graph-resistivity", "figure"),
    Input("filter-material", "value"),
    Input("filter-batch",    "value"),
)
def update_all(mat_sel, bat_sel):
    ids, samp_f = _filter(mat_sel, bat_sel)

    fib_f  = fibers_m[fibers_m["sample_id"].isin(ids)]
    con_f  = contacts_m[contacts_m["sample_id"].isin(ids)]
    aco_f  = acoustic_m[acoustic_m["sample_id"].isin(ids)]

    # ── KPIs ────────────────────────────────────────────────────────────────
    n_samples   = len(samp_f)
    n_fibers    = len(fib_f)
    n_contacts  = len(con_f)
    mean_por    = samp_f["porosity"].mean()
    mean_qual   = samp_f["quality_score"].mean()

    def kpi(label, value, icon, color):
        return dbc.Col(dbc.Card(body=True, style={
            "borderRadius": "10px", "borderTop": f"4px solid {color}",
        }, children=[
            html.Div([
                html.Span(icon, style={"fontSize": "22px", "marginRight": "10px", "color": color}),
                html.Div([
                    html.P(label, style={"margin": 0, "fontSize": "11px", "color": "#64748B", "fontWeight": 600}),
                    html.P(value, style={"margin": 0, "fontSize": "22px", "fontWeight": 700, "color": "#1E293B"}),
                ])
            ], style={"display": "flex", "alignItems": "center"})
        ]), md=True)

    kpis = [
        kpi("Échantillons",       str(n_samples),              "🧪", "#2563EB"),
        kpi("Fibres analysées",   f"{n_fibers:,}",             "🔬", "#7C3AED"),
        kpi("Contacts détectés",  f"{n_contacts:,}",           "🔗", "#16A34A"),
        kpi("Porosité moyenne",   f"{mean_por:.2f}" if n_samples else "—", "💨", "#D97706"),
        kpi("Score qualité moy.", f"{mean_qual:.1f}/5" if n_samples else "—", "⭐", "#DC2626"),
    ]

    # ── Diamètre ────────────────────────────────────────────────────────────
    fig_diam = _boxplot(fib_f, "diameter_um", title_y="Diamètre (µm)")
    fig_diam.update_layout(title_text="")

    # ── Longueur ────────────────────────────────────────────────────────────
    fig_len = _boxplot(fib_f, "length_um", title_y="Longueur (µm)")

    # ── Orientations θ ─────────────────────────────────────────────────────
    fig_ori = go.Figure()
    for mat in sorted(fib_f["material"].dropna().unique()):
        vals = fib_f[fib_f["material"] == mat]["orientation_theta"].dropna()
        if len(vals) == 0:
            continue
        fig_ori.add_trace(go.Histogram(
            x=vals,
            name=mat,
            marker_color=MAT_COLORS.get(mat, "#94A3B8"),
            opacity=0.75,
            nbinsx=18,
            histnorm="percent",
        ))
    fig_ori.update_layout(
        **PLOT_LAYOUT,
        barmode="overlay",
        xaxis_title="θ (degrés)",
        yaxis_title="% fibres",
        legend=dict(orientation="h", y=1.02, x=0),
    )

    # ── Courbure ────────────────────────────────────────────────────────────
    # Courbure * 1000 pour avoir des valeurs lisibles (mm⁻¹ × 10³)
    fib_f2 = fib_f.copy()
    fib_f2["curvature_scaled"] = fib_f2["curvature"] * 1000
    fig_curv = _boxplot(fib_f2, "curvature_scaled", title_y="κ × 10³ (mm⁻¹)")

    # ── Aires de contact ────────────────────────────────────────────────────
    fig_ca = go.Figure()
    for mat in sorted(con_f["material"].dropna().unique()):
        vals = con_f[con_f["material"] == mat]["contact_area_um2"].dropna()
        if len(vals) == 0:
            continue
        # Clip outliers extrêmes (>99e percentile)
        p99 = vals.quantile(0.99)
        vals = vals[vals <= p99]
        fig_ca.add_trace(go.Histogram(
            x=vals,
            name=mat,
            marker_color=MAT_COLORS.get(mat, "#94A3B8"),
            opacity=0.75,
            nbinsx=30,
            histnorm="percent",
        ))
    fig_ca.update_layout(
        **PLOT_LAYOUT,
        barmode="overlay",
        xaxis_title="Aire de contact (µm²)",
        yaxis_title="% contacts",
        legend=dict(orientation="h", y=1.02, x=0),
    )

    # ── Densité connexions vs Porosité ──────────────────────────────────────
    fig_dp = go.Figure()
    for mat in sorted(samp_f["material"].dropna().unique()):
        sub = samp_f[samp_f["material"] == mat]
        fig_dp.add_trace(go.Scatter(
            x=sub["porosity"],
            y=sub["contact_density"],
            mode="markers",
            name=mat,
            marker=dict(
                color=MAT_COLORS.get(mat, "#94A3B8"),
                size=10,
                line=dict(width=1, color="white"),
            ),
            text=sub["sample_id"],
            hovertemplate="<b>%{text}</b><br>Porosité: %{x:.3f}<br>Densité: %{y:.1f}<extra></extra>",
        ))
    fig_dp.update_layout(
        **PLOT_LAYOUT,
        xaxis_title="Porosité",
        yaxis_title="Densité de connexions (N/mm³)",
    )

    # ── Absorption acoustique ────────────────────────────────────────────────
    freqs = [250, 500, 1000, 2000, 4000]
    freq_cols = ["absorption_250hz", "absorption_500hz", "absorption_1000hz",
                 "absorption_2000hz", "absorption_4000hz"]
    fig_abs = go.Figure()
    if len(aco_f) > 0:
        for _, row in aco_f.iterrows():
            vals = [row[c] for c in freq_cols if c in row]
            if any(pd.isna(v) for v in vals):
                continue
            mat = row.get("material", "—")
            fig_abs.add_trace(go.Scatter(
                x=freqs,
                y=vals,
                mode="lines+markers",
                name=f"{row['sample_id']} ({mat})",
                line=dict(color=MAT_COLORS.get(mat, "#94A3B8"), width=1.5),
                marker=dict(size=5),
                opacity=0.8,
                hovertemplate=f"<b>{row['sample_id']}</b><br>%{{x}} Hz: %{{y:.3f}}<extra></extra>",
            ))
        # Courbe médiane
        medians = []
        for c in freq_cols:
            col_data = aco_f[c].dropna()
            if len(col_data):
                medians.append(col_data.median())
        if len(medians) == 5:
            fig_abs.add_trace(go.Scatter(
                x=freqs,
                y=medians,
                mode="lines",
                name="Médiane",
                line=dict(color="#1E293B", width=3, dash="dot"),
            ))
    fig_abs.update_layout(
        **PLOT_LAYOUT,
        xaxis=dict(title="Fréquence (Hz)", tickvals=freqs, ticktext=[f"{f} Hz" for f in freqs]),
        yaxis=dict(title="α (coefficient d'absorption)", range=[0, 1.05]),
        legend=dict(orientation="v", x=1.02, y=1),
    )

    # ── Résistivité vs Porosité ─────────────────────────────────────────────
    fig_res = go.Figure()
    if len(aco_f) > 0:
        for mat in sorted(aco_f["material"].dropna().unique()):
            sub = aco_f[aco_f["material"] == mat]
            fig_res.add_trace(go.Scatter(
                x=sub["porosity"],
                y=sub["airflow_resistivity"],
                mode="markers",
                name=mat,
                marker=dict(
                    color=MAT_COLORS.get(mat, "#94A3B8"),
                    size=11,
                    line=dict(width=1, color="white"),
                ),
                text=sub["sample_id"],
                hovertemplate="<b>%{text}</b><br>Porosité: %{x:.3f}<br>Résistivité: %{y:,.0f} Pa·s/m²<extra></extra>",
            ))
        # Tendance log-linéaire
        x_all = aco_f["porosity"].dropna()
        y_all = aco_f["airflow_resistivity"].dropna()
        common_idx = x_all.index.intersection(y_all.index)
        if len(common_idx) >= 3:
            x_v = x_all[common_idx].values
            y_v = np.log(y_all[common_idx].values + 1)
            z = np.polyfit(x_v, y_v, 1)
            x_lin = np.linspace(x_v.min(), x_v.max(), 80)
            y_lin = np.exp(np.polyval(z, x_lin))
            fig_res.add_trace(go.Scatter(
                x=x_lin, y=y_lin,
                mode="lines",
                name="Tendance",
                line=dict(color="#1E293B", width=2, dash="dash"),
                showlegend=True,
            ))
    fig_res.update_layout(
        **PLOT_LAYOUT,
        xaxis_title="Porosité",
        yaxis_title="Résistivité au flux (Pa·s/m²)",
        yaxis_type="log",
    )

    return kpis, fig_diam, fig_len, fig_ori, fig_curv, fig_ca, fig_dp, fig_abs, fig_res


# ── Reset filtres ──────────────────────────────────────────────────────────────
@app.callback(
    Output("filter-material", "value"),
    Output("filter-batch",    "value"),
    Input("btn-reset", "n_clicks"),
    prevent_initial_call=True,
)
def reset_filters(_):
    return None, None


if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 8050))
    DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=PORT, debug=DEBUG)
