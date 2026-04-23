from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from scipy.stats import gaussian_kde
from config import TABS, BASE_TAB, sel_tab, PLOT_LAYOUT, AXIS_STYLE, apply_grid, mat_color
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
                "Ces mesures permettent de comprendre pourquoi certains matériaux absorbent mieux le son que d'autres. "
                "Références : Tran et al. (2024), Tableau 2 et Figure 3 ; Depriester et al. (2022), Fig. 7B et 18B.",
                [
                    "Diamètre : l'épaisseur d'une fibre. Des fibres fines = réseau plus serré = meilleure absorption.",
                    "Longueur : la longueur d'une fibre. Des fibres longues créent plus de liaisons.",
                    "Angle zénithal θ : inclinaison de la fibre (0° = à plat, 90° = vertical).",
                    "Angle azimutal ψ : direction de la fibre dans le plan horizontal (0° à 360°).",
                    "Figure de pôle : représentation 3D complète de l'orientation — identique à Depriester et al. (2022).",
                ],
            ),

            # Boxplot diamètre
            dbc.Row(className="px-1 g-3", children=[
                graph_card(
                    "graph-diameter",
                    "Épaisseur des fibres par matériau (µm)",
                    "Épaisseur des fibres par matériau — référence : Tran et al. (2024), Tableau 2.",
                    "La barre centrale = diamètre médian. La boîte = 50 % des fibres. "
                    "Les traits = plage habituelle (hors valeurs extrêmes).",
                    col_width=12,
                    accent=TABS["morphology"]["bg"],
                ),
            ]),

            # KDE diamètre
            dbc.Row(className="px-1 g-3", children=[
                graph_card(
                    "graph-diameter-kde",
                    "Distribution des diamètres de fibres (densité de probabilité)",
                    "Distribution des tailles de fibres — inspiré de Tran et al. (2024), Figure 3. "
                    "Chaque courbe montre à quelle taille les fibres se concentrent.",
                    "Un pic étroit = fibres homogènes en taille. Un pic large = tailles très variées.",
                    height="280px", col_width=12,
                    accent=TABS["morphology"]["bg"],
                ),
            ]),

            # Figure de pôle + distribution des angles
            dbc.Row(className="px-1 g-3", children=[
                graph_card(
                    "graph-polar",
                    "Figure de pôle — Orientation 3D des fibres",
                    "Représentation polaire de l'orientation des fibres dans l'espace 3D. "
                    "Chaque point = une fibre. L'angle radial = θ (inclinaison / angle zénithal). "
                    "L'angle angulaire = ψ (direction / angle azimutal). "
                    "Inspiré de Depriester et al. (2022), Fig. 7B et 18B.",
                    "Un nuage centré vers le bord = fibres à plat (θ proche de 90°). "
                    "Nuage au centre = fibres verticales (θ proche de 0°). "
                    "Nuage dispersé sur tout le cercle = orientations aléatoires.",
                    height="390px", col_width=6,
                    accent=TABS["morphology"]["bg"],
                ),
                graph_card(
                    "graph-angles",
                    "Distribution des angles θ (zénithal) et ψ (azimutal)",
                    "Histogrammes des angles d'orientation des fibres — "
                    "référence : Tran et al. (2024), Figure 3 et Tableau 2.",
                    "Gauche — θ : 0° = fibre verticale, 90° = fibre à plat dans le plan. "
                    "Droite — ψ : direction dans le plan horizontal (0° à 180°). "
                    "Une distribution uniforme de ψ = pas de direction préférentielle.",
                    height="390px", col_width=6,
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
    """Figure de pôle — Depriester et al. (2022) Fig. 7B / 18B."""
    fig_polar = go.Figure()
    if not fib_polar.empty and _has(fib_polar, "orientation_theta", "orientation_psi", "material"):
        for i, mat in enumerate(sorted(fib_polar["material"].dropna().unique())):
            grp = fib_polar[fib_polar["material"] == mat][
                ["orientation_theta", "orientation_psi"]
            ].dropna()
            if grp.empty:
                continue
            sample_size = min(500, len(grp))
            grp = grp.sample(sample_size, random_state=42)
            fig_polar.add_trace(go.Scatterpolar(
                r=grp["orientation_theta"],
                theta=grp["orientation_psi"],
                mode="markers",
                name=mat,
                marker=dict(color=mat_color(mat, i), size=4, opacity=0.45),
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
                    title=dict(text="θ (°)", font=dict(size=10, color="#334155")),
                ),
                angularaxis=dict(
                    tickfont=dict(size=10, color="#334155"),
                    linecolor="#CBD5E1",
                    direction="counterclockwise",
                ),
                bgcolor="#F8FAFC",
            ),
            showlegend=True,
            legend=dict(
                orientation="h", y=-0.14, x=0.5, xanchor="center",
                font=dict(size=10, color="#334155"),
                bgcolor="rgba(248,250,252,0.9)", bordercolor="#CBD5E1", borderwidth=1,
            ),
            margin=dict(l=60, r=60, t=30, b=70),
            hoverlabel=dict(bgcolor="#1E293B", bordercolor="#0F172A", font_size=12, font_color="white"),
        )
    else:
        fig_polar = _empty_fig("Colonnes 'orientation_theta' / 'orientation_psi' non disponibles")
    return fig_polar


def build_angles(fib_f):
    """Distributions des angles zénithal θ et azimutal ψ — Tran et al. (2024) Fig. 3."""
    if fib_f.empty or not _has(fib_f, "orientation_theta", "orientation_psi", "material"):
        return _empty_fig("Colonnes d'orientation non disponibles")

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=["Angle zénithal θ (inclinaison)", "Angle azimutal ψ (direction)"],
        horizontal_spacing=0.13,
    )

    shown = set()
    for i, mat in enumerate(sorted(fib_f["material"].dropna().unique())):
        grp = fib_f[fib_f["material"] == mat]
        theta_vals = grp["orientation_theta"].dropna()
        psi_vals   = grp["orientation_psi"].dropna()
        color = mat_color(mat, i)
        first = mat not in shown
        shown.add(mat)

        if not theta_vals.empty:
            fig.add_trace(go.Histogram(
                x=theta_vals, name=mat,
                marker_color=color,
                marker_line=dict(color="white", width=0.5),
                opacity=0.65, nbinsx=18, histnorm="probability density",
                legendgroup=mat, showlegend=first,
                hovertemplate=f"<b>{mat}</b><br>θ ≈ %{{x:.1f}}°<br>Densité = %{{y:.5f}}<extra></extra>",
            ), row=1, col=1)

        if not psi_vals.empty:
            fig.add_trace(go.Histogram(
                x=psi_vals, name=mat,
                marker_color=color,
                marker_line=dict(color="white", width=0.5),
                opacity=0.65, nbinsx=18, histnorm="probability density",
                legendgroup=mat, showlegend=False,
                hovertemplate=f"<b>{mat}</b><br>ψ ≈ %{{x:.1f}}°<br>Densité = %{{y:.5f}}<extra></extra>",
            ), row=1, col=2)

    # Styles des axes
    ax = {k: v for k, v in AXIS_STYLE.items() if k != "title_font"}
    fig.update_xaxes(**ax, title_font=AXIS_STYLE["title_font"])
    fig.update_yaxes(**ax, title_font=AXIS_STYLE["title_font"])
    fig.update_xaxes(title_text="θ (degrés)", row=1, col=1)
    fig.update_xaxes(title_text="ψ (degrés)", row=1, col=2)
    fig.update_yaxes(title_text="Densité de probabilité", row=1, col=1)

    fig.update_layout(
        **PLOT_LAYOUT,
        barmode="overlay",
        showlegend=False,
    )
    return fig
