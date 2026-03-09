import numpy as np
import pandas as pd
from dash import html, dcc, callback, Input, Output
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from utils.data_loader import load_acoustic_thermal, load_samples
from utils.stats import pearson_matrix, linear_regression
from utils import figures as fig_utils
from components.info_box import info_box, guide_box, warn_box, chart_header
from config import COLORS, MATERIAL_COLORS

FREQ_COLS = ["absorption_250hz", "absorption_500hz", "absorption_1000hz",
             "absorption_2000hz", "absorption_4000hz"]
FREQ_LABELS = [250, 500, 1000, 2000, 4000]

TRANSPORT_PARAMS = [
    ("airflow_resistivity",   "Résistivité à l'écoulement (Pa·s/m²)"),
    ("thermal_permeability",  "Perméabilité thermique (m²)"),
    ("viscous_length_um",     "Longueur visqueuse Λ (µm)"),
    ("thermal_length_um",     "Longueur thermique Λ' (µm)"),
]

ORIENT_BINS = [0, 20, 40, 90]
ORIENT_LABELS = ["Anisotrope (<20°)", "Modéré (20–40°)", "Quasi-isotrope (>40°)"]
ORIENT_SYMBOLS = ["circle", "square", "diamond"]
ORIENT_COLORS = ["#2E86AB", "#E63946", "#2A9D8F"]


def _orient_category(dispersion: float) -> str:
    if dispersion < 20:
        return ORIENT_LABELS[0]
    if dispersion < 40:
        return ORIENT_LABELS[1]
    return ORIENT_LABELS[2]


def layout() -> html.Div:
    acoustic = load_acoustic_thermal()
    sample_ids = acoustic["sample_id"].tolist()

    return html.Div([
        html.H2("Propriétés acoustiques et thermiques", className="page-title"),
        html.P(
            "Relation entre la microstructure des fibres et les propriétés "
            "acoustiques/thermiques mesurées expérimentalement.",
            className="page-subtitle",
        ),

        # ── Section 1 : Scatter dark theme ───────────────────────────────────
        info_box(
            "Le coefficient d'absorption acoustique α varie entre 0 (aucune absorption, "
            "le son est réfléchi) et 1 (absorption totale). Une valeur de 0,8 à 1000 Hz "
            "signifie que 80 % de l'énergie sonore est absorbée à cette fréquence."
        ),
        html.Div([
            html.Div([
                chart_header(
                    "Absorption à 1000 Hz vs porosité",
                    "La porosité φ est la fraction de volume vide (0 = solide, 1 = vide). "
                    "Une porosité élevée favorise généralement l'absorption acoustique.",
                ),
                dcc.Graph(id="at-scatter-porosity-abs"),
            ], className="card col-6"),
            html.Div([
                chart_header(
                    "Absorption à 1000 Hz vs diamètre moyen",
                    "Des fibres plus fines augmentent la surface de contact avec l'air, "
                    "améliorant l'absorption par friction visqueuse.",
                ),
                dcc.Graph(id="at-scatter-diameter-abs"),
            ], className="card col-6"),
        ], className="row"),

        html.Div([
            html.Div([
                chart_header(
                    "Perméabilité thermique vs porosité",
                    "La perméabilité thermique k₀' traduit la facilité avec laquelle la chaleur "
                    "se propage dans le matériau. Elle augmente avec la porosité.",
                ),
                dcc.Graph(id="at-scatter-perm-porosity"),
            ], className="card col-6"),
            html.Div([
                chart_header(
                    "Matrice de corrélation — microstructure ↔ acoustique/thermique",
                    "Valeurs de corrélation de Pearson entre les descripteurs microstructuraux "
                    "et les propriétés mesurées. Rouge = corrélation négative, Bleu = positive.",
                ),
                html.Div([
                    html.Div([
                        html.Span("−1", style={"fontSize": "10px", "color": "#F24236"}),
                        html.Div(className="scale-bar"),
                        html.Span("+1", style={"fontSize": "10px", "color": "#2E86AB"}),
                    ], className="scale-hint"),
                ]),
                dcc.Graph(id="at-heatmap-corr"),
            ], className="card col-6"),
        ], className="row"),


        # ── Section 2 : Paramètres de transport ──────────────────────────────
        html.H3("Paramètres de transport vs porosité — modèle JCA", className="section-separator"),
        info_box(
            "Le modèle Johnson-Champoux-Allard (JCA) décrit la propagation acoustique "
            "dans les milieux poreux via 5 paramètres de transport. Ces graphiques montrent "
            "comment chaque paramètre évolue avec la porosité, en distinguant les orientations des fibres. "
            "Les lignes en pointillés sont les droites de régression linéaire par catégorie d'orientation."
        ),
        html.Div([
            html.Div([dcc.Graph(id="at-transport-subplot")], className="card col-12"),
        ], className="row"),

        # ── Section 3 : Courbes d'absorption ─────────────────────────────────
        html.H3("Courbes d'absorption acoustique en fréquence", className="section-separator"),
        info_box(
            "Ces courbes montrent l'évolution du coefficient d'absorption α en fonction "
            "de la fréquence (250 Hz à 4000 Hz). Chaque ligne représente un échantillon. "
            "Sélectionnez jusqu'à 6 échantillons pour les comparer côte à côte."
        ),
        html.Div([
            html.Div([
                html.Div([
                    html.Label("Échantillons à comparer (max 6)",
                               style={"color": COLORS["text_secondary"], "fontSize": "11px",
                                      "fontWeight": "600"}),
                    dcc.Dropdown(
                        id="at-sample-select",
                        options=[{"label": sid, "value": sid} for sid in sample_ids],
                        value=sample_ids[:4],
                        multi=True,
                        className="dash-dropdown-dark",
                        style={"fontSize": "13px"},
                    ),
                ], style={"marginBottom": "12px"}),
                dcc.Graph(id="at-absorption-curve"),
            ], className="card col-8"),
            html.Div([
                chart_header(
                    "Résistivité à l'écoulement par matériau",
                    "σ (Pa·s/m²) : résistance du matériau au passage de l'air. "
                    "Valeur trop faible → peu d'absorption. Trop élevée → le son rebondit.",
                ),
                dcc.Graph(id="at-bar-resistivity"),
            ], className="card col-4"),
        ], className="row"),

    ], className="page-content")


