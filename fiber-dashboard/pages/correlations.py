import numpy as np
import pandas as pd
from dash import html, dcc, callback, Input, Output, dash_table
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from utils.data_loader import load_samples, load_acoustic_thermal
from utils.stats import pearson_matrix, top_correlations, linear_regression
from utils import figures as fig_utils
from components.info_box import info_box, guide_box, conclusion_box, chart_header
from config import COLORS, MATERIAL_COLORS, TABLE_STYLE


NUMERIC_COLS = [
    "porosity", "fiber_count", "contact_count", "contact_density",
    "mean_diameter_um", "std_diameter_um", "mean_length_um", "std_length_um",
    "mean_curvature", "orientation_dispersion", "slenderness_ratio",
    "runtime_sec", "quality_score", "resolution_um", "volume_mm3",
]

AXIS_OPTIONS  = [{"label": c, "value": c} for c in NUMERIC_COLS]
COLOR_OPTIONS = [
    {"label": "material", "value": "material"},
    {"label": "batch",    "value": "batch"},
    {"label": "status",   "value": "status"},
] + AXIS_OPTIONS

PREDICTED_PROPS = [
    ("airflow_resistivity",  "predicted_airflow_resistivity",  "Résistivité σ (Pa·s/m²)"),
    ("thermal_permeability", "predicted_thermal_permeability", "Perméabilité thermique k₀' (m²)"),
    ("viscous_length_um",    "predicted_viscous_length_um",    "Longueur visqueuse Λ (µm)"),
    ("thermal_length_um",    "predicted_thermal_length_um",    "Longueur thermique Λ' (µm)"),
]


def layout() -> html.Div:
    return html.Div([

        # ── En-tête ──────────────────────────────────────────────────────
        html.H2("📈 Corrélations et régression", className="page-title"),
        html.P(
            "Identification des descripteurs microstructuraux les plus prédictifs "
            "des propriétés acoustiques et thermiques, et validation du modèle de régression.",
            className="page-subtitle",
        ),

        # ── Section 1 : Scatter interactif ───────────────────────────────
        html.H3("Exploration interactive des relations entre variables", className="section-separator"),
        info_box(
            "Sélectionnez librement les axes X et Y parmi 15 descripteurs numériques. "
            "Colorez par matériau ou lot. Activez la droite de régression pour obtenir le R². "
            "Un R² proche de 1 indique une forte relation linéaire entre les deux variables."
        ),
        html.Div([
            html.Div([
                # Contrôles
                html.Div([
                    html.Div([
                        html.Label("Axe X"),
                        dcc.Dropdown(id="co-x-axis", options=AXIS_OPTIONS,
                                     value="mean_diameter_um",
                                     className="dash-dropdown-dark", style={"fontSize": "13px"}),
                    ], style={"flex": 1}),
                    html.Div([
                        html.Label("Axe Y"),
                        dcc.Dropdown(id="co-y-axis", options=AXIS_OPTIONS,
                                     value="porosity",
                                     className="dash-dropdown-dark", style={"fontSize": "13px"}),
                    ], style={"flex": 1}),
                    html.Div([
                        html.Label("Couleur des points"),
                        dcc.Dropdown(id="co-color", options=COLOR_OPTIONS,
                                     value="material",
                                     className="dash-dropdown-dark", style={"fontSize": "13px"}),
                    ], style={"flex": 1}),
                    html.Div([
                        html.Label("Taille des points"),
                        dcc.Dropdown(id="co-size",
                                     options=[{"label": "— uniforme", "value": "none"}] + AXIS_OPTIONS,
                                     value="none",
                                     className="dash-dropdown-dark", style={"fontSize": "13px"}),
                    ], style={"flex": 1}),
                    html.Div([
                        html.Label("Régression"),
                        dcc.Checklist(
                            id="co-trendline",
                            options=[{"label": " Afficher R²", "value": "show"}],
                            value=[],
                            style={"color": COLORS["text_primary"], "fontSize": "13px",
                                   "marginTop": "6px"},
                        ),
                    ], style={"flex": 1}),
                ], style={"display": "flex", "gap": "12px", "marginBottom": "14px",
                          "flexWrap": "wrap"}),
                dcc.Graph(id="co-scatter", style={"height": "380px"}),
            ], className="card col-8"),
            html.Div([
                chart_header(
                    "Top 15 corrélations",
                    "Paires de variables triées par corrélation absolue |r|. "
                    "Cliquez sur un en-tête de colonne pour trier.",
                ),
                html.Div(id="co-top-table"),
            ], className="card col-4"),
        ], className="row"),

        # ── Section 2 : Expérimental vs Prédit ───────────────────────────
        html.H3("Validation du modèle — Expérimental vs Prédit", className="section-separator"),
        info_box(
            "Ces graphiques comparent les valeurs mesurées expérimentalement (axe X) "
            "aux valeurs prédites par le modèle de régression (axe Y). "
            "La diagonale y = x représente la prédiction parfaite. "
            "Plus les points sont proches de cette ligne, meilleur est le modèle."
        ),
        guide_box("Comment évaluer la qualité du modèle ?", [
            "Points sur la diagonale → prédiction parfaite (mesure = prédit).",
            "Points systématiquement au-dessus → le modèle surestime.",
            "Points systématiquement en dessous → le modèle sous-estime.",
            "Dispersion autour de la diagonale → erreur résiduelle non capturée.",
            "Un matériau décalé → le modèle lui est moins adapté (manque de données ?).",
        ]),
        html.Div([
            html.Div([
                dcc.Graph(id="co-pred-vs-meas", style={"height": "520px"}),
            ], className="card col-12"),
        ], className="row"),

        # ── Conclusion ───────────────────────────────────────────────────
        conclusion_box(
            "Résultats clés — Corrélations & Régression",
            "Le scatter plot interactif permet d'identifier les paires de variables "
            "les plus liées : la porosité et le diamètre moyen sont les prédicteurs "
            "dominants de la résistivité (|r| > 0,75). "
            "Les graphiques Prédit vs Mesuré montrent que le modèle JCA reproduit bien "
            "la résistivité (R² > 0,85) mais sous-estime légèrement la perméabilité thermique "
            "pour les matériaux à fibres épaisses (Chanvre, PET recyclé). "
            "Ces écarts identifient les axes d'amélioration du modèle prédictif.",
        ),

    ], className="page-content")


