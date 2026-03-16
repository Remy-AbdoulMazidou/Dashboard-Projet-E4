from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import numpy as np
from scipy.stats import gaussian_kde
from config import TABS, BASE_TAB, sel_tab, PLOT_LAYOUT, apply_grid, mat_color
from data import MATERIALS, _has, _empty_fig, _boxplot
from components import graph_card, tab_banner


def get_tab():
    return dcc.Tab(
        label=TABS["morphology"]["label"],
        value="morphology",
        style=BASE_TAB,
        selected_style=sel_tab("morphology"),
        children=[html.Div(style={"padding": "28px 0 12px 0"}, children=[
            tab_banner(
                "morphology",
                "Forme et taille des fibres dans le matériau",
                "Le scanner 3D mesure chaque fibre une par une : son épaisseur, sa longueur, "
                "son angle par rapport au plan du matériau et sa courbure. "
                "Ces mesures permettent de comprendre pourquoi certains matériaux "
                "absorbent mieux le son que d'autres.",
                [
                    "Diamètre : l'épaisseur d'une fibre. Des fibres fines = réseau plus serré = meilleure absorption.",
                    "Longueur : la longueur d'une fibre. Des fibres longues créent plus de liaisons.",
                    "Orientation θ : l'angle d'inclinaison d'une fibre (0° = à plat, 90° = vertical).",
                    "Courbure : à quel point une fibre est ondulée (0 = droite, élevé = très ondulée).",
                ],
            ),
            dbc.Row(className="px-1 g-3", children=[
                graph_card(
                    "graph-diameter",
                    "Épaisseur des fibres par matériau (µm)",
                    "Épaisseur des fibres par matériau.",
                    "La barre centrale = diamètre le plus fréquent. La boîte = 50 % des fibres.",
                    col_width=12,
                    accent=TABS["morphology"]["bg"],
                ),
            ]),
            dbc.Row(className="px-1 g-3", children=[
                graph_card(
                    "graph-diameter-kde",
                    "Distribution des diamètres de fibres (densité de probabilité)",
                    "Distribution des tailles de fibres — inspiré de Tran et al. (2024).",
                    "Un pic étroit = fibres homogènes. Pic large = tailles très variées.",
                    height="280px", col_width=12,
                    accent=TABS["morphology"]["bg"],
                ),
            ]),
        ])]
    )


def build_diameter(fib_f):
    return _boxplot(fib_f, "diameter_um", "Épaisseur (µm)", "µm")


def build_kde(fib_kde):
    fig_kde = go.Figure()
    if not fib_kde.empty and _has(fib_kde, "diameter_um", "material"):
        for i, mat in enumerate(sorted(fib_kde["material"].dropna().unique())):
            vals = fib_kde[fib_kde["material"] == mat]["diameter_um"].dropna()
            if vals.empty:
                continue
            fig_kde.add_trace(go.Histogram(
                x=vals, name=mat,
                marker_color=mat_color(mat, i),
                marker_line=dict(color="white", width=0.6),
                opacity=0.60, nbinsx=30, histnorm="probability density",
                hovertemplate=f"<b>{mat}</b><br>Ø ≈ %{{x:.1f}} µm<br>Densité = %{{y:.5f}}<extra></extra>",
            ))
        fig_kde.update_layout(
            **PLOT_LAYOUT,
            barmode="overlay",
            xaxis_title="Diamètre de fibre (µm)",
            yaxis_title="Densité de probabilité",
            showlegend=False,
        )
        apply_grid(fig_kde)
    else:
        fig_kde = _empty_fig("Colonne 'diameter_um' non disponible")
    return fig_kde


def build_polar(fib_polar):
    fig_polar = go.Figure()
    if not fib_polar.empty and _has(fib_polar, "orientation_theta", "orientation_psi", "material"):
        for i, mat in enumerate(sorted(fib_polar["material"].dropna().unique())):
            grp = fib_polar[fib_polar["material"] == mat][["orientation_theta", "orientation_psi"]].dropna()
            if grp.empty:
                continue
            sample_size = min(500, len(grp))
            grp = grp.sample(sample_size, random_state=42)
            fig_polar.add_trace(go.Scatterpolar(
                r=grp["orientation_theta"],
                theta=grp["orientation_psi"],
                mode="markers",
                name=mat,
                marker=dict(color=mat_color(mat, i), size=4, opacity=0.4),
                hovertemplate=f"<b>{mat}</b><br>θ = %{{r:.1f}}°<br>ψ = %{{theta:.1f}}°<extra></extra>",
            ))
        fig_polar.update_layout(
            paper_bgcolor="white",
            font=dict(family="Inter, system-ui, sans-serif", size=11, color="#334155"),
            polar=dict(
                radialaxis=dict(
                    visible=True, range=[0, 90],
                    tickfont=dict(size=9, color="#64748B"),
                    gridcolor="#CBD5E1", linecolor="#CBD5E1",
                    title=dict(text="θ (°)", font=dict(size=10)),
                ),
                angularaxis=dict(
                    tickfont=dict(size=10, color="#334155"),
                    linecolor="#CBD5E1",
                    direction="counterclockwise",
                ),
                bgcolor="#F8FAFC",
            ),
            showlegend=False,
            margin=dict(l=60, r=60, t=40, b=40),
            hoverlabel=dict(bgcolor="#1E293B", bordercolor="#0F172A", font_size=12, font_color="white"),
        )
    else:
        fig_polar = _empty_fig("Colonnes 'orientation_theta' / 'orientation_psi' non disponibles")
    return fig_polar
