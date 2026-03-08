from dash import html, dcc, callback, Input, Output, dash_table
import pandas as pd

from components.kpi_card import kpi_card
from components.filters import material_filter, batch_filter, status_filter, filter_bar
from components.info_box import info_box, guide_box, chart_header
from utils.data_loader import load_samples
from utils.stats import format_large_number
from utils import figures as fig_utils
from config import COLORS, TABLE_STYLE


def layout() -> html.Div:
    return html.Div([
        html.H2("Vue d'ensemble", className="page-title"),

        html.P(
            "Résumé statistique de tous les échantillons analysés par tomographie µ-CT. "
            "Utilisez les filtres ci-dessous pour restreindre l'analyse à un matériau, "
            "un lot ou un statut de traitement particulier.",
            className="page-subtitle",
        ),

        filter_bar(
            material_filter("ov-filter-material"),
            batch_filter("ov-filter-batch"),
            status_filter("ov-filter-status"),
        ),

        # KPI section
        info_box(
            "Les indicateurs clés (KPI) résument en un coup d'œil l'état de la base de données. "
            "Ils se mettent à jour automatiquement selon les filtres sélectionnés.",
        ),
        html.Div(id="ov-kpi-row", className="kpi-row"),

        # Charts row
        html.Div([
            html.Div([
                chart_header(
                    "Fibres détectées par matériau",
                    "Compare le volume de fibres segmentées pour chaque type de matériau. "
                    "Un nombre élevé peut indiquer une densité fibreuse plus grande ou un plus grand volume scanné.",
                ),
                dcc.Graph(id="ov-bar-material"),
            ], className="card col-6"),
            html.Div([
                chart_header(
                    "Répartition des statuts de traitement",
                    "Indique combien d'échantillons sont traités (✓), en cours ou en erreur. "
                    "Idéalement, la majorité doit être en statut 'completed'.",
                ),
                dcc.Graph(id="ov-pie-status"),
            ], className="card col-6"),
        ], className="row"),

        guide_box("Comment lire ces graphiques ?", [
            "Barres : hauteur = nombre total de fibres. Comparez entre matériaux pour identifier les différences de densité.",
            "Camembert : chaque portion = proportion d'échantillons dans cet état. Un taux élevé d'erreurs signale un problème de traitement.",
        ]),

        # Timeline
        html.Div([
            html.Div([
                chart_header(
                    "Avancement des traitements dans le temps",
                    "Montre le nombre d'échantillons traités par date. Utile pour suivre la progression des expériences en cours.",
                ),
                dcc.Graph(id="ov-timeline"),
            ], className="card col-12"),
        ], className="row"),

        # Table
        html.Div([
            html.Div([
                chart_header(
                    "Tableau récapitulatif des échantillons",
                    "Toutes les métadonnées par échantillon. Cliquez sur les en-têtes pour trier, "
                    "utilisez la barre de recherche pour filtrer.",
                ),
                html.Div(id="ov-table"),
            ], className="card col-12"),
        ], className="row"),

    ], className="page-content")


@callback(
    Output("ov-kpi-row", "children"),
    Output("ov-bar-material", "figure"),
    Output("ov-pie-status", "figure"),
    Output("ov-timeline", "figure"),
    Output("ov-table", "children"),
    Input("ov-filter-material", "value"),
    Input("ov-filter-batch", "value"),
    Input("ov-filter-status", "value"),
)
def update_overview(materials, batches, statuses):
    from utils.data_loader import filter_samples, load_fibers, load_contacts

    df = filter_samples(
        materials=materials or None,
        batches=batches or None,
        statuses=statuses or None,
    )

    all_fibers = load_fibers()
    all_contacts = load_contacts()

    n_samples = len(df)
    total_fibers = format_large_number(all_fibers[all_fibers["sample_id"].isin(df["sample_id"])]["fiber_id"].count())
    total_contacts = format_large_number(all_contacts[all_contacts["sample_id"].isin(df["sample_id"])].shape[0])
    mean_porosity = f"{df['porosity'].mean():.3f}" if not df.empty else "—"
    total_runtime = format_large_number(df["runtime_sec"].sum()) + " s" if not df.empty else "—"
    mean_quality = f"{df['quality_score'].mean():.1f} / 5" if not df.empty else "—"

    kpis = html.Div([
        kpi_card("📦", str(n_samples), "Échantillons analysés", color=COLORS["primary"]),
        kpi_card("🧵", total_fibers, "Fibres détectées", color=COLORS["success"]),
        kpi_card("🔗", total_contacts, "Contacts identifiés", color=COLORS["warning"]),
        kpi_card("💧", mean_porosity, "Porosité moyenne (0–1)", color=COLORS["neutral"]),
        kpi_card("⏱", total_runtime, "Temps calcul total", color=COLORS["accent"]),
        kpi_card("⭐", mean_quality, "Score qualité moyen /5", color=COLORS["primary"]),
    ], className="kpi-row")

    fibers_by_material = df.groupby("material")["fiber_count"].sum().reset_index()
    bar_mat = fig_utils.bar_chart(
        fibers_by_material, "material", "fiber_count",
        "Fibres détectées par matériau", color_col="material",
        xlabel="Matériau", ylabel="Nombre de fibres",
    )

    status_counts = df["status"].value_counts().reset_index()
    status_counts.columns = ["status", "count"]
    pie_status = fig_utils.pie_chart(
        labels=status_counts["status"].tolist(),
        values=status_counts["count"].tolist(),
        title="Répartition des statuts",
    )

    if not df.empty and "processing_date" in df.columns:
        timeline_df = df.dropna(subset=["processing_date"]).copy()
        timeline_df["processing_date"] = pd.to_datetime(timeline_df["processing_date"])
        timeline_df = timeline_df.sort_values("processing_date")
        daily = timeline_df.groupby(["processing_date", "status"]).size().reset_index(name="count")
        timeline = fig_utils.bar_chart(
            daily, "processing_date", "count",
            "Avancement des traitements par date",
            color_col="status",
            xlabel="Date", ylabel="Échantillons traités",
        )
    else:
        timeline = fig_utils.empty_figure("Pas de données de date disponibles")

    table_cols = ["sample_id", "material", "batch", "fiber_count", "porosity",
                  "mean_diameter_um", "quality_score", "status"]
    table_data = df[table_cols].to_dict("records")
    table = dash_table.DataTable(
        data=table_data,
        columns=[{"name": c, "id": c} for c in table_cols],
        page_size=12,
        sort_action="native",
        filter_action="native",
        **TABLE_STYLE,
    )

    return kpis, bar_mat, pie_status, timeline, table
