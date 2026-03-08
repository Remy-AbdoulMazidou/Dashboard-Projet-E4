import numpy as np
import pandas as pd
from dash import html, dcc, callback, Input, Output, dash_table
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from utils.data_loader import load_samples, load_acoustic_thermal
from utils.stats import pearson_matrix, top_correlations, linear_regression
from utils import figures as fig_utils
from components.info_box import info_box, guide_box, warn_box, chart_header
from config import COLORS, MATERIAL_COLORS, TABLE_STYLE


NUMERIC_COLS = [
    "porosity", "fiber_count", "contact_count", "contact_density",
    "mean_diameter_um", "std_diameter_um", "mean_length_um", "std_length_um",
    "mean_curvature", "orientation_dispersion", "slenderness_ratio",
    "runtime_sec", "quality_score", "resolution_um", "volume_mm3",
]

AXIS_OPTIONS = [{"label": c, "value": c} for c in NUMERIC_COLS]
COLOR_OPTIONS = [{"label": "material", "value": "material"},
                 {"label": "batch", "value": "batch"},
                 {"label": "status", "value": "status"}] + AXIS_OPTIONS

PREDICTED_PROPS = [
    ("airflow_resistivity",  "predicted_airflow_resistivity",  "Résistivité à l'écoulement (Pa·s/m²)"),
    ("thermal_permeability", "predicted_thermal_permeability", "Perméabilité thermique (m²)"),
    ("viscous_length_um",    "predicted_viscous_length_um",    "Longueur visqueuse Λ (µm)"),
    ("thermal_length_um",    "predicted_thermal_length_um",    "Longueur thermique Λ' (µm)"),
]


