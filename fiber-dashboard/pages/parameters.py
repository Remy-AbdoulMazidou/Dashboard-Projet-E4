import numpy as np
from dash import html, dcc, callback, Input, Output

from components.filters import sample_selector
from components.info_box import info_box, guide_box, warn_box, chart_header
from utils.data_loader import load_samples, load_parameter_sweep
from utils import figures as fig_utils
from config import COLORS


def layout() -> html.Div:
    samples = load_samples()
    sweep = load_parameter_sweep()
    sweep_sample_ids = sweep["sample_id"].unique().tolist()
    valid_ids = [s for s in samples["sample_id"].tolist() if s in sweep_sample_ids]

    return html.Div([
        html.H2("Paramètres de l'algorithme de segmentation", className="page-title"),
        html.P(
            "Analyse de sensibilité : comment les paramètres de l'algorithme influencent "
            "les résultats de la segmentation µ-CT (nombre de fibres, contacts, temps de calcul).",
            className="page-subtitle",
        ),

        info_box(
            "L'algorithme de segmentation détecte les fibres dans un volume 3D et identifie "
            "leurs contacts. Ses deux paramètres principaux sont : "
            "(1) le seuil de misorientation — angle maximal entre deux voxels pour être considérés "
            "comme appartenant à la même fibre, et "
            "(2) le nombre de directions — précision de l'analyse d'orientation (plus = précis mais lent)."
        ),

        html.Div([
            sample_selector("pa-sample-select", valid_ids),
        ], className="filter-bar"),

        html.Div([
            html.Div([
                chart_header(
                    "Fibres détectées vs seuil de misorientation",
                    "Un seuil trop bas → fibres fragmentées (surestimation). "
                    "Un seuil trop élevé → fibres fusionnées (sous-estimation). "
                    "Cherchez le plateau stable.",
                ),
                dcc.Graph(id="pa-line-fibers"),
            ], className="card col-6"),
            html.Div([
                chart_header(
                    "Contacts identifiés vs seuil de misorientation",
                    "Le nombre de contacts entre fibres doit se stabiliser. "
                    "Un pic suivi d'une chute peut indiquer des fusions parasites.",
                ),
                dcc.Graph(id="pa-line-contacts"),
            ], className="card col-6"),
        ], className="row"),

        html.Div([
            html.Div([
                chart_header(
                    "Temps de calcul vs nombre de directions",
                    "Le temps augmente quasi-linéairement avec le nombre de directions. "
                    "Cherchez le bon compromis précision/temps (souvent entre 13 et 26 directions).",
                ),
                dcc.Graph(id="pa-line-runtime"),
            ], className="card col-12"),
        ], className="row"),

        html.Div([
            html.Div([
                chart_header(
                    "Carte de chaleur — Fibres détectées (seuil × directions)",
                    "Visualisez simultanément l'effet des deux paramètres. "
                    "Les cases les plus bleues indiquent les combinaisons optimales. "
                    "Idéalement, la zone centrale doit être homogène (résultat stable).",
                ),
                dcc.Graph(id="pa-heatmap"),
            ], className="card col-12"),
        ], className="row"),

    ], className="page-content")


@callback(
    Output("pa-line-fibers", "figure"),
    Output("pa-line-contacts", "figure"),
    Output("pa-line-runtime", "figure"),
    Output("pa-heatmap", "figure"),
    Input("pa-sample-select", "value"),
)
def update_parameters(sample_id):
    empty = fig_utils.empty_figure()
    if not sample_id:
        return empty, empty, empty, empty

    sweep = load_parameter_sweep()
    df = sweep[sweep["sample_id"] == sample_id]

    if df.empty:
        return empty, empty, empty, empty

    agg_threshold = (
        df.groupby("misorientation_threshold")
        .agg(
            fiber_count=("fiber_count", "mean"),
            contact_count=("contact_count", "mean"),
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

    return line_fibers, line_contacts, line_runtime, heatmap
