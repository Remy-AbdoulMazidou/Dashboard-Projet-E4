from dash import html, dcc, callback, Input, Output

from components.filters import material_filter, batch_filter, filter_bar
from components.kpi_card import kpi_card
from components.info_box import info_box, guide_box, conclusion_box, chart_header
from utils.data_loader import load_fibers, filter_samples
from utils import figures as fig_utils
from config import COLORS


def layout() -> html.Div:
    return html.Div([

        # ── En-tête ──────────────────────────────────────────────────────
        html.H2("🔬 Microstructure des fibres", className="page-title"),
        html.P(
            "Analyse morphologique complète des fibres extraites par segmentation µ-CT : "
            "distributions de taille, orientations 3D et comparaisons entre matériaux.",
            className="page-subtitle",
        ),

        # ── Filtres ──────────────────────────────────────────────────────
        filter_bar(
            material_filter("ms-filter-material"),
            batch_filter("ms-filter-batch"),
        ),

        # ── KPIs ─────────────────────────────────────────────────────────
        html.Div(id="ms-kpi-row", className="kpi-row"),

        # ── Section 1 : Distributions par matériau ───────────────────────
        html.H3("Distributions morphologiques par matériau", className="section-separator"),
        info_box(
            "Les boîtes à moustaches comparent la distribution du diamètre et de la longueur "
            "entre les 6 matériaux. La ligne centrale = médiane, la boîte = 50 % des valeurs "
            "(Q1–Q3), les moustaches = valeurs extrêmes, les points = données aberrantes."
        ),
        html.Div([
            html.Div([
                chart_header(
                    "Diamètre par matériau (µm)",
                    "Un diamètre plus faible augmente la surface de contact avec l'air, "
                    "ce qui améliore l'absorption acoustique par friction visqueuse.",
                ),
                dcc.Graph(id="ms-box-diameter", style={"height": "340px"}),
            ], className="card col-6"),
            html.Div([
                chart_header(
                    "Longueur par matériau (µm)",
                    "Des fibres plus longues favorisent l'interconnexion du réseau fibreux "
                    "et influencent la perméabilité thermique du matériau.",
                ),
                dcc.Graph(id="ms-box-length", style={"height": "340px"}),
            ], className="card col-6"),
        ], className="row"),

        # ── Section 2 : Distributions de probabilité (KDE) ───────────────
        html.H3("Distributions de probabilité — style publication", className="section-separator"),
        info_box(
            "Les courbes KDE (Kernel Density Estimation) estiment la distribution continue "
            "d'un descripteur pour chaque matériau. Contrairement à un histogramme, la courbe "
            "est lissée par un noyau gaussien (règle de Silverman). "
            "Les lignes pointillées verticales indiquent la moyenne de chaque groupe."
        ),
        guide_box("Comment lire une courbe KDE ?", [
            "Pic étroit et haut → fibres très uniformes (bonne reproductibilité de fabrication).",
            "Pic large et plat → forte variabilité (propriétés moins prévisibles).",
            "Distribution bimodale (2 pics) → deux populations distinctes dans l'échantillon.",
            "Décalage entre matériaux → différence microstructurale réelle à exploiter.",
            "L'aire sous la courbe = 1 (densité de probabilité normalisée).",
        ]),
        html.Div([
            html.Div([
                chart_header(
                    "PDF — Diamètre (µm)",
                    "Distribution de probabilité du diamètre de fibre par matériau. "
                    "Le Nylon et le Carbone ont les distributions les plus contrastées.",
                ),
                dcc.Graph(id="ms-pdf-diameter", style={"height": "280px"}),
            ], className="card col-4"),
            html.Div([
                chart_header(
                    "Rosace des orientations azimutales ψ",
                    "Distribution polaire des angles ψ dans le plan. "
                    "Une rosace uniforme = réseau isotrope. Un lobe = orientation préférentielle.",
                ),
                dcc.Graph(id="ms-rose-psi", style={"height": "280px"}),
            ], className="card col-4"),
            html.Div([
                chart_header(
                    "PDF — Angle zénithal θ (0–90°)",
                    "Inclinaison hors du plan. θ = 0° → fibre perpendiculaire au plan d'imagerie. "
                    "θ = 90° → fibre couchée dans le plan.",
                ),
                dcc.Graph(id="ms-pdf-theta", style={"height": "280px"}),
            ], className="card col-4"),
        ], className="row"),

        # ── Section 3 : Figure de pôle ────────────────────────────────────
        html.H3("Figure de pôle — projection stéréographique 3D", className="section-separator"),
        info_box(
            "La figure de pôle représente l'orientation 3D de chaque fibre en 2D. "
            "Le rayon = angle zénithal θ (centre = fibres ⊥ au plan, bord = fibres dans le plan). "
            "L'angle angulaire = angle azimutal ψ dans le plan. "
            "La taille des points est proportionnelle à la longueur de la fibre."
        ),
        guide_box("Comment lire la figure de pôle ?", [
            "Points concentrés au centre → fibres perpendiculaires au plan (orientation préférentielle).",
            "Points à la périphérie → fibres couchées dans le plan (matériau en couches).",
            "Distribution uniforme sur tout le cercle → réseau isotrope (aucune orientation dominante).",
            "Couleurs distinctes par matériau → comparez les orientations préférentielles.",
            "Cette visualisation est standard dans les publications de science des matériaux.",
        ]),
        html.Div([
            html.Div([
                dcc.Graph(id="ms-pole-figure", style={"height": "520px"}),
            ], className="card col-12"),
        ], className="row"),

        # ── Section 4 : Géométrie individuelle des fibres ─────────────────
        html.H3("Géométrie individuelle des fibres", className="section-separator"),
        html.Div([
            html.Div([
                chart_header(
                    "Longueur × diamètre par fibre",
                    "Chaque point est une fibre. Révèle la polydispersité réelle "
                    "et les populations distinctes par matériau.",
                ),
                dcc.Graph(id="ms-scatter-lxd", style={"height": "380px"}),
            ], className="card col-8"),
            html.Div([
                chart_header(
                    "Contacts par fibre",
                    "Nombre de liaisons fibre-fibre. Un réseau très interconnecté "
                    "améliore la rigidité mécanique du matériau.",
                ),
                dcc.Graph(id="ms-box-contacts", style={"height": "380px"}),
            ], className="card col-4"),
        ], className="row"),
        html.Div([
            html.Div([
                chart_header(
                    "Coefficient de variation du diamètre (CV = σ/μ)",
                    "Quantifie la polydispersité par matériau. "
                    "Un CV élevé = diamètres très variables entre les fibres.",
                ),
                dcc.Graph(id="ms-bar-cv", style={"height": "280px"}),
            ], className="card col-6"),
            html.Div([
                chart_header(
                    "Rapport d'élancement moyen (λ = longueur / diamètre)",
                    "Grand λ = fibres longues et fines, réseau dense et interconnecté.",
                ),
                dcc.Graph(id="ms-bar-slenderness", style={"height": "280px"}),
            ], className="card col-6"),
        ], className="row"),

        # ── Conclusion ───────────────────────────────────────────────────
        conclusion_box(
            "Résultats clés — Microstructure",
            "Les 6 matériaux présentent des géométries fibreuses très distinctes : le Carbone "
            "possède les fibres les plus fines (Ø ~7 µm, absorption maximale attendue), tandis que "
            "le Chanvre présente les fibres les plus épaisses (Ø ~30 µm). Les courbes KDE montrent "
            "que le Nylon et le PET recyclé ont des distributions de diamètre plus larges, "
            "suggérant une variabilité de fabrication plus importante. La figure de pôle révèle "
            "que la plupart des matériaux ont une légère orientation préférentielle dans le plan "
            "(θ moyen > 45°), ce qui influence directement leur résistivité à l'écoulement.",
        ),

    ], className="page-content")


