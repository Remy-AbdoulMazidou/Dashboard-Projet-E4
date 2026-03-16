from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from config import TABS, BASE_TAB, sel_tab, PLOT_LAYOUT, mat_color
from data import MATERIALS, _has, _empty_fig
from components import graph_card, tab_banner, kpi_card


def get_tab():
    return dcc.Tab(
        label=TABS["overview"]["label"],
        value="overview",
        style=BASE_TAB,
        selected_style=sel_tab("overview"),
        children=[html.Div(style={"padding": "28px 0 12px 0"}, children=[
            tab_banner(
                "overview",
                "Résumé des données analysées",
                "Cette page donne un aperçu rapide de tout ce que le scanner 3D a mesuré "
                "pour les matériaux sélectionnés. C'est le point de départ idéal avant "
                "d'explorer les détails dans les autres onglets.",
                [
                    "Échantillons : morceaux de matériau numérisés en 3D par le scanner.",
                    "Fibres : chaque fil individuel détecté à l'intérieur du matériau.",
                    "Contacts : points où deux fibres se touchent et forment une liaison.",
                    "Porosité : part de vide dans le matériau — plus c'est élevé, plus il y a d'air à l'intérieur.",
                ],
            ),
            dbc.Row(id="row-kpis", className="px-1"),
            dbc.Row(className="px-1 mt-4", children=[
                graph_card(
                    "graph-summary-table",
                    "Résumé des matériaux analysés",
                    "Tableau récapitulatif des mesures clés par matériau.",
                    "Chaque ligne = un matériau. Survolez pour les détails.",
                    height="260px", col_width=12,
                    accent=TABS["overview"]["bg"],
                ),
            ]),
        ])]
    )


def build_kpis(samp_f, fib_f, aco_f):
    n_samples  = len(samp_f)
    n_fibers   = len(fib_f)
    mean_por   = samp_f["porosity"].mean() if _has(samp_f, "porosity") and n_samples else None
    return [
        kpi_card("Échantillons analysés", str(n_samples),
                 "Volumes 3D numérisés par microtomographie X", "#1D4ED8"),
        kpi_card("Fibres détectées", f"{n_fibers:,}",
                 "Fibres individuelles segmentées dans les volumes 3D", "#6D28D9"),
        kpi_card("Porosité moyenne",
                 f"{mean_por:.3f}" if mean_por is not None else "—",
                 "Fraction de vide dans le matériau (0 = plein, 1 = creux)", "#B45309"),
    ]


def build_summary_table(samp_f, aco_f):
    fig_summary = go.Figure()
    if not samp_f.empty:
        _s = samp_f[["material"] + [c for c in ["mean_diameter_um", "mean_length_um", "porosity", "orientation_dispersion"] if c in samp_f.columns]].groupby("material").mean().round(2).reset_index()
        _a_cols = [c for c in ["absorption_1000hz", "airflow_resistivity"] if c in aco_f.columns]
        if _a_cols and not aco_f.empty:
            _a = aco_f[["material"] + _a_cols].groupby("material").mean().round(3).reset_index()
            _t = _s.merge(_a, on="material", how="left")
        else:
            _t = _s
        col_labels = {
            "material": "Matériau",
            "mean_diameter_um": "Ø moyen (µm)",
            "mean_length_um": "Longueur moy. (µm)",
            "porosity": "Porosité",
            "orientation_dispersion": "Orient. (°)",
            "absorption_1000hz": "Absorption 1 kHz",
            "airflow_resistivity": "Résistivité σ",
        }
        ordered = [c for c in col_labels if c in _t.columns]
        fig_summary.add_trace(go.Table(
            header=dict(
                values=[f"<b>{col_labels[c]}</b>" for c in ordered],
                fill_color=TABS["overview"]["bg"],
                font=dict(color="white", size=12),
                align="center", height=36,
                line=dict(color="white", width=1),
            ),
            cells=dict(
                values=[_t[c].tolist() for c in ordered],
                fill_color=[["#EFF6FF" if i % 2 == 0 else "white"] * len(_t) for i in range(len(ordered))],
                font=dict(color="#334155", size=11),
                align="center", height=30,
                line=dict(color="#E2E8F0", width=1),
            ),
        ))
        fig_summary.update_layout(
            paper_bgcolor="white",
            plot_bgcolor="white",
            margin=dict(l=10, r=10, t=10, b=10),
        )
    else:
        fig_summary = _empty_fig("Données insuffisantes")
    return fig_summary
