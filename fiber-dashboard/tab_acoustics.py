from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import numpy as np
from config import TABS, BASE_TAB, sel_tab, PLOT_LAYOUT, apply_grid, mat_color
from data import _has, _empty_fig
from components import graph_card, tab_banner, _absorption_card


def get_tab():
    return dcc.Tab(
        label=TABS["acoustics"]["label"],
        value="acoustics",
        style=BASE_TAB,
        selected_style=sel_tab("acoustics"),
        children=[html.Div(style={"padding": "28px 0 12px 0"}, children=[
            tab_banner(
                "acoustics",
                "Performances sonores des matériaux fibreux",
                "Ces mesures montrent combien de son chaque matériau absorbe "
                "selon la fréquence (grave, medium, aigu). "
                "L'objectif du projet est de relier ces performances aux caractéristiques "
                "des fibres (épaisseur, porosité...) pour concevoir de meilleurs matériaux "
                "sans avoir à tout mesurer en laboratoire.",
                [
                    "α (coefficient d'absorption) : de 0 (le son rebondit) à 1 (le son est totalement absorbé).",
                    "Fréquence : 250 Hz = graves, 1 000 Hz ≈ voix humaine, 4 000 Hz = aigus.",
                    "Résistivité σ : résistance au passage de l'air — une valeur intermédiaire est idéale.",
                ],
            ),
            dbc.Row(className="px-1 g-3", children=[
                _absorption_card(),
            ]),
            dbc.Row(className="px-1 g-3", children=[
                graph_card(
                    "graph-resistivity",
                    "Résistance à l'air vs quantité de vide (porosité)",
                    "Ce graphique montre tous les échantillons analysés : chaque point correspond "
                    "à un échantillon scanné. On compare leur résistance au passage de l'air (axe vertical) "
                    "à leur porosité (axe horizontal), c'est-à-dire le pourcentage de vide dans le matériau. "
                    "Un matériau très poreux laisse passer l'air facilement donc résiste peu — "
                    "un matériau dense résiste beaucoup. La ligne pointillée montre la tendance générale.",
                    "Survolez un point pour voir à quel échantillon il correspond. "
                    "Les échantillons affichés sont ceux sélectionnés via les cases en bas du graphique.",
                    height="310px", col_width=12,
                    accent=TABS["acoustics"]["bg"],
                ),
            ]),
        ])]
    )


def build_resistivity(samp_f, aco_res):
    fig_res = go.Figure()
    if not aco_res.empty and _has(aco_res, "porosity", "airflow_resistivity", "material"):
        for i, mat in enumerate(sorted(aco_res["material"].dropna().unique())):
            grp = aco_res[aco_res["material"] == mat].dropna(subset=["porosity", "airflow_resistivity"])
            if grp.empty:
                continue
            fig_res.add_trace(go.Scatter(
                x=grp["porosity"], y=grp["airflow_resistivity"],
                mode="markers", name=mat,
                marker=dict(color=mat_color(mat, i), size=12,
                            line=dict(width=1.5, color="white")),
                text=grp.get("sample_id"),
                hovertemplate=(
                    "<b>Échantillon %{text}</b><br>"
                    "Porosité : %{x:.3f}<br>"
                    "Résistivité : %{y:,.0f} Pa·s/m²"
                    "<extra></extra>"
                ),
            ))
        valid = aco_res.dropna(subset=["porosity", "airflow_resistivity"])
        if len(valid) >= 3:
            xv = valid["porosity"].values
            yv = np.log(valid["airflow_resistivity"].values + 1)
            z  = np.polyfit(xv, yv, 1)
            xl = np.linspace(xv.min(), xv.max(), 100)
            fig_res.add_trace(go.Scatter(
                x=xl, y=np.exp(np.polyval(z, xl)),
                mode="lines", name="Tendance",
                line=dict(color="#475569", width=2, dash="dash"),
                hovertemplate="Tendance → σ = %{y:,.0f} Pa·s/m²<extra></extra>",
            ))
        fig_res.update_layout(
            **PLOT_LAYOUT,
            xaxis_title="Porosité (proportion de vide)",
            yaxis_title="Résistivité σ (Pa·s/m²)",
            yaxis_type="log",
            showlegend=False,
        )
        apply_grid(fig_res)
    else:
        fig_res = _empty_fig("Colonnes 'airflow_resistivity' ou 'porosity' non disponibles")
    return fig_res