@callback(
    Output("ms-kpi-row", "children"),
    Output("ms-box-diameter", "figure"),
    Output("ms-box-length", "figure"),
    Input("ms-filter-material", "value"),
    Input("ms-filter-batch", "value"),
)
def update_morphology(materials, batches):
    try:
        filtered_samples = filter_samples(materials=materials or None, batches=batches or None)
        fibers = load_fibers()
        fibers = fibers[fibers["sample_id"].isin(filtered_samples["sample_id"])]
        fibers_mat = fibers.merge(
            filtered_samples[["sample_id", "material"]], on="sample_id", how="left"
        )

        if fibers.empty:
            empty = fig_utils.empty_figure("Aucune donnée pour ce filtre")
            return html.Div(), empty, empty

        disp_df = fibers_mat.merge(
            filtered_samples[["sample_id", "orientation_dispersion"]], on="sample_id", how="left"
        )

        kpis = html.Div([
            kpi_card("◎", f"{fibers['diameter_um'].mean():.2f} µm", "Diamètre moyen", color=COLORS["primary"]),
            kpi_card("↔", f"{fibers['length_um'].mean():.1f} µm", "Longueur moyenne", color=COLORS["success"]),
            kpi_card("⟳", f"{disp_df['orientation_dispersion'].mean():.1f}°", "Dispersion orientation", color=COLORS["warning"]),
            kpi_card("≡", str(len(fibers)), "Fibres analysées", color=COLORS["neutral"]),
        ], className="kpi-row")

        box_d = fig_utils.boxplot_by_group(fibers_mat, "diameter_um", "material",
                                            "Diamètre par matériau", "Diamètre (µm)")
        box_l = fig_utils.boxplot_by_group(fibers_mat, "length_um", "material",
                                            "Longueur par matériau", "Longueur (µm)")
        return kpis, box_d, box_l
    except Exception:
        empty = fig_utils.empty_figure("Données non disponibles")
        return html.Div(), empty, empty


