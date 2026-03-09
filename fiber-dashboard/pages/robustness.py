import numpy as np
from dash import html, dcc, callback, Input, Output

from components.filters import sample_selector
from components.info_box import info_box, guide_box, warn_box, chart_header
from utils.data_loader import load_samples, load_robustness
from utils import figures as fig_utils
from config import COLORS


def layout() -> html.Div:
    samples = load_samples()
    robust = load_robustness()
    robust_ids = robust["sample_id"].unique().tolist()
    valid_ids = [s for s in samples["sample_id"].tolist() if s in robust_ids]

    return html.Div([
        html.H2("Robustesse et limitations de l'algorithme", className="page-title"),
        html.P(
            "Évaluation de la stabilité des résultats face à une dégradation "
            "artificielle de la qualité d'image (sous-échantillonnage et ajout de bruit).",
            className="page-subtitle",
        ),

        info_box(
            "Pour valider un algorithme de segmentation, on teste intentionnellement "
            "des conditions dégradées : résolution réduite (sous-échantillonnage) et bruit artificiel. "
            "Si les résultats restent stables malgré la dégradation, l'algorithme est robuste. "
            "Ces tests permettent d'identifier les limites d'utilisation et les seuils critiques."
        ),

        html.Div([
            sample_selector("rb-sample-select", valid_ids),
        ], className="filter-bar"),

        warn_box(
            "Zones critiques : un facteur de sous-échantillonnage ≥ 3 ou un niveau de bruit ≥ 0,15 "
            "dégrade significativement la séparation individuelle des fibres (perte > 40 % de précision)."
        ),

        # Sous-échantillonnage
        html.H3("Impact du sous-échantillonnage (résolution réduite)", className="section-separator"),
        html.Div([
            html.Div([
                chart_header(
                    "Fibres détectées vs facteur de sous-échantillonnage",
                    "Si le nombre de fibres chute fortement avec un faible facteur, "
                    "la résolution est critique pour cet échantillon.",
                ),
                dcc.Graph(id="rb-line-ds-fibers"),
            ], className="card col-12"),
        ], className="row"),

        html.Div([
            html.Div([
                chart_header(
                    "Dispersion d'orientation vs sous-échantillonnage",
                    "La dispersion d'orientation doit rester stable. "
                    "Une dérive indique que l'algorithme confond les orientations à basse résolution.",
                ),
                dcc.Graph(id="rb-line-ds-orient"),
            ], className="card col-6"),
            html.Div([
                chart_header(
                    "Score qualité — carte (sous-échantillonnage × bruit)",
                    "Vue combinée : chaque cellule montre le score qualité pour une combinaison "
                    "de résolution et de bruit. Les zones foncées = conditions critiques à éviter.",
                ),
                dcc.Graph(id="rb-heatmap-quality"),
            ], className="card col-6"),
        ], className="row"),

        # Bruit
        html.H3("Impact du bruit sur l'image", className="section-separator"),
        html.Div([
            html.Div([
                chart_header(
                    "Fibres détectées vs niveau de bruit",
                    "Un fort bruit peut créer des artefacts détectés comme de fausses fibres "
                    "(surestimation) ou masquer des fibres réelles (sous-estimation).",
                ),
                dcc.Graph(id="rb-line-noise-fibers"),
            ], className="card col-12"),
        ], className="row"),

    ], className="page-content")


@callback(
    Output("rb-line-ds-fibers", "figure"),
    Output("rb-line-ds-orient", "figure"),
    Output("rb-heatmap-quality", "figure"),
    Output("rb-line-noise-fibers", "figure"),
    Input("rb-sample-select", "value"),
)
def update_robustness(sample_id):
    empty = fig_utils.empty_figure()
    if not sample_id:
        return empty, empty, empty, empty

    robust = load_robustness()
    df = robust[robust["sample_id"] == sample_id]

    if df.empty:
        return empty, empty, empty, empty

    ds_df = df.groupby("downsampling_factor").agg(
        fiber_count=("fiber_count", "mean"),
        orientation_dispersion=("orientation_dispersion", "mean"),
    ).reset_index()

    noise_df = df.groupby("noise_level").agg(
        fiber_count=("fiber_count", "mean"),
    ).reset_index()

    line_ds_fibers = fig_utils.line_chart(
        ds_df, "downsampling_factor", "fiber_count",
        title="Fibres détectées vs facteur de sous-échantillonnage",
        xlabel="Facteur de sous-échantillonnage", ylabel="Fibres détectées",
    )
    line_ds_orient = fig_utils.line_chart(
        ds_df, "downsampling_factor", "orientation_dispersion",
        title="Dispersion d'orientation vs sous-échantillonnage",
        xlabel="Facteur", ylabel="Dispersion (°)",
    )

    pivot = df.groupby(["downsampling_factor", "noise_level"])["quality_score"].mean().unstack(fill_value=0)
    ds_vals = pivot.index.tolist()
    noise_vals = [str(round(c, 2)) for c in pivot.columns.tolist()]
    heatmap_quality = fig_utils.heatmap_2d(
        pivot.values, noise_vals, [str(d) for d in ds_vals],
        title="Score qualité — (sous-échantillonnage × bruit)",
        xlabel="Niveau de bruit", ylabel="Facteur sous-échantillonnage",
    )

    line_noise_fibers = fig_utils.line_chart(
        noise_df, "noise_level", "fiber_count",
        title="Fibres détectées vs niveau de bruit",
        xlabel="Niveau de bruit", ylabel="Fibres détectées",
    )
    return line_ds_fibers, line_ds_orient, heatmap_quality, line_noise_fibers
