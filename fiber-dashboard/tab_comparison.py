from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from config import TABS, BASE_TAB, sel_tab, PLOT_LAYOUT, apply_grid, mat_color
from data import FREQ_COLS, _has, _empty_fig
from components import graph_card, tab_banner


def get_tab():
    return dcc.Tab(
        label=TABS["correlations"]["label"],
        value="correlations",
        style=BASE_TAB,
        selected_style=sel_tab("correlations"),
        children=[html.Div(style={"padding": "28px 0 12px 0"}, children=[
            tab_banner(
                "correlations",
                "Quel matériau absorbe le mieux le son — et pourquoi ?",
                "Ce graphique compare directement les 6 matériaux à chaque fréquence sonore. "
                "Il permet de voir d'un coup d'œil quel matériau est le plus performant, "
                "et si c'est lié à la taille de ses fibres.",
                [
                    "Chaque groupe de barres = une fréquence sonore (250 Hz = graves, 4000 Hz = aigus).",
                    "Plus la barre est haute, plus le matériau absorbe le son à cette fréquence.",
                    "Le scatter à droite montre si les fibres fines absorbent mieux que les grosses.",
                ],
            ),
            dbc.Row(className="px-1 g-3", children=[
                graph_card(
                    "graph-ranking-bar",
                    "Absorption par matériau et par fréquence",
                    "Comparaison directe de tous les matériaux à chaque fréquence.",
                    "Plus la barre est haute = meilleure absorption.",
                    height="360px", col_width=7,
                    accent=TABS["correlations"]["bg"],
                ),
                graph_card(
                    "graph-morph-scatter",
                    "Taille des fibres vs absorption à 1 kHz",
                    "Ce graphique montre tous les échantillons acoustiques disponibles. "
                    "Chaque point représente un échantillon : sa position horizontale = "
                    "le diamètre moyen de ses fibres, sa position verticale = "
                    "son absorption à 1 kHz (fréquence de la voix humaine). "
                    "Si les points forment une tendance (courbe descendante de gauche à droite), "
                    "cela confirme que les fibres fines absorbent mieux le son.",
                    "Survolez un point pour voir le matériau et les valeurs exactes. "
                    "Si les points sont dispersés sans tendance, c'est que d'autres facteurs "
                    "(longueur, porosité) jouent aussi un rôle.",
                    height="360px", col_width=5,
                    accent=TABS["correlations"]["bg"],
                ),
            ]),
        ])]
    )


def build_ranking(aco_f):
    fig_ranking = go.Figure()
    if not aco_f.empty and FREQ_COLS and "material" in aco_f.columns:
        _freqs_labels = {
            "absorption_250hz": "250 Hz",
            "absorption_500hz": "500 Hz",
            "absorption_1000hz": "1 kHz",
            "absorption_2000hz": "2 kHz",
            "absorption_4000hz": "4 kHz",
        }
        avail = [c for c in FREQ_COLS if c in aco_f.columns]
        for i, mat in enumerate(sorted(aco_f["material"].dropna().unique())):
            grp = aco_f[aco_f["material"] == mat][avail].mean()
            fig_ranking.add_trace(go.Bar(
                name=mat,
                x=[_freqs_labels.get(c, c) for c in avail],
                y=grp.values,
                marker_color=mat_color(mat, i),
                hovertemplate=f"<b>{mat}</b><br>%{{x}} : α = %{{y:.3f}}<extra></extra>",
            ))
        fig_ranking.update_layout(
            **PLOT_LAYOUT,
            barmode="group",
            xaxis_title="Fréquence",
            yaxis_title="Coefficient d'absorption α",
            yaxis_range=[0, 1.05],
            showlegend=True,
            legend=dict(orientation="h", y=-0.2, font_size=11),
        )
        apply_grid(fig_ranking)
    else:
        fig_ranking = _empty_fig("Données acoustiques non disponibles")
    return fig_ranking


def build_scatter(aco_f):
    fig_scatter = go.Figure()
    if not aco_f.empty and _has(aco_f, "mean_diameter_um", "absorption_1000hz", "material"):
        _sc = aco_f.dropna(subset=["mean_diameter_um", "absorption_1000hz"])
        for i, mat in enumerate(sorted(_sc["material"].dropna().unique())):
            grp = _sc[_sc["material"] == mat]
            fig_scatter.add_trace(go.Scatter(
                x=grp["mean_diameter_um"], y=grp["absorption_1000hz"],
                mode="markers", name=mat,
                marker=dict(size=12, color=mat_color(mat, i), line=dict(width=1.5, color="white")),
                hovertemplate=f"<b>{mat}</b><br>Ø = %{{x:.1f}} µm<br>Absorption = %{{y:.3f}}<extra></extra>",
            ))
        fig_scatter.update_layout(
            **PLOT_LAYOUT,
            xaxis_title="Diamètre moyen des fibres (µm)",
            yaxis_title="Absorption à 1 kHz",
            yaxis_range=[0, 1.05],
            showlegend=False,
        )
        apply_grid(fig_scatter)
    else:
        fig_scatter = _empty_fig("Données non disponibles")
    return fig_scatter