def layout() -> html.Div:
    return html.Div([
        html.H2("Corrélations et régression", className="page-title"),
        html.P(
            "Identification des descripteurs microstructuraux les plus prédictifs "
            "des propriétés acoustiques et thermiques.",
            className="page-subtitle",
        ),

        # ── Section 1 : Matrice de corrélation ──────────────────────────────
        info_box(
            "La matrice de corrélation de Pearson calcule la relation linéaire entre "
            "chaque paire de descripteurs. Les valeurs sont comprises entre −1 et +1. "
            "Plus la couleur est intense, plus la relation est forte."
        ),
        html.Div([
            html.Div([
                html.Div([
                    html.Span("Lecture de la couleur :", style={"fontSize": "11px", "color": "#8B9BB4", "marginRight": "8px"}),
                    html.Span("Rouge = corrélation négative", style={"fontSize": "11px", "color": "#F24236"}),
                    html.Span("  |  ", style={"color": "#8B9BB4", "fontSize": "11px"}),
                    html.Span("Bleu = corrélation positive", style={"fontSize": "11px", "color": "#2E86AB"}),
                    html.Span("  |  ", style={"color": "#8B9BB4", "fontSize": "11px"}),
                    html.Span("Centre blanc = pas de relation", style={"fontSize": "11px", "color": "#8B9BB4"}),
                ], style={"marginBottom": "8px", "display": "flex", "flexWrap": "wrap", "gap": "4px"}),
                dcc.Graph(id="co-heatmap"),
            ], className="card col-12"),
        ], className="row"),

        guide_box("Comment utiliser cette matrice ?", [
            "Cherchez les descripteurs microstructuraux fortement corrélés aux propriétés acoustiques (absorption_*) ou thermiques.",
            "Une corrélation > 0,7 ou < −0,7 est généralement considérée comme forte.",
            "La diagonale vaut toujours 1 (une variable est parfaitement corrélée avec elle-même).",
            "Ignorez les corrélations entre descripteurs similaires (ex. mean_length et std_length).",
        ]),

        # ── Section 2 : Scatter interactif ──────────────────────────────────
        html.H3("Scatter plot interactif", className="section-separator"),
        info_box(
            "Explorez librement les relations entre deux descripteurs. "
            "Choisissez les axes X et Y, la couleur des points (par matériau, lot…) "
            "et activez la droite de régression pour quantifier la tendance (R²)."
        ),
        html.Div([
            html.Div([
                html.H4("Paramètres du graphique", className="section-title"),
                html.Div([
                    html.Div([
                        html.Label("Axe X", style={"color": COLORS["text_secondary"],
                                                     "fontSize": "11px", "fontWeight": "600"}),
                        dcc.Dropdown(id="co-x-axis", options=AXIS_OPTIONS,
                                      value="mean_diameter_um",
                                      className="dash-dropdown-dark", style={"fontSize": "13px"}),
                    ], style={"flex": 1}),
                    html.Div([
                        html.Label("Axe Y", style={"color": COLORS["text_secondary"],
                                                     "fontSize": "11px", "fontWeight": "600"}),
                        dcc.Dropdown(id="co-y-axis", options=AXIS_OPTIONS,
                                      value="porosity",
                                      className="dash-dropdown-dark", style={"fontSize": "13px"}),
                    ], style={"flex": 1}),
                    html.Div([
                        html.Label("Couleur", style={"color": COLORS["text_secondary"],
                                                      "fontSize": "11px", "fontWeight": "600"}),
                        dcc.Dropdown(id="co-color", options=COLOR_OPTIONS,
                                      value="material",
                                      className="dash-dropdown-dark", style={"fontSize": "13px"}),
                    ], style={"flex": 1}),
                    html.Div([
                        html.Label("Taille des points", style={"color": COLORS["text_secondary"],
                                                         "fontSize": "11px", "fontWeight": "600"}),
                        dcc.Dropdown(id="co-size",
                                      options=[{"label": "— uniforme", "value": "none"}] + AXIS_OPTIONS,
                                      value="none",
                                      className="dash-dropdown-dark", style={"fontSize": "13px"}),
                    ], style={"flex": 1}),
                    html.Div([
                        html.Label("Régression", style={"color": COLORS["text_secondary"],
                                                           "fontSize": "11px", "fontWeight": "600"}),
                        dcc.Checklist(
                            id="co-trendline",
                            options=[{"label": " Afficher R²", "value": "show"}],
                            value=[],
                            style={"color": COLORS["text_primary"], "fontSize": "13px",
                                   "marginTop": "6px"},
                        ),
                    ], style={"flex": 1}),
                ], style={"display": "flex", "gap": "12px", "marginBottom": "12px"}),
                dcc.Graph(id="co-scatter"),
            ], className="card col-8"),
            html.Div([
                chart_header(
                    "Top 15 corrélations",
                    "Paires de variables les plus fortement corrélées, triées par |r|. "
                    "Cliquez sur une colonne pour trier.",
                ),
                html.Div(id="co-top-table"),
            ], className="card col-4"),
        ], className="row"),

        guide_box("Interpréter le R² de la régression", [
            "R² = 1,0 → la droite explique 100 % de la variance (relation parfaite).",
            "R² > 0,7 → bonne prédictabilité linéaire entre les deux variables.",
            "R² < 0,3 → relation faible ou non-linéaire — envisager d'autres modèles.",
            "R² proche de 0 → aucune relation linéaire détectable.",
        ]),

        # ── Section 3 : Expérimental vs Prédit ──────────────────────────────
        html.H3("Validation du modèle — Expérimental vs Prédit", className="section-separator"),
        info_box(
            "Ces graphiques comparent les valeurs mesurées expérimentalement (axe X) "
            "avec les valeurs prédites par le modèle de régression (axe Y). "
            "La diagonale y = x représente la prédiction parfaite : "
            "plus les points sont proches de cette ligne, meilleur est le modèle."
        ),
        guide_box("Comment évaluer la qualité du modèle ?", [
            "Points sur la diagonale → prédiction parfaite.",
            "Points au-dessus → le modèle surestime.",
            "Points en dessous → le modèle sous-estime.",
            "Dispersion autour de la diagonale → erreur systématique ou variabilité non capturée.",
            "Couleurs par matériau : si un matériau est systématiquement décalé, le modèle lui est moins adapté.",
        ]),
        html.Div([
            html.Div([dcc.Graph(id="co-pred-vs-meas")], className="card col-12"),
        ], className="row"),

    ], className="page-content")


@callback(
    Output("co-heatmap", "figure"),
    Output("co-top-table", "children"),
    Input("co-heatmap", "id"),
)
def build_correlation_matrix(_):
    samples = load_samples()
    numeric = samples[NUMERIC_COLS].dropna(how="all")
    corr = pearson_matrix(numeric)
    heatmap = fig_utils.heatmap_corr(corr, "Matrice de corrélation — descripteurs microstructuraux")

    top = top_correlations(corr, n=15)
    top["r"] = top["r"].round(3)
    top["abs_r"] = top["abs_r"].round(3)
    table = dash_table.DataTable(
        data=top[["var_1", "var_2", "r", "abs_r"]].to_dict("records"),
        columns=[{"name": c, "id": c} for c in ["var_1", "var_2", "r", "abs_r"]],
        sort_action="native",
        page_size=15,
        **TABLE_STYLE,
    )
    return heatmap, table


