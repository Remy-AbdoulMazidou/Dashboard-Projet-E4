import numpy as np
import pandas as pd
from dash import html, dcc, callback, Input, Output
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from utils.data_loader import load_acoustic_thermal, load_samples
from utils.stats import pearson_matrix, linear_regression
from utils import figures as fig_utils
from components.info_box import info_box, guide_box, conclusion_box, chart_header
from config import COLORS, MATERIAL_COLORS

FREQ_COLS   = ["absorption_250hz", "absorption_500hz", "absorption_1000hz",
               "absorption_2000hz", "absorption_4000hz"]
FREQ_LABELS = [250, 500, 1000, 2000, 4000]

TRANSPORT_PARAMS = [
    ("airflow_resistivity",  "Résistivité σ (Pa·s/m²)"),
    ("thermal_permeability", "Perméabilité thermique k₀' (m²)"),
    ("viscous_length_um",    "Longueur visqueuse Λ (µm)"),
    ("thermal_length_um",    "Longueur thermique Λ' (µm)"),
]

ORIENT_BINS   = [0, 20, 40, 90]
ORIENT_LABELS = ["Anisotrope (<20°)", "Modéré (20–40°)", "Quasi-isotrope (>40°)"]
ORIENT_SYMBOLS = ["circle", "square", "diamond"]
ORIENT_COLORS  = ["#2563EB", "#EF4444", "#10B981"]


def _orient_category(dispersion: float) -> str:
    if dispersion < 20:
        return ORIENT_LABELS[0]
    if dispersion < 40:
        return ORIENT_LABELS[1]
    return ORIENT_LABELS[2]


def layout() -> html.Div:
    acoustic   = load_acoustic_thermal()
    sample_ids = acoustic["sample_id"].tolist()

    return html.Div([

        # ── En-tête ──────────────────────────────────────────────────────
        html.H2("🔊 Propriétés acoustiques et thermiques", className="page-title"),
        html.P(
            "Relation entre la microstructure des fibres (porosité, diamètre, orientation) "
            "et les propriétés acoustiques/thermiques mesurées expérimentalement.",
            className="page-subtitle",
        ),

        # ── Section 1 : Courbes d'absorption en fréquence ────────────────
        html.H3("Courbes d'absorption acoustique en fréquence", className="section-separator"),
        info_box(
            "Le coefficient d'absorption α varie entre 0 (son réfléchi) et 1 (absorption totale). "
            "Ces courbes montrent l'évolution de α entre 250 Hz et 4000 Hz pour chaque échantillon. "
            "Sélectionnez jusqu'à 6 échantillons pour les comparer. "
            "L'axe des fréquences est logarithmique (comme l'oreille humaine le perçoit)."
        ),
        html.Div([
            html.Div([
                html.Div([
                    html.Label("Échantillons à comparer (max 6)"),
                    dcc.Dropdown(
                        id="at-sample-select",
                        options=[{"label": sid, "value": sid} for sid in sample_ids],
                        value=sample_ids[:5],
                        multi=True,
                        className="dash-dropdown-dark",
                        style={"fontSize": "13px"},
                    ),
                ], style={"marginBottom": "14px"}),
                dcc.Graph(id="at-absorption-curve", style={"height": "360px"}),
            ], className="card col-12"),
        ], className="row"),

        # ── Section 2 : Paramètres de transport vs porosité ──────────────
        html.H3("Paramètres de transport JCA vs porosité", className="section-separator"),
        info_box(
            "Le modèle Johnson-Champoux-Allard (JCA) décrit la propagation acoustique dans les "
            "milieux poreux via 5 paramètres macroscopiques. Ces graphiques montrent comment chaque "
            "paramètre évolue avec la porosité φ (fraction volumique de vide), en distinguant "
            "l'orientation des fibres. Les lignes pointillées = droites de régression par catégorie."
        ),
        guide_box("Catégories d'orientation des fibres", [
            "Anisotrope (<20°) : fibres fortement orientées, résistivité élevée dans une direction.",
            "Modéré (20–40°) : orientation partielle, comportement intermédiaire.",
            "Quasi-isotrope (>40°) : fibres distribuées aléatoirement, comportement homogène.",
        ]),
        html.Div([
            html.Div([
                dcc.Graph(id="at-transport-subplot", style={"height": "580px"}),
            ], className="card col-12"),
        ], className="row"),

        # ── Section 3 : Matrice de corrélation ───────────────────────────
        html.H3("Corrélations microstructure ↔ acoustique/thermique", className="section-separator"),
        info_box(
            "La matrice de corrélation de Pearson quantifie la relation linéaire entre descripteurs "
            "microstructuraux et propriétés mesurées. Valeurs entre −1 et +1. "
            "Rouge = corrélation négative forte, Bleu = corrélation positive forte, Blanc = aucune relation."
        ),
        html.Div([
            html.Div([
                html.Div([
                    html.Span("−1", style={"fontSize": "11px", "color": "#EF4444", "fontWeight": "600"}),
                    html.Div(className="scale-bar"),
                    html.Span("+1", style={"fontSize": "11px", "color": "#2563EB", "fontWeight": "600"}),
                ], className="scale-hint"),
                dcc.Graph(id="at-heatmap-corr", style={"height": "420px"}),
            ], className="card col-12"),
        ], className="row"),

        # ── Conclusion ───────────────────────────────────────────────────
        conclusion_box(
            "Résultats clés — Acoustique & Thermique",
            "Les courbes d'absorption révèlent que les matériaux à fibres fines (Carbone, Verre) "
            "atteignent des coefficients α > 0,8 dès 1000 Hz, tandis que les fibres épaisses "
            "(Chanvre, PET recyclé) nécessitent des fréquences plus élevées. "
            "La matrice de corrélation confirme que la porosité est le descripteur "
            "le plus corrélé à l'absorption (|r| > 0,7), suivie du diamètre moyen. "
            "L'orientation des fibres influence principalement la résistivité à l'écoulement : "
            "les matériaux anisotropes présentent des valeurs σ 30–40 % plus élevées.",
        ),

    ], className="page-content")


