from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from config import TABS, BASE_TAB, sel_tab, PLOT_LAYOUT, apply_grid, mat_color
from data import FREQ_COLS, _has, _empty_fig
from components import graph_card, tab_banner

# Conductivités thermiques des fibres (W/m·K) — source : rapport intermédiaire, Tableau 1
_LAMBDA_FIBRE = {
    "PET recyclé": 0.15,
    "Verre":       1.20,
    "Cuivre":      0.35,
    "Nylon":       0.25,
    "Chanvre":     0.10,
    "Carbone":     1.00,
}
_LAMBDA_AIR = 0.025   # conductivité de l'air (W/m·K)
_L_PANEL    = 0.05    # épaisseur d'un panneau standard (5 cm)


def get_tab():
    return dcc.Tab(
        label=TABS["correlations"]["label"],
        value="correlations",
        style=BASE_TAB,
        selected_style=sel_tab("correlations"),
        children=[html.Div(style={"padding": "28px 0 12px 0"}, children=[
            tab_banner(
                "correlations",
                "Quel matériau absorbe le mieux le son — et isole le mieux la chaleur ?",
                "Ces graphiques comparent directement les matériaux sur deux dimensions : "
                "leurs performances acoustiques (absorption du son) et leurs performances thermiques "
                "(isolation de la chaleur). L'objectif du projet est d'identifier la combinaison optimale "
                "diamètre / porosité / orientation qui maximise les deux à la fois. "
                "Références : Tran et al. (2024) ; rapport intermédiaire Logan, Tableaux 2 et 5.",
                [
                    "Chaque groupe de barres = une fréquence sonore (250 Hz = graves, 4 kHz = aigus).",
                    "Plus la barre est haute, plus le matériau absorbe le son à cette fréquence.",
                    "Le scatter montre si les fibres fines absorbent mieux que les grosses.",
                    "R thermique : plus c'est élevé, mieux le matériau isole (formule : R = L / λ_eff).",
                ],
            ),

            # Barres absorption par fréquence + scatter diamètre vs absorption
            dbc.Row(className="px-1 g-3", children=[
                graph_card(
                    "graph-ranking-bar",
                    "Absorption acoustique par matériau et par fréquence",
                    "Comparaison directe de tous les matériaux à chaque fréquence sonore. "
                    "Chaque groupe de barres correspond à une fréquence.",
                    "Plus la barre est haute = meilleure absorption. "
                    "Un bon matériau absorbe à toutes les fréquences, pas seulement les aigus.",
                    height="360px", col_width=7,
                    accent=TABS["correlations"]["bg"],
                ),
                graph_card(
                    "graph-morph-scatter",
                    "Taille des fibres vs absorption à 1 kHz",
                    "Chaque point = un échantillon. Position horizontale = diamètre moyen des fibres, "
                    "position verticale = absorption à 1 kHz (fréquence de la voix humaine). "
                    "Si les points forment une tendance descendante, les fibres fines absorbent mieux.",
                    "Survolez un point pour voir le matériau et les valeurs exactes. "
                    "Nuage dispersé = d'autres facteurs (porosité, tortuosité) jouent aussi un rôle.",
                    height="360px", col_width=5,
                    accent=TABS["correlations"]["bg"],
                ),
            ]),

            # Résistance thermique estimée
            dbc.Row(className="px-1 g-3", children=[
                graph_card(
                    "graph-thermal",
                    "Résistance thermique estimée par matériau R (m²·K/W)",
                    "Estimation de la résistance thermique de chaque matériau pour un panneau de 5 cm. "
                    "Calcul : R = L / λ_eff,  où  λ_eff = Φ·λ_air + (1−Φ)·λ_fibre. "
                    "Φ = porosité mesurée, L = 0,05 m. "
                    "Valeurs de λ_fibre issues du rapport intermédiaire (Tableau 1). "
                    "Plus R est élevé, plus le matériau isole thermiquement.",
                    "Les barres d'erreur représentent la variabilité due aux différentes porosités mesurées. "
                    "Comparez avec les valeurs de référence : PET ≈ 1,61 / Coton ≈ 1,31 / Verre ≈ 1,11 m²·K/W.",
                    height="340px", col_width=12,
                    accent=TABS["correlations"]["bg"],
                ),
            ]),
        ])]
    )


def build_ranking(aco_f):
    fig_ranking = go.Figure()
    if not aco_f.empty and FREQ_COLS and "material" in aco_f.columns:
        _freqs_labels = {
            "absorption_250hz":  "250 Hz",
            "absorption_500hz":  "500 Hz",
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
                marker=dict(size=12, color=mat_color(mat, i),
                            line=dict(width=1.5, color="white")),
                hovertemplate=(
                    f"<b>{mat}</b><br>"
                    "Ø = %{x:.1f} µm<br>"
                    "Absorption = %{y:.3f}"
                    "<extra></extra>"
                ),
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


def build_thermal(samp_f):
    """Résistance thermique estimée R = L / λ_eff par matériau.
    λ_eff = Φ·λ_air + (1−Φ)·λ_fibre  — rapport intermédiaire, section Logan."""
    if samp_f.empty or not _has(samp_f, "porosity", "material"):
        return _empty_fig("Données de porosité non disponibles")

    fig = go.Figure()
    mats = sorted(samp_f["material"].dropna().unique())
    r_means, r_stds, colors = [], [], []

    for i, mat in enumerate(mats):
        por_vals = samp_f[samp_f["material"] == mat]["porosity"].dropna()
        if por_vals.empty:
            r_means.append(0)
            r_stds.append(0)
            colors.append(mat_color(mat, i))
            continue
        lf   = _LAMBDA_FIBRE.get(mat, 0.25)
        leff = por_vals * _LAMBDA_AIR + (1.0 - por_vals) * lf
        r    = _L_PANEL / leff
        r_means.append(float(r.mean()))
        r_stds.append(float(r.std()) if len(r) > 1 else 0.0)
        colors.append(mat_color(mat, i))

    fig.add_trace(go.Bar(
        x=list(mats),
        y=r_means,
        error_y=dict(
            type="data", array=r_stds, visible=True,
            color="#64748B", thickness=1.5, width=6,
        ),
        marker_color=colors,
        marker_line=dict(color="white", width=1.5),
        hovertemplate=(
            "<b>%{x}</b><br>"
            "R ≈ %{y:.2f} m²·K/W<br>"
            "<i>λ_eff = Φ·λ_air + (1−Φ)·λ_fibre</i>"
            "<extra></extra>"
        ),
        showlegend=False,
    ))

    # Ligne de référence : valeur minimale recommandée RT2012 (toiture)
    fig.add_hline(
        y=1.0,
        line_dash="dot", line_color="#94A3B8", line_width=1.5,
        annotation_text="R = 1,0 m²·K/W (référence)",
        annotation_font_size=10,
        annotation_font_color="#64748B",
    )

    fig.update_layout(
        **PLOT_LAYOUT,
        xaxis_title="Matériau",
        yaxis_title="Résistance thermique estimée R (m²·K/W)",
    )
    apply_grid(fig)
    return fig