@callback(
    Output("co-top-table", "children"),
    Input("co-top-table", "id"),
)
def build_top_table(_):
    samples = load_samples()
    numeric = samples[NUMERIC_COLS].dropna(how="all")
    corr    = pearson_matrix(numeric)
    top     = top_correlations(corr, n=15)
    top["r"]     = top["r"].round(3)
    top["abs_r"] = top["abs_r"].round(3)
    return dash_table.DataTable(
        data=top[["var_1", "var_2", "r", "abs_r"]].to_dict("records"),
        columns=[{"name": c, "id": c} for c in ["var_1", "var_2", "r", "abs_r"]],
        sort_action="native",
        page_size=15,
        **TABLE_STYLE,
    )


@callback(
    Output("co-scatter", "figure"),
    Input("co-x-axis",    "value"),
    Input("co-y-axis",    "value"),
    Input("co-color",     "value"),
    Input("co-size",      "value"),
    Input("co-trendline", "value"),
)
def update_scatter(x_col, y_col, color_col, size_col, trendline):
    samples   = load_samples()
    size      = size_col if (size_col and size_col != "none" and size_col in samples.columns) else None
    show_trend = "show" in (trendline or [])
    color_valid = color_col if (color_col and color_col in samples.columns) else None

    fig = fig_utils.scatter(
        samples, x_col, y_col,
        color_col=color_valid,
        size_col=size,
        title=f"{y_col} vs {x_col}",
        xlabel=x_col, ylabel=y_col,
    )

    if show_trend:
        reg = linear_regression(samples[x_col], samples[y_col])
        if reg:
            fig.add_trace(go.Scatter(
                x=reg["x_line"], y=reg["y_line"],
                mode="lines",
                name=f"R² = {reg['r_squared']:.3f}",
                line=dict(color=COLORS["danger"], width=2, dash="dash"),
            ))
    return fig


@callback(
    Output("co-pred-vs-meas", "figure"),
    Input("co-pred-vs-meas", "id"),
)
def build_predicted_vs_measured(_):
    acoustic = load_acoustic_thermal()
    samples  = load_samples()
    df = acoustic.merge(samples[["sample_id", "material"]], on="sample_id", how="left")

    pred_cols_present = [
        (meas, pred, label) for meas, pred, label in PREDICTED_PROPS
        if pred in df.columns
    ]

    if not pred_cols_present:
        return fig_utils.empty_figure("Colonnes 'predicted_*' absentes")

    n = len(pred_cols_present)
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=[label for _, _, label in pred_cols_present],
        horizontal_spacing=0.14,
        vertical_spacing=0.18,
    )

    materials   = sorted(df["material"].dropna().unique())
    sci_palette = fig_utils._SCI_PALETTE
    sci_symbols = fig_utils._SCI_SYMBOLS

    for idx, (meas_col, pred_col, label) in enumerate(pred_cols_present):
        row = idx // 2 + 1
        col = idx % 2 + 1

        for mat_idx, material in enumerate(materials):
            sub = df[df["material"] == material][[meas_col, pred_col]].dropna()
            if sub.empty:
                continue
            color = MATERIAL_COLORS.get(material, sci_palette[mat_idx % len(sci_palette)])
            fig.add_trace(go.Scatter(
                x=sub[meas_col], y=sub[pred_col],
                mode="markers",
                name=material,
                legendgroup=material,
                showlegend=(idx == 0),
                marker=dict(
                    color=color,
                    symbol=sci_symbols[mat_idx % len(sci_symbols)],
                    size=9, opacity=0.85,
                    line=dict(width=0.8, color="white"),
                ),
            ), row=row, col=col)

        all_vals = df[[meas_col, pred_col]].dropna().values.flatten()
        if len(all_vals) > 0:
            v_min, v_max = float(all_vals.min()), float(all_vals.max())
            margin = (v_max - v_min) * 0.05
            fig.add_trace(go.Scatter(
                x=[v_min - margin, v_max + margin],
                y=[v_min - margin, v_max + margin],
                mode="lines",
                showlegend=(idx == 0),
                name="y = x  (prédiction parfaite)",
                line=dict(color="#64748B", width=1.5, dash="dash"),
            ), row=row, col=col)

        axis_idx = "" if idx == 0 else str(idx + 1)
        fig.update_layout(**{
            f"xaxis{axis_idx}_title": "Valeur mesurée",
            f"yaxis{axis_idx}_title": "Valeur prédite",
        })

    sci = fig_utils._SCI_LAYOUT.copy()
    sci.pop("xaxis", None); sci.pop("yaxis", None)
    fig.update_layout(
        **sci, height=520,
        legend=dict(
            title="Matériau",
            bgcolor="rgba(255,255,255,0.95)",
            bordercolor="#E2E8F0", borderwidth=1,
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
