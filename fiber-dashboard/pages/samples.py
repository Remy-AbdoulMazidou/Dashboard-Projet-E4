from dash import html, dcc, callback, Input, Output, dash_table
import pandas as pd

from components.filters import sample_selector
from utils.data_loader import load_samples, load_fibers
from utils import figures as fig_utils
from config import COLORS, TABLE_STYLE


def layout() -> html.Div:
    samples = load_samples()
    sample_ids = samples["sample_id"].tolist()

    return html.Div([
        html.H2("Visualisation des échantillons", className="page-title"),
        html.Div([
            sample_selector("sp-sample-select", sample_ids),
        ], className="filter-bar"),

        html.Div(id="sp-sample-card", className="card col-12"),

        html.Div([
            html.Div([
                html.Div(
                    "Visualisation µ-CT",
                    style={"fontWeight": "600", "fontSize": "12px",
                           "color": "#64748B", "marginBottom": "8px"},
                ),
                html.Div([
                    html.Span("🔬", style={"fontSize": "28px", "display": "block",
                                           "textAlign": "center", "marginBottom": "8px"}),
                    html.Div(
                        "Images µ-CT brutes, segmentées et overlays à intégrer depuis "
                        "le répertoire assets/images/. Nommez les fichiers "
                        "{sample_id}_raw.png, {sample_id}_seg.png, {sample_id}_overlay.png.",
                        style={"fontSize": "12px", "color": "#94A3B8",
                               "textAlign": "center", "lineHeight": "1.5"},
                    ),
                ], style={
                    "border": "2px dashed #E2E8F0",
                    "borderRadius": "8px",
                    "padding": "24px 16px",
                    "background": "#F8FAFC",
                }),
            ], className="card col-12"),
        ], className="row"),

        html.Div(
            [
                html.Div([dcc.Graph(id="sp-hist-diameter")], className="card col-6"),
                html.Div([dcc.Graph(id="sp-hist-length")], className="card col-6"),
            ],
            className="row",
        ),

        html.Div([
            html.Div([
                html.H4("Fibres de cet échantillon", className="section-title"),
                html.Div(id="sp-fiber-table"),
            ], className="card col-12"),
        ], className="row"),
    ], className="page-content")


@callback(
    Output("sp-sample-card", "children"),
    Output("sp-hist-diameter", "figure"),
    Output("sp-hist-length", "figure"),
    Output("sp-fiber-table", "children"),
    Input("sp-sample-select", "value"),
)
def update_sample_view(sample_id):
    if not sample_id:
        empty = fig_utils.empty_figure()
        return html.Div("Sélectionnez un échantillon"), empty, empty, html.Div()

    samples = load_samples()
    fibers = load_fibers()

    row = samples[samples["sample_id"] == sample_id].iloc[0]
    sample_fibers = fibers[fibers["sample_id"] == sample_id]

    info_items = [
        ("Matériau", row["material"]),
        ("Lot", row["batch"]),
        ("Résolution", f"{row['resolution_um']} µm"),
        ("Voxel", f"{row['voxel_size']} µm"),
        ("Volume", f"{row['volume_mm3']} mm³"),
        ("Porosité", f"{row['porosity']:.3f}"),
        ("Fibres détectées", str(int(row["fiber_count"]))),
        ("Contacts", str(int(row["contact_count"]))),
        ("Seuil misorientation", f"{row['misorientation_threshold']}°"),
        ("Directions", str(int(row["n_directions"]))),
        ("Dilatation", row["dilation_type"]),
        ("Score qualité", f"{row['quality_score']} / 5"),
        ("Statut", row["status"]),
        ("Date", str(row["processing_date"])[:10] if row["processing_date"] else "—"),
    ]

    card = html.Div([
        html.H4(f"Fiche — {sample_id}", className="section-title"),
        html.Div(
            [
                html.Div([
                    html.Span(label + " : ", style={"color": COLORS["text_secondary"], "fontSize": "12px"}),
                    html.Span(value, style={"color": COLORS["text_primary"], "fontWeight": "600", "fontSize": "13px"}),
                ], style={"padding": "4px 12px"})
                for label, value in info_items
            ],
            style={"display": "grid", "gridTemplateColumns": "repeat(4, 1fr)", "gap": "4px"},
        ),
        html.Div(
            f"Notes : {row['notes']}" if (row.get("notes") and not pd.isna(row.get("notes", ""))) else "",
            style={"color": COLORS["text_secondary"], "fontSize": "12px",
                   "marginTop": "10px", "fontStyle": "italic"},
        ),
    ])

    if sample_fibers.empty:
        hist_d = fig_utils.empty_figure("Aucune fibre pour cet échantillon")
        hist_l = fig_utils.empty_figure("Aucune fibre pour cet échantillon")
    else:
        hist_d = fig_utils.histogram(sample_fibers, "diameter_um",
                                      "Distribution des diamètres", "Diamètre (µm)",
                                      color=COLORS["primary"])
        hist_l = fig_utils.histogram(sample_fibers, "length_um",
                                      "Distribution des longueurs", "Longueur (µm)",
                                      color=COLORS["success"])

    table_cols = ["fiber_id", "diameter_um", "length_um", "orientation_theta",
                  "orientation_psi", "curvature", "n_contacts"]
    table_data = sample_fibers[table_cols].round(3).to_dict("records")
    fiber_table = dash_table.DataTable(
        data=table_data,
        columns=[{"name": c, "id": c} for c in table_cols],
        page_size=15,
        sort_action="native",
        filter_action="native",
        **TABLE_STYLE,
    )

    return card, hist_d, hist_l, fiber_table