@callback(
    Output("at-scatter-porosity-abs", "figure"),
    Output("at-scatter-diameter-abs", "figure"),
    Output("at-bar-resistivity", "figure"),
    Output("at-scatter-perm-porosity", "figure"),
    Output("at-heatmap-corr", "figure"),
    Input("at-sample-select", "id"),
)
def build_static_charts(_):
    acoustic = load_acoustic_thermal()
    samples = load_samples()
    df = acoustic.merge(samples[["sample_id", "material"]], on="sample_id", how="left")

    scatter_por = fig_utils.scatter(
        df, "porosity", "absorption_1000hz", color_col="material",
        title="Absorption à 1000 Hz vs porosité",
        xlabel="Porosité φ", ylabel="Absorption α (1000 Hz)",
    )
    scatter_diam = fig_utils.scatter(
        df, "mean_diameter_um", "absorption_1000hz", color_col="material",
        title="Absorption à 1000 Hz vs diamètre moyen",
        xlabel="Diamètre moyen (µm)", ylabel="Absorption α (1000 Hz)",
    )
    resistivity_by_mat = (
        df.groupby("material")["airflow_resistivity"].mean().reset_index()
        .rename(columns={"airflow_resistivity": "mean_resistivity"})
    )
    bar_res = fig_utils.bar_chart(
        resistivity_by_mat, "material", "mean_resistivity",
        "Résistivité à l'écoulement par matériau",
        color_col="material", xlabel="Matériau", ylabel="Résistivité σ (Pa·s/m²)",
    )
    scatter_perm = fig_utils.scatter(
        df, "porosity", "thermal_permeability", color_col="material",
        title="Perméabilité thermique vs porosité",
        xlabel="Porosité φ", ylabel="Perméabilité thermique k₀' (m²)",
    )
    corr_cols = ["porosity", "mean_diameter_um", "orientation_dispersion",
                 "airflow_resistivity", "absorption_1000hz", "absorption_2000hz",
                 "thermal_permeability"]
    corr_matrix = pearson_matrix(acoustic[corr_cols].dropna())
    heatmap_corr = fig_utils.heatmap_corr(
        corr_matrix,
        "Corrélations : microstructure ↔ acoustique/thermique",
    )
    return scatter_por, scatter_diam, bar_res, scatter_perm, heatmap_corr


