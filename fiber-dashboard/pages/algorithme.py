import numpy as np
from dash import html, dcc, callback, Input, Output

from components.filters import sample_selector
from components.info_box import info_box, guide_box, warn_box, conclusion_box, chart_header
from utils.data_loader import load_samples, load_parameter_sweep, load_robustness
from utils import figures as fig_utils
from config import COLORS


def layout() -> html.Div:
    samples = load_samples()

    sweep        = load_parameter_sweep()
    sweep_ids    = sweep["sample_id"].unique().tolist()
    pa_valid_ids = [s for s in samples["sample_id"].tolist() if s in sweep_ids]

    robust       = load_robustness()
    robust_ids   = robust["sample_id"].unique().tolist()
    rb_valid_ids = [s for s in samples["sample_id"].tolist() if s in robust_ids]

    return html.Div([

        # ── En-tête ──────────────────────────────────────────────────────
        html.H2("⚙️ Analyse de l'algorithme de segmentation", className="page-title"),
        html.P(
            "Sensibilité des paramètres de segmentation µ-CT et évaluation de la robustesse "
            "de l'algorithme face à une dégradation de la qualité d'image.",
            className="page-subtitle",
        ),

        # ── Section 1 : Sensibilité des paramètres ────────────────────────
        html.H3("Sensibilité des paramètres — Fibres détectées (seuil × directions)", className="section-separator"),
        info_box(
            "L'algorithme de segmentation possède deux paramètres clés : "
            "(1) le seuil de misorientation — angle maximal entre deux voxels voisins pour être "
            "classés dans la même fibre, et "
            "(2) le nombre de directions — précision de l'analyse d'orientation (plus = précis, mais plus lent). "
            "La carte de chaleur ci-dessous montre comment le nombre de fibres détectées varie "
            "simultanément en fonction de ces deux paramètres."
        ),
        guide_box("Comment identifier le réglage optimal ?", [
            "Zone homogène au centre de la carte → les paramètres sont robustes (résultat stable).",
            "Gradient fort en vertical → le seuil de misorientation est critique pour cet échantillon.",
            "Gradient fort en horizontal → le nombre de directions impacte beaucoup la détection.",
            "Valeur trop faible du seuil → fibres fragmentées (surestimation du nombre).",
            "Valeur trop élevée → fibres fusionnées (sous-estimation du nombre).",
        ]),
        html.Div([
            sample_selector("alg-pa-sample", pa_valid_ids),
        ], className="filter-bar"),
        html.Div([
            html.Div([
                chart_header(
                    "Carte de chaleur — Fibres détectées (seuil × directions)",
                    "Chaque cellule = nombre moyen de fibres détectées pour cette combinaison de paramètres. "
                    "Les zones les plus bleues correspondent aux conditions optimales stables.",
                ),
                dcc.Graph(id="alg-pa-heatmap", style={"height": "400px"}),
            ], className="card col-12"),
        ], className="row"),

        # ── Section 2 : Robustesse ────────────────────────────────────────
        html.H3("Robustesse — Score qualité (sous-échantillonnage × bruit)", className="section-separator"),
        info_box(
            "Pour valider un algorithme de segmentation, on dégrade intentionnellement les images "
            "et on vérifie que les résultats restent stables. Deux types de dégradation sont testés : "
            "(1) sous-échantillonnage — réduction de la résolution (facteur 1 = original, 4 = 4× moins résolu), "
            "(2) ajout de bruit gaussien — simule un mauvais rapport signal/bruit au scan. "
            "La carte de chaleur montre le score qualité moyen pour chaque combinaison."
        ),
        warn_box(
            "Zones critiques : sous-échantillonnage ≥ 3 OU bruit ≥ 0,15 → "
            "perte de précision > 40 % (fibres fusionnées ou artefacts non détectés)."
        ),
        html.Div([
            sample_selector("alg-rb-sample", rb_valid_ids),
        ], className="filter-bar"),
        html.Div([
            html.Div([
                chart_header(
                    "Score qualité (sous-échantillonnage × niveau de bruit)",
                    "Chaque cellule = score qualité moyen (0–5). "
                    "Les cellules claires = bonnes conditions. Les cellules foncées = conditions critiques à éviter.",
                ),
                dcc.Graph(id="alg-rb-heatmap", style={"height": "400px"}),
            ], className="card col-12"),
        ], className="row"),

        # ── Conclusion ───────────────────────────────────────────────────
        conclusion_box(
            "Résultats clés — Algorithme de segmentation",
            "L'analyse de sensibilité montre qu'un seuil de misorientation entre 15° et 25° "
            "et un nombre de directions entre 13 et 26 offrent les résultats les plus stables "
            "pour la majorité des échantillons. Au-delà, la détection se dégrade. "
            "Les tests de robustesse confirment que l'algorithme reste fiable jusqu'à un "
            "sous-échantillonnage ×2 et un bruit < 0,10. Ces seuils critiques définissent "
            "les conditions minimales d'acquisition µ-CT à respecter pour garantir la qualité "
            "des résultats de segmentation.",
        ),

    ], className="page-content")


@callback(
    Output("alg-pa-heatmap", "figure"),
    Input("alg-pa-sample", "value"),
)
def update_param_heatmap(sample_id):
    if not sample_id:
        return fig_utils.empty_figure("Sélectionnez un échantillon")

    sweep = load_parameter_sweep()
    df    = sweep[sweep["sample_id"] == sample_id]

    if df.empty:
        return fig_utils.empty_figure("Aucune donnée pour cet échantillon")

    pivot = df.groupby(["misorientation_threshold", "n_directions"])["fiber_count"].mean().unstack(fill_value=0)
    thresholds = pivot.index.tolist()
    n_dirs     = [str(c) for c in pivot.columns.tolist()]

    return fig_utils.heatmap_2d(
        pivot.values,
        n_dirs, [str(t) for t in thresholds],
        title="Fibres détectées — (seuil de misorientation × nombre de directions)",
        xlabel="Nombre de directions",
        ylabel="Seuil de misorientation (°)",
    )


@callback(
    Output("alg-rb-heatmap", "figure"),
    Input("alg-rb-sample", "value"),
)
def update_robustness_heatmap(sample_id):
    if not sample_id:
        return fig_utils.empty_figure("Sélectionnez un échantillon")

    robust = load_robustness()
    df     = robust[robust["sample_id"] == sample_id]

    if df.empty:
        return fig_utils.empty_figure("Aucune donnée pour cet échantillon")

    pivot      = df.groupby(["downsampling_factor", "noise_level"])["quality_score"].mean().unstack(fill_value=0)
    ds_vals    = pivot.index.tolist()
    noise_vals = [str(round(c, 2)) for c in pivot.columns.tolist()]

    return fig_utils.heatmap_2d(
        pivot.values,
        noise_vals, [str(d) for d in ds_vals],
        title="Score qualité — (sous-échantillonnage × niveau de bruit)",
        xlabel="Niveau de bruit",
        ylabel="Facteur de sous-échantillonnage",
    )
