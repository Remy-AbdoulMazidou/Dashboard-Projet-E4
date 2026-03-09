from dash import html, dcc, callback, Input, Output

from components.filters import material_filter, batch_filter, filter_bar
from components.kpi_card import kpi_card
from components.info_box import info_box, guide_box, warn_box, chart_header
from utils.data_loader import load_fibers, filter_samples
from utils import figures as fig_utils
from config import COLORS


def layout() -> html.Div:
    return html.Div([
        html.H2("Descripteurs microstructuraux", className="page-title"),
        html.P(
            "Analyse morphologique des fibres extraites par segmentation µ-CT : "
            "taille, forme, orientation et contacts entre fibres.",
            className="page-subtitle",
        ),

        # ── Section 1 : Vue générale ─────────────────────────────────────────
        filter_bar(
            material_filter("ms-filter-material"),
            batch_filter("ms-filter-batch"),
        ),
        info_box(
            "Les indicateurs ci-dessous décrivent la géométrie moyenne des fibres "
            "pour les échantillons sélectionnés. La dispersion d'orientation mesure "
            "l'uniformité directionnelle (0° = toutes parallèles, 90° = aléatoire)."
        ),
        html.Div(id="ms-kpi-row", className="kpi-row"),

        html.Div([
            html.Div([
                chart_header(
                    "Distribution des diamètres",
                    "Histogramme du diamètre de toutes les fibres. Un pic étroit indique "
                    "une fabrication homogène. Un pic large ou bimodal signale plusieurs populations de fibres.",
                ),
                dcc.Graph(id="ms-hist-diameter"),
            ], className="card col-6"),
            html.Div([
                chart_header(
                    "Distribution des longueurs",
                    "Histogramme des longueurs de fibres. Des fibres très longues augmentent "
                    "l'interconnexion du réseau et influencent la résistivité à l'écoulement.",
                ),
                dcc.Graph(id="ms-hist-length"),
            ], className="card col-6"),
        ], className="row"),

        html.Div([
            html.Div([
                chart_header(
                    "Diamètres par matériau",
                    "Boîtes à moustaches : la ligne centrale = médiane, la boîte = 50 % des valeurs, "
                    "les moustaches = valeurs extrêmes. Comparez la dispersion entre matériaux.",
                ),
                dcc.Graph(id="ms-box-diameter"),
            ], className="card col-6"),
            html.Div([
                chart_header(
                    "Longueurs par matériau",
                    "Même lecture que pour les diamètres. Un matériau avec une grande dispersion "
                    "de longueurs peut produire des propriétés acoustiques moins prévisibles.",
                ),
                dcc.Graph(id="ms-box-length"),
            ], className="card col-6"),
        ], className="row"),

        html.Div([
            html.Div([
                chart_header(
                    "Contacts moyens par fibre et par matériau",
                    "Nombre moyen de points de contact entre fibres voisines. "
                    "Un nombre élevé indique un réseau dense et interconnecté, "
                    "ce qui influence la perméabilité thermique et l'absorption acoustique.",
                ),
                dcc.Graph(id="ms-bar-contacts"),
            ], className="card col-12"),
        ], className="row"),

        # ── Section 2 : Distributions PDF ───────────────────────────────────
        html.H3("Distributions de probabilité — style publication", className="section-separator"),
        info_box(
            "Les courbes KDE (Kernel Density Estimation) montrent la distribution de probabilité "
            "continue d'un descripteur pour chaque matériau. Contrairement à un histogramme, "
            "la courbe est lissée et permet une meilleure comparaison entre groupes. "
            "Les lignes pointillées verticales indiquent la moyenne de chaque groupe."
        ),
        guide_box("Comment interpréter une courbe KDE ?", [
            "Un pic étroit et haut = fibres très uniformes pour ce descripteur.",
            "Un pic large et plat = forte variabilité (moins contrôlé).",
            "Deux pics (distribution bimodale) = deux populations distinctes coexistent.",
            "Décalage entre matériaux = différence structurelle significative.",
        ]),
        html.Div([
            html.Div([
                chart_header("PDF — Diamètre (µm)", "Distribution de probabilité du diamètre par matériau."),
                dcc.Graph(id="ms-pdf-diameter"),
            ], className="card col-4"),
            html.Div([
                chart_header("PDF — Angle azimutal ψ", "Orientation dans le plan de l'image (0–180°)."),
                dcc.Graph(id="ms-pdf-psi"),
            ], className="card col-4"),
            html.Div([
                chart_header("PDF — Angle zénithal θ", "Inclinaison hors plan (0° = perpendiculaire, 90° = in-plane)."),
                dcc.Graph(id="ms-pdf-theta"),
            ], className="card col-4"),
        ], className="row"),

        # ── Section 3 : Pole figure ─────────────────────────────────────────
        html.H3("Pole figure — projection stéréographique", className="section-separator"),
        info_box(
            "La figure de pôle représente l'orientation 3D de chaque fibre. "
            "Le centre du cercle correspond aux fibres perpendiculaires au plan d'imagerie (θ = 0°), "
            "le bord du cercle aux fibres dans le plan (θ = 90°). "
            "L'angle azimutal ψ indique la direction dans le plan.",
        ),
        guide_box("Comment lire la figure de pôle ?", [
            "Concentration au centre → fibres principalement perpendiculaires au plan (orientation préférentielle).",
            "Concentration à la périphérie → fibres couchées dans le plan (matériau en couches).",
            "Distribution uniforme → réseau isotrope (aucune orientation privilégiée).",
            "Taille des points proportionnelle à la longueur de la fibre.",
        ]),
        html.Div([
            html.Div([
                dcc.Graph(id="ms-pole-figure"),
            ], className="card col-12"),
        ], className="row"),

    ], className="page-content")