@callback(
    Output("at-transport-subplot", "figure"),
    Input("at-sample-select", "id"),
)
def build_transport_subplot(_):
    acoustic = load_acoustic_thermal()
    samples = load_samples()
    df = acoustic.merge(samples[["sample_id", "material"]], on="sample_id", how="left")
    df["orient_category"] = df["orientation_dispersion"].apply(_orient_category)

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=[label for _, label in TRANSPORT_PARAMS],
        horizontal_spacing=0.12,
        vertical_spacing=0.16,
    )

    positions = [(1, 1), (1, 2), (2, 1), (2, 2)]

    for idx, ((col, ylabel), (row, colnum)) in enumerate(zip(TRANSPORT_PARAMS, positions)):
        legend_shown = set()
        for cat_idx, cat in enumerate(ORIENT_LABELS):
            sub = df[df["orient_category"] == cat]
            if sub.empty:
                continue
            show_legend = cat not in legend_shown
            legend_shown.add(cat)
            fig.add_trace(
                go.Scatter(
                    x=sub["porosity"],
                    y=sub[col],
                    mode="markers",
                    name=cat,
                    legendgroup=cat,
                    showlegend=(idx == 0 and show_legend),
                    marker=dict(
                        symbol=ORIENT_SYMBOLS[cat_idx],
                        color=ORIENT_COLORS[cat_idx],
                        size=8,
                        opacity=0.8,
                        line=dict(width=0.5, color="#333"),
                    ),
                ),
                row=row, col=colnum,
            )

            reg = linear_regression(sub["porosity"], sub[col])
            if reg:
                fig.add_trace(
                    go.Scatter(
                        x=reg["x_line"],
                        y=reg["y_line"],
                        mode="lines",
                        showlegend=False,
                        line=dict(color=ORIENT_COLORS[cat_idx], width=1.2, dash="dot"),
                    ),
                    row=row, col=colnum,
                )

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
        height=600,
        legend=dict(
            title="Orientation des fibres",
            bgcolor="rgba(255,255,255,0.95)",
            bordercolor="#ccc",
            borderwidth=1,
            font=dict(size=10, color="#1a1a2e"),
        ),
    )
    fig.update_xaxes(
        gridcolor="#e0e0e0", linecolor="#333", mirror=True,
        showline=True, ticks="outside", tickcolor="#333",
    )
    fig.update_yaxes(
        gridcolor="#e0e0e0", linecolor="#333", mirror=True,
        showline=True, ticks="outside", tickcolor="#333",
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
    samples = load_samples()
    selected = selected_samples[:6]
    df = acoustic[acoustic["sample_id"].isin(selected)].merge(
        samples[["sample_id", "material"]], on="sample_id", how="left"
    )

    sci_colors = fig_utils._SCI_PALETTE
    sci_symbols = ["circle", "square", "diamond", "cross", "triangle-up", "star"]

    fig = go.Figure()
    for i, (_, row) in enumerate(df.iterrows()):
        values = [row[col] for col in FREQ_COLS]
        color = sci_colors[i % len(sci_colors)]
        fig.add_trace(go.Scatter(
            x=FREQ_LABELS,
            y=values,
            mode="lines+markers",
            name=f"{row['sample_id']} ({row.get('material', '')})",
            line=dict(color=color, width=2),
            marker=dict(symbol=sci_symbols[i % len(sci_symbols)], size=8,
                        color=color, line=dict(width=0.5, color="#333")),
        ))

    fig.update_layout(
        xaxis=dict(
            type="log",
            tickvals=FREQ_LABELS,
            ticktext=[str(f) for f in FREQ_LABELS],
            title={"text": "Fréquence (Hz)", "font": {"size": 12}},
        ),
        yaxis=dict(range=[0, 1.05], title={"text": "Coefficient d'absorption α (0 → 1)", "font": {"size": 12}}),
        height=380,
    )
    return fig_utils.apply_scientific_theme(fig)
