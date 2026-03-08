import numpy as np
import pandas as pd
from dash import html, dcc, callback, Input, Output

from components.filters import sample_selector
from utils.data_loader import load_samples, load_parameter_sweep
from utils import figures as fig_utils
from config import COLORS


def layout() -> html.Div:
    samples = load_samples()
    sweep = load_parameter_sweep()
    sweep_sample_ids = sweep["sample_id"].unique().tolist()
    valid_ids = [s for s in samples["sample_id"].tolist() if s in sweep_sample_ids]

    return html.Div([
        html.H2("Paramètres de l'algorithme", className="page-title"),
        html.Div([
            sample_selector("pa-sample-select", valid_ids),
        ], className="filter-bar"),
        html.Div(
            [
                html.Div([dcc.Graph(id="pa-line-fibers")], className="card col-6"),
                html.Div([dcc.Graph(id="pa-line-contacts")], className="card col-6"),
            ],
            className="row",
        ),
        html.Div(
            [
                html.Div([dcc.Graph(id="pa-line-orphans")], className="card col-6"),
                html.Div([dcc.Graph(id="pa-line-runtime")], className="card col-6"),
            ],
            className="row",
        ),
        html.Div(
            [
                html.Div([dcc.Graph(id="pa-heatmap")], className="card col-7"),
                html.Div([dcc.Graph(id="pa-bar-dilation")], className="card col-5"),
            ],
            className="row",
        ),
    ], className="page-content")


@callback(
    Output("pa-line-fibers", "figure"),
    Output("pa-line-contacts", "figure"),
    Output("pa-line-orphans", "figure"),
    Output("pa-line-runtime", "figure"),
    Output("pa-heatmap", "figure"),
    Output("pa-bar-dilation", "figure"),
    Input("pa-sample-select", "value"),
)
def update_parameters(sample_id):
    empty = fig_utils.empty_figure()
    if not sample_id:
        return empty, empty, empty, empty, empty, empty

    sweep = load_parameter_sweep()
    df = sweep[sweep["sample_id"] == sample_id]

    if df.empty:
        return empty, empty, empty, empty, empty, empty

    agg_threshold = (
        df.groupby("misorientation_threshold")
        .agg(
            fiber_count=("fiber_count", "mean"),
            contact_count=("contact_count", "mean"),
            orphan_fraction=("orphan_fraction", "mean"),
        )
        .reset_index()
    )

    line_fibers = fig_utils.line_chart(
        agg_threshold, "misorientation_threshold", "fiber_count",
        title="Fibres détectées vs seuil de misorientation",
        xlabel="Seuil (°)", ylabel="Fibres détectées",
    )
    line_contacts = fig_utils.line_chart(
        agg_threshold, "misorientation_threshold", "contact_count",
        title="Contacts vs seuil de misorientation",
        xlabel="Seuil (°)", ylabel="Contacts",
    )
    line_orphans = fig_utils.line_chart(
        agg_threshold, "misorientation_threshold", "orphan_fraction",
        title="Fraction de voxels orphelins vs seuil",
        xlabel="Seuil (°)", ylabel="Fraction orphelins",
    )

    agg_ndirs = (
        df.groupby("n_directions")["runtime_sec"]
        .mean()
        .reset_index()
    )
    line_runtime = fig_utils.line_chart(
        agg_ndirs, "n_directions", "runtime_sec",
        title="Temps de calcul vs nombre de directions",
        xlabel="Directions", ylabel="Durée (s)",
    )

    pivot = df.groupby(["misorientation_threshold", "n_directions"])["fiber_count"].mean().unstack(fill_value=0)
    thresholds = pivot.index.tolist()
    n_dirs = [str(c) for c in pivot.columns.tolist()]
    z = pivot.values

    heatmap = fig_utils.heatmap_2d(
        z, n_dirs, [str(t) for t in thresholds],
        title="Fibres détectées (seuil × directions)",
        xlabel="Nombre de directions", ylabel="Seuil de misorientation (°)",
    )

    dilation_compare = (
        df.groupby("dilation_type")
        .agg(fiber_count=("fiber_count", "mean"), contact_count=("contact_count", "mean"))
        .reset_index()
    )
    dilation_long = pd.melt(dilation_compare, id_vars="dilation_type",
                             value_vars=["fiber_count", "contact_count"],
                             var_name="metric", value_name="value")
    bar_dil = fig_utils.bar_chart(
        dilation_long, "metric", "value",
        title="Longitudinal vs Isotrope",
        color_col="dilation_type",
        xlabel="Métrique", ylabel="Valeur moyenne",
    )

    return line_fibers, line_contacts, line_orphans, line_runtime, heatmap, bar_dil