@callback(
    Output("ms-pdf-diameter", "figure"),
    Output("ms-rose-psi", "figure"),
    Output("ms-pdf-theta", "figure"),
    Input("ms-filter-material", "value"),
    Input("ms-filter-batch", "value"),
)
def update_kde(materials, batches):
    filtered_samples = filter_samples(materials=materials or None, batches=batches or None)
    fibers = load_fibers()
    fibers = fibers[fibers["sample_id"].isin(filtered_samples["sample_id"])]
    fibers = fibers.merge(
        filtered_samples[["sample_id", "material"]], on="sample_id", how="left"
    )

    if fibers.empty:
        empty = fig_utils.empty_figure("Aucune donnée")
        return empty, empty, empty

    mats = sorted(fibers["material"].dropna().unique())
    data_d = {m: fibers[fibers["material"] == m]["diameter_um"].dropna().values for m in mats}
    data_p = {m: fibers[fibers["material"] == m]["orientation_psi"].dropna().values for m in mats}
    data_t = {m: fibers[fibers["material"] == m]["orientation_theta"].dropna().values for m in mats}

    return (
        fig_utils.pdf_overlay(data_d, xlabel="Diamètre (µm)"),
        fig_utils.rose_diagram(data_p),
        fig_utils.pdf_overlay(data_t, xlabel="Angle zénithal θ (°)"),
    )