@callback(
    Output("co-scatter", "figure"),
    Input("co-x-axis", "value"),
    Input("co-y-axis", "value"),
    Input("co-color", "value"),
    Input("co-size", "value"),
    Input("co-trendline", "value"),
)
def update_scatter(x_col, y_col, color_col, size_col, trendline):
    samples = load_samples()
    size = size_col if size_col and size_col != "none" else None
    show_trend = "show" in (trendline or [])
    if size and size not in samples.columns:
        size = None

    fig = fig_utils.scatter(
        samples, x_col, y_col,
        color_col=color_col if color_col in samples.columns else None,
        size_col=size,
        title=f"{y_col} vs {x_col}",
        xlabel=x_col, ylabel=y_col,
        trendline=show_trend,
    )

    if show_trend and not size:
        reg = linear_regression(samples[x_col], samples[y_col])
        if reg:
            fig.add_trace(go.Scatter(
                x=reg["x_line"], y=reg["y_line"],
                mode="lines",
                name=f"R²={reg['r_squared']:.3f}",
                line=dict(color=COLORS["accent"], width=2, dash="dash"),
            ))
    return fig


@callback(
    Output("co-pred-vs-meas", "figure"),
    Input("co-pred-vs-meas", "id"),
)
def build_predicted_vs_measured(_):
    acoustic = load_acoustic_thermal()
    samples = load_samples()
    df = acoustic.merge(samples[["sample_id", "material"]], on="sample_id", how="left")

    pred_cols_present = [
        (meas, pred, label) for meas, pred, label in PREDICTED_PROPS
        if pred in df.columns
    ]

    if not pred_cols_present:
        return fig_utils.empty_figure("Colonnes 'predicted_*' absentes — régénérez les mock data")

    n = len(pred_cols_present)
    ncols = 2
    nrows = int(np.ceil(n / ncols))

    subplot_titles = [label for _, _, label in pred_cols_present]
    fig = make_subplots(
        rows=nrows, cols=ncols,
        subplot_titles=subplot_titles,
        horizontal_spacing=0.12,
        vertical_spacing=0.16,
    )

    materials = df["material"].dropna().unique()
    sci_palette = fig_utils._SCI_PALETTE
    sci_symbols = fig_utils._SCI_SYMBOLS

    for idx, (meas_col, pred_col, label) in enumerate(pred_cols_present):
        row = idx // ncols + 1
        col = idx % ncols + 1

        for mat_idx, material in enumerate(sorted(materials)):
            sub = df[df["material"] == material][[meas_col, pred_col]].dropna()
            if sub.empty:
                continue
            color = MATERIAL_COLORS.get(material, sci_palette[mat_idx % len(sci_palette)])
            fig.add_trace(
                go.Scatter(
                    x=sub[meas_col],
                    y=sub[pred_col],
                    mode="markers",
                    name=material,
                    legendgroup=material,
                    showlegend=(idx == 0),
                    marker=dict(
                        color=color,
                        symbol=sci_symbols[mat_idx % len(sci_symbols)],
                        size=9,
                        opacity=0.85,
                        line=dict(width=0.5, color="#333"),
                    ),
                ),
                row=row, col=col,
            )

        all_vals = df[[meas_col, pred_col]].dropna().values.flatten()
        if len(all_vals) > 0:
            v_min, v_max = float(all_vals.min()), float(all_vals.max())
            margin = (v_max - v_min) * 0.05
            fig.add_trace(
                go.Scatter(
                    x=[v_min - margin, v_max + margin],
                    y=[v_min - margin, v_max + margin],
                    mode="lines",
                    showlegend=(idx == 0),
                    name="y = x  (prédiction parfaite)",
                    line=dict(color="#333", width=1.5, dash="dash"),
                ),
                row=row, col=col,
            )

        axis_idx = "" if idx == 0 else str(idx + 1)
        fig.update_layout(**{
            f"xaxis{axis_idx}_title": "Valeur mesurée",
            f"yaxis{axis_idx}_title": "Valeur prédite",
        })

    sci = fig_utils._SCI_LAYOUT.copy()
    sci.pop("xaxis", None)
    sci.pop("yaxis", None)
    fig.update_layout(
        **sci,
        height=550,
        legend=dict(
            title="Matériau",
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
