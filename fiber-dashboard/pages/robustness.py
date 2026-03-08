import numpy as np
from dash import html, dcc, callback, Input, Output

from components.filters import sample_selector
from utils.data_loader import load_samples, load_robustness
from utils import figures as fig_utils
from config import COLORS


def layout() -> html.Div:
    samples = load_samples()
    robust = load_robustness()
    robust_ids = robust["sample_id"].unique().tolist()
    valid_ids = [s for s in samples["sample_id"].tolist() if s in robust_ids]

    return html.Div([
        html.H2("Robustesse et limitations", className="page-title"),
        html.Div([
            sample_selector("rb-sample-select", valid_ids),
        ], className="filter-bar"),

        html.Div(
            html.Div([
                html.Div(
                    "Les zones ombrées indiquent les régions où l'algorithme devient instable "
                    "(degradation > 40% du score qualité initial). "
                    "Un facteur de sous-échantillonnage ≥ 3 ou un niveau de bruit ≥ 0.15 "
                    "dégrade significativement la séparation individuelle des fibres.",
                    className="annotation-box",
                ),
            ], className="card col-12"),
            className="row",
        ),

        html.Div(
            [
                html.Div([dcc.Graph(id="rb-line-ds-fibers")], className="card col-6"),
                html.Div([dcc.Graph(id="rb-line-ds-diameter")], className="card col-6"),
            ],
            className="row",
        ),
        html.Div(
            [
                html.Div([dcc.Graph(id="rb-line-ds-orient")], className="card col-6"),
                html.Div([dcc.Graph(id="rb-heatmap-quality")], className="card col-6"),
            ],
            className="row",
        ),
        html.Div(
            [
                html.Div([dcc.Graph(id="rb-line-noise-fibers")], className="card col-6"),
                html.Div([dcc.Graph(id="rb-line-noise-diameter")], className="card col-6"),
            ],
            className="row",
        ),
    ], className="page-content")


@callback(
    Output("rb-line-ds-fibers", "figure"),
    Output("rb-line-ds-diameter", "figure"),
    Output("rb-line-ds-orient", "figure"),
    Output("rb-heatmap-quality", "figure"),
    Output("rb-line-noise-fibers", "figure"),
    Output("rb-line-noise-diameter", "figure"),
    Input("rb-sample-select", "value"),
)
def update_robustness(sample_id):
    empty = fig_utils.empty_figure()
    if not sample_id:
        return empty, empty, empty, empty, empty, empty

    robust = load_robustness()
    df = robust[robust["sample_id"] == sample_id]

    if df.empty:
        return empty, empty, empty, empty, empty, empty

    ds_df = df.groupby("downsampling_factor").agg(
        fiber_count=("fiber_count", "mean"),
        mean_diameter_um=("mean_diameter_um", "mean"),
        orientation_dispersion=("orientation_dispersion", "mean"),
    ).reset_index()

    noise_df = df.groupby("noise_level").agg(
        fiber_count=("fiber_count", "mean"),
        mean_diameter_um=("mean_diameter_um", "mean"),
    ).reset_index()

    line_ds_fibers = fig_utils.line_chart(
        ds_df, "downsampling_factor", "fiber_count",
        title="Fibres détectées vs facteur de sous-échantillonnage",
        xlabel="Facteur de sous-échantillonnage", ylabel="Fibres détectées",
    )
    line_ds_diam = fig_utils.line_chart(
        ds_df, "downsampling_factor", "mean_diameter_um",
        title="Diamètre moyen vs sous-échantillonnage",
        xlabel="Facteur", ylabel="Diamètre moyen (µm)",
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
    line_noise_diam = fig_utils.line_chart(
        noise_df, "noise_level", "mean_diameter_um",
        title="Diamètre moyen vs niveau de bruit",
        xlabel="Niveau de bruit", ylabel="Diamètre moyen (µm)",
    )

    return line_ds_fibers, line_ds_diam, line_ds_orient, heatmap_quality, line_noise_fibers, line_noise_diam