@callback(
    Output("ms-pole-figure", "figure"),
    Input("ms-filter-material", "value"),
    Input("ms-filter-batch", "value"),
)
def update_pole_figure(materials, batches):
    filtered_samples = filter_samples(materials=materials or None, batches=batches or None)
    fibers = load_fibers()
    fibers = fibers[fibers["sample_id"].isin(filtered_samples["sample_id"])]
    fibers = fibers.merge(
        filtered_samples[["sample_id", "material"]], on="sample_id", how="left"
    )

    if fibers.empty:
        return fig_utils.empty_figure("Aucune donnée")

    if len(fibers) > 3000:
        fibers = fibers.sample(3000, random_state=42)

    return fig_utils.pole_figure_pub(
        fibers,
        theta_col="orientation_theta",
        psi_col="orientation_psi",
        color_col="material",
        size_col="length_um",
    )


@callback(
    Output("ms-scatter-lxd", "figure"),
    Output("ms-box-contacts", "figure"),
    Input("ms-filter-material", "value"),
    Input("ms-filter-batch", "value"),
)
def update_fiber_scatter(materials, batches):
    try:
        filtered_samples = filter_samples(materials=materials or None, batches=batches or None)
        fibers = load_fibers()
        fibers = fibers[fibers["sample_id"].isin(filtered_samples["sample_id"])]
        fibers_mat = fibers.merge(
            filtered_samples[["sample_id", "material"]], on="sample_id", how="left"
        )

        if fibers_mat.empty:
            empty = fig_utils.empty_figure("Aucune donnée pour ce filtre")
            return empty, empty

        plot_df = fibers_mat.dropna(subset=["diameter_um", "length_um", "material"])
        if len(plot_df) > 2000:
            plot_df = plot_df.sample(2000, random_state=42)

        scatter_fig = fig_utils.scatter(
            plot_df, "diameter_um", "length_um",
            color_col="material",
            title="Longueur × diamètre des fibres",
            xlabel="Diamètre (µm)",
            ylabel="Longueur (µm)",
        )
        contacts_fig = fig_utils.boxplot_by_group(
            fibers_mat.dropna(subset=["n_contacts", "material"]),
            "n_contacts", "material",
            "Contacts par fibre",
            "Nombre de contacts",
        )
        return scatter_fig, contacts_fig
    except Exception:
        empty = fig_utils.empty_figure("Données non disponibles")
        return empty, empty


@callback(
    Output("ms-bar-cv", "figure"),
    Output("ms-bar-slenderness", "figure"),
    Input("ms-filter-material", "value"),
    Input("ms-filter-batch", "value"),
)
def update_morphology_advanced(materials, batches):
    try:
        filtered_samples = filter_samples(materials=materials or None, batches=batches or None)
        fibers = load_fibers()
        fibers = fibers[fibers["sample_id"].isin(filtered_samples["sample_id"])]
        fibers_mat = fibers.merge(
            filtered_samples[["sample_id", "material"]], on="sample_id", how="left"
        )

        if fibers_mat.empty:
            empty = fig_utils.empty_figure("Aucune donnée pour ce filtre")
            return empty, empty

        cv_df = (
            fibers_mat.groupby("material")["diameter_um"]
            .agg(lambda s: s.std() / s.mean() if s.mean() > 0 else 0)
            .reset_index()
            .rename(columns={"diameter_um": "CV_diametre"})
        )
        bar_cv = fig_utils.bar_chart(
            cv_df, "material", "CV_diametre",
            "Coefficient de variation du diamètre",
            color_col="material",
            xlabel="Matériau", ylabel="CV = σ/μ",
        )

        fibers_sl = fibers_mat.copy()
        fibers_sl["slenderness"] = fibers_sl["length_um"] / fibers_sl["diameter_um"].clip(lower=0.1)
        sl_df = fibers_sl.groupby("material")["slenderness"].mean().reset_index()
        bar_sl = fig_utils.bar_chart(
            sl_df, "material", "slenderness",
            "Rapport d'élancement moyen",
            color_col="material",
            xlabel="Matériau", ylabel="λ = longueur/diamètre",
        )

        return bar_cv, bar_sl
    except Exception:
        empty = fig_utils.empty_figure("Données non disponibles")
        return empty, empty