@callback(
    Output("ms-kpi-row", "children"),
    Output("ms-hist-diameter", "figure"),
    Output("ms-hist-length", "figure"),
    Output("ms-box-diameter", "figure"),
    Output("ms-box-length", "figure"),
    Output("ms-bar-contacts", "figure"),
    Input("ms-filter-material", "value"),
    Input("ms-filter-batch", "value"),
)
def update_overview(materials, batches):
    filtered_samples = filter_samples(materials=materials or None, batches=batches or None)
    fibers = load_fibers()
    fibers = fibers[fibers["sample_id"].isin(filtered_samples["sample_id"])]
    fibers_with_material = fibers.merge(
        filtered_samples[["sample_id", "material"]], on="sample_id", how="left"
    )

    if fibers.empty:
        empty = fig_utils.empty_figure("Aucune donnée pour ce filtre")
        return html.Div(), empty, empty, empty, empty, empty

    disp_df = fibers_with_material.merge(
        filtered_samples[["sample_id", "orientation_dispersion"]], on="sample_id", how="left"
    )
    kpis = html.Div([
        kpi_card("◎", f"{fibers['diameter_um'].mean():.2f} µm", "Diamètre moyen", color=COLORS["primary"]),
        kpi_card("↔", f"{fibers['length_um'].mean():.1f} µm", "Longueur moyenne", color=COLORS["success"]),
        kpi_card("⟳", f"{disp_df['orientation_dispersion'].mean():.1f}°", "Dispersion orientation", color=COLORS["warning"]),
        kpi_card("≡", str(len(fibers)), "Fibres analysées", color=COLORS["neutral"]),
    ], className="kpi-row")

    hist_d = fig_utils.histogram(fibers, "diameter_um", "Distribution des diamètres",
                                  "Diamètre (µm)", color=COLORS["primary"])
    hist_l = fig_utils.histogram(fibers, "length_um", "Distribution des longueurs",
                                  "Longueur (µm)", color=COLORS["success"])
    box_d = fig_utils.boxplot_by_group(fibers_with_material, "diameter_um", "material",
                                        "Diamètres par matériau", "Diamètre (µm)")
    box_l = fig_utils.boxplot_by_group(fibers_with_material, "length_um", "material",
                                        "Longueurs par matériau", "Longueur (µm)")
    contacts_by_material = (
        fibers_with_material.groupby("material")["n_contacts"]
        .mean().reset_index()
        .rename(columns={"n_contacts": "mean_contacts"})
    )
    bar_contacts = fig_utils.bar_chart(
        contacts_by_material, "material", "mean_contacts",
        "Contacts moyens par fibre et par matériau",
        color_col="material", xlabel="Matériau", ylabel="Contacts moyens / fibre",
    )
    return kpis, hist_d, hist_l, box_d, box_l, bar_contacts


@callback(
    Output("ms-pdf-diameter", "figure"),
    Output("ms-pdf-psi", "figure"),
    Output("ms-pdf-theta", "figure"),
    Input("ms-filter-material", "value"),
    Input("ms-filter-batch", "value"),
)
def update_pdf_distributions(materials, batches):
    filtered_samples = filter_samples(materials=materials or None, batches=batches or None)
    fibers = load_fibers()
    fibers = fibers[fibers["sample_id"].isin(filtered_samples["sample_id"])]
    fibers = fibers.merge(
        filtered_samples[["sample_id", "material"]], on="sample_id", how="left"
    )

    if fibers.empty:
        empty = fig_utils.empty_figure("Aucune donnée")
        return empty, empty, empty

    material_groups = sorted(fibers["material"].dropna().unique())

    data_diameter = {m: fibers[fibers["material"] == m]["diameter_um"].dropna().values
                     for m in material_groups}
    data_psi = {m: fibers[fibers["material"] == m]["orientation_psi"].dropna().values
                for m in material_groups}
    data_theta = {m: fibers[fibers["material"] == m]["orientation_theta"].dropna().values
                  for m in material_groups}

    return (
        fig_utils.pdf_overlay(data_diameter, xlabel="Diamètre (µm)"),
        fig_utils.pdf_overlay(data_psi, xlabel="Angle azimutal ψ (°)"),
        fig_utils.pdf_overlay(data_theta, xlabel="Angle zénithal θ (°)"),
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