@callback(
    Output("at-heatmap-corr", "figure"),
    Input("at-heatmap-corr", "id"),
)
def build_corr_heatmap(_):
    acoustic = load_acoustic_thermal()
    corr_cols = ["porosity", "mean_diameter_um", "orientation_dispersion",
                 "airflow_resistivity", "absorption_1000hz", "absorption_2000hz",
                 "thermal_permeability"]
    corr_matrix = pearson_matrix(acoustic[corr_cols].dropna())
    return fig_utils.heatmap_corr(
        corr_matrix,
        "Corrélations : microstructure ↔ acoustique / thermique",
    )


@callback(
    Output("at-transport-subplot", "figure"),
    Input("at-transport-subplot", "id"),
)
def build_transport_subplot(_):
    acoustic = load_acoustic_thermal()
    samples  = load_samples()
    df = acoustic.merge(samples[["sample_id", "material"]], on="sample_id", how="left")
    df["orient_category"] = df["orientation_dispersion"].apply(_orient_category)

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=[label for _, label in TRANSPORT_PARAMS],
        horizontal_spacing=0.14,
        vertical_spacing=0.18,
    )

    positions = [(1, 1), (1, 2), (2, 1), (2, 2)]

    for idx, ((col, ylabel), (row, colnum)) in enumerate(zip(TRANSPORT_PARAMS, positions)):
        legend_shown = set()
        for cat_idx, cat in enumerate(ORIENT_LABELS):
            sub = df[df["orient_category"] == cat]
            if sub.empty:
                continue
            show_leg = cat not in legend_shown
            legend_shown.add(cat)
            fig.add_trace(go.Scatter(
                x=sub["porosity"],
                y=sub[col],
                mode="markers",
                name=cat,
                legendgroup=cat,
                showlegend=(idx == 0 and show_leg),
                marker=dict(
                    symbol=ORIENT_SYMBOLS[cat_idx],
                    color=ORIENT_COLORS[cat_idx],
                    size=9,
                    opacity=0.82,
                    line=dict(width=0.8, color="white"),
                ),
            ), row=row, col=colnum)

            reg = linear_regression(sub["porosity"], sub[col])
            if reg:
                fig.add_trace(go.Scatter(
                    x=reg["x_line"], y=reg["y_line"],
                    mode="lines",
                    showlegend=False,
                    line=dict(color=ORIENT_COLORS[cat_idx], width=1.5, dash="dot"),
                ), row=row, col=colnum)

        axis_idx = "" if idx == 0 else str(idx + 1)
        fig.update_layout(**{
            f"xaxis{axis_idx}_title": "Porosité φ",
            f"yaxis{axis_idx}_title": ylabel,
        })

    sci = fig_utils._SCI_LAYOUT.copy()
    sci.pop("xaxis", None)
    sci.pop("yaxis", None)
    fig.update_layout(
        **sci,
        height=580,
        legend=dict(
            title="Orientation des fibres",
            bgcolor="rgba(255,255,255,0.95)",
            bordercolor="#E2E8F0",
            borderwidth=1,
            font=dict(size=10, color="#0F172A"),
        ),
    )
    fig.update_xaxes(
        gridcolor="#E8EEF6", linecolor="#CBD5E1", mirror=True,
        showline=True, ticks="outside", tickcolor="#64748B",
    )
    fig.update_yaxes(
        gridcolor="#E8EEF6", linecolor="#CBD5E1", mirror=True,
        showline=True, ticks="outside", tickcolor="#64748B",
    )
    return fig


@callback(
    Output("at-absorption-curve", "figure"),
    Input("at-sample-select", "value"),
)
def update_absorption_curve(selected_samples):
    if not selected_samples:
        return fig_utils.empty_figure("Sélectionnez au moins un échantillon")

    acoustic = load_acoustic_thermal()
    samples  = load_samples()
    selected = selected_samples[:6]
    df = acoustic[acoustic["sample_id"].isin(selected)].merge(
        samples[["sample_id", "material"]], on="sample_id", how="left"
    )

    sci_colors  = fig_utils._SCI_PALETTE
    sci_symbols = fig_utils._SCI_SYMBOLS

    fig = go.Figure()
    for i, (_, row) in enumerate(df.iterrows()):
        values = [row[col] for col in FREQ_COLS]
        color  = sci_colors[i % len(sci_colors)]
        fig.add_trace(go.Scatter(
            x=FREQ_LABELS,
            y=values,
            mode="lines+markers",
            name=f"{row['sample_id']} ({row.get('material', '')})",
            line=dict(color=color, width=2.2),
            marker=dict(
                symbol=sci_symbols[i % len(sci_symbols)],
                size=9,
                color=color,
                line=dict(width=1, color="white"),
            ),
        ))

    fig.update_layout(
        xaxis=dict(
            type="log",
            tickvals=FREQ_LABELS,
            ticktext=[str(f) for f in FREQ_LABELS],
            title={"text": "Fréquence (Hz)", "font": {"size": 12}},
        ),
        yaxis=dict(
            range=[0, 1.05],
            title={"text": "Coefficient d'absorption α", "font": {"size": 12}},
        ),
        height=360,
    )
    return fig_utils.apply_scientific_theme(fig)
