from dash import html, dcc, callback, Input, Output, dash_table

from components.kpi_card import kpi_card
from utils.data_loader import load_quality_log
from utils import figures as fig_utils
from config import COLORS, TABLE_STYLE

SEVERITY_COLORS = {
    "low": COLORS["success"],
    "medium": COLORS["warning"],
    "high": COLORS["accent"],
}

ISSUE_OPTIONS = ["artifact", "low_contrast", "incomplete_volume", "segmentation_error",
                 "oversized_object", "noise", "ok"]
SEVERITY_OPTIONS = ["low", "medium", "high"]


def layout() -> html.Div:
    return html.Div([
        html.H2("Contrôle qualité", className="page-title"),

        html.Div(id="qc-kpi-row", className="kpi-row"),

        html.Div(
            [
                html.Div([dcc.Graph(id="qc-bar-issue-type")], className="card col-6"),
                html.Div([dcc.Graph(id="qc-pie-detection")], className="card col-6"),
            ],
            className="row",
        ),

        html.Div(
            [
                html.Div([dcc.Graph(id="qc-bar-by-sample")], className="card col-12"),
            ],
            className="row",
        ),

        html.Div([
            html.Div([
                html.H4("Journal des issues", className="section-title"),
                html.Div([
                    html.Div([
                        html.Label("Type d'issue", style={"color": COLORS["text_secondary"],
                                                           "fontSize": "11px", "fontWeight": "600"}),
                        dcc.Dropdown(
                            id="qc-filter-type",
                            options=[{"label": t, "value": t} for t in ISSUE_OPTIONS],
                            multi=True, placeholder="Tous",
                            className="dash-dropdown-dark", style={"fontSize": "13px"},
                        ),
                    ], style={"flex": 1}),
                    html.Div([
                        html.Label("Sévérité", style={"color": COLORS["text_secondary"],
                                                       "fontSize": "11px", "fontWeight": "600"}),
                        dcc.Dropdown(
                            id="qc-filter-severity",
                            options=[{"label": s, "value": s} for s in SEVERITY_OPTIONS],
                            multi=True, placeholder="Toutes",
                            className="dash-dropdown-dark", style={"fontSize": "13px"},
                        ),
                    ], style={"flex": 1}),
                    html.Div([
                        html.Label("Statut résolution", style={"color": COLORS["text_secondary"],
                                                               "fontSize": "11px", "fontWeight": "600"}),
                        dcc.Dropdown(
                            id="qc-filter-resolved",
                            options=[{"label": "Résolue", "value": "true"},
                                     {"label": "Non résolue", "value": "false"}],
                            multi=True, placeholder="Tous",
                            className="dash-dropdown-dark", style={"fontSize": "13px"},
                        ),
                    ], style={"flex": 1}),
                ], style={"display": "flex", "gap": "12px", "marginBottom": "12px"}),
                html.Div(id="qc-table"),
            ], className="card col-12"),
        ], className="row"),
    ], className="page-content")


@callback(
    Output("qc-kpi-row", "children"),
    Output("qc-bar-issue-type", "figure"),
    Output("qc-pie-detection", "figure"),
    Output("qc-bar-by-sample", "figure"),
    Input("qc-kpi-row", "id"),
)
def build_quality_overview(_):
    log = load_quality_log()

    total_issues = len(log)
    resolved_pct = f"{log['resolved'].mean() * 100:.1f}%"
    high_severity = len(log[log["severity"] == "high"])
    auto_detected = f"{(log['detected_by'] == 'auto').mean() * 100:.1f}%"

    kpis = html.Div([
        kpi_card("⚠", str(total_issues), "Issues totales", color=COLORS["warning"]),
        kpi_card("✓", resolved_pct, "Résolues", color=COLORS["success"]),
        kpi_card("!", str(high_severity), "Sévérité haute", color=COLORS["accent"]),
        kpi_card("⊙", auto_detected, "Détection auto", color=COLORS["primary"]),
    ], className="kpi-row")

    issue_counts = log["issue_type"].value_counts().reset_index()
    issue_counts.columns = ["issue_type", "count"]
    bar_type = fig_utils.bar_chart(
        issue_counts, "issue_type", "count",
        title="Nombre d'issues par type",
        xlabel="Type", ylabel="Nombre",
    )

    det_counts = log["detected_by"].value_counts()
    pie_det = fig_utils.pie_chart(
        labels=det_counts.index.tolist(),
        values=det_counts.values.tolist(),
        title="Détection automatique vs manuelle",
    )

    sample_counts = log.groupby("sample_id")["log_id"].count().reset_index()
    sample_counts.columns = ["sample_id", "issue_count"]
    sample_counts = sample_counts.sort_values("issue_count", ascending=False).head(30)
    bar_sample = fig_utils.bar_chart(
        sample_counts, "sample_id", "issue_count",
        title="Issues par échantillon (top 30)",
        xlabel="Échantillon", ylabel="Nombre d'issues",
    )

    return kpis, bar_type, pie_det, bar_sample


@callback(
    Output("qc-table", "children"),
    Input("qc-filter-type", "value"),
    Input("qc-filter-severity", "value"),
    Input("qc-filter-resolved", "value"),
)
def update_quality_table(issue_types, severities, resolved_filter):
    log = load_quality_log()

    if issue_types:
        log = log[log["issue_type"].isin(issue_types)]
    if severities:
        log = log[log["severity"].isin(severities)]
    if resolved_filter:
        bool_vals = [v == "true" for v in resolved_filter]
        log = log[log["resolved"].isin(bool_vals)]

    table_cols = ["log_id", "sample_id", "issue_type", "severity",
                  "description", "detected_by", "resolved"]
    table = dash_table.DataTable(
        data=log[table_cols].to_dict("records"),
        columns=[{"name": c, "id": c} for c in table_cols],
        page_size=15,
        sort_action="native",
        filter_action="native",
        style_data_conditional=TABLE_STYLE["style_data_conditional"] + [
            {"if": {"filter_query": '{severity} = "high"'},
             "color": COLORS["accent"]},
            {"if": {"filter_query": '{severity} = "medium"'},
             "color": COLORS["warning"]},
            {"if": {"filter_query": '{resolved} = "True"'},
             "backgroundColor": "rgba(46,204,113,0.05)"},
        ],
        **{k: v for k, v in TABLE_STYLE.items() if k != "style_data_conditional"},
    )
    return table
