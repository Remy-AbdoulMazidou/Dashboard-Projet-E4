from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import numpy as np
from config import TABS, BASE_TAB, sel_tab, PLOT_LAYOUT, apply_grid, mat_color
from data import _has, _empty_fig
from components import graph_card, tab_banner, _absorption_card

# Valeurs de référence issues du rapport intermédiaire (Logan — Tableau 4)
_RW_REF = [
    ("PET recyclé",     "18 – 22", "1 200 – 1 500", "0,85"),
    ("Coton textile",   "20 – 24", "1 000 – 1 200", "0,92"),
    ("Fibres de verre", "22 – 26", "800 – 1 000",   "0,95"),
]


def _rw_reference_block():
    accent = TABS["acoustics"]["bg"]
    _h = {"backgroundColor": accent, "color": "white",
          "padding": "8px 14px", "fontWeight": 700, "fontSize": "11px",
          "textAlign": "center", "borderRight": "1px solid rgba(255,255,255,0.3)"}
    _c_even = {"backgroundColor": "#FFFBEB", "padding": "7px 14px",
               "fontSize": "12px", "color": "#1E293B", "textAlign": "center",
               "borderRight": "1px solid #FDE68A"}
    _c_odd  = {"backgroundColor": "white", "padding": "7px 14px",
               "fontSize": "12px", "color": "#1E293B", "textAlign": "center",
               "borderRight": "1px solid #FDE68A"}

    header_row = html.Div(style={
        "display": "grid", "gridTemplateColumns": "2fr 1fr 1fr 1fr",
        "backgroundColor": accent, "borderRadius": "8px 8px 0 0",
    }, children=[
        html.Div(h, style=_h)
        for h in ["Matériau (référence)", "Rw (dB)", "fp (Hz)", "α_max"]
    ])

    data_rows = []
    for k, (mat, rw, fp, amax) in enumerate(_RW_REF):
        cell_style = _c_even if k % 2 == 0 else _c_odd
        data_rows.append(html.Div(style={
            "display": "grid", "gridTemplateColumns": "2fr 1fr 1fr 1fr",
            "borderTop": "1px solid #FDE68A",
        }, children=[
            html.Div(mat,  style={**cell_style, "fontWeight": 600, "textAlign": "left"}),
            html.Div(rw,   style=cell_style),
            html.Div(fp,   style=cell_style),
            html.Div(amax, style=cell_style),
        ]))

    return html.Div(style={
        "backgroundColor": "#FFFBEB",
        "border": "1px solid #FDE68A",
        "borderLeft": f"5px solid {accent}",
        "borderRadius": "10px",
        "padding": "18px 22px",
        "margin": "0 8px 20px 8px",
    }, children=[
        html.H6(
            "Valeurs de référence — Affaiblissement acoustique Rw et absorption maximale",
            style={"color": accent, "fontWeight": 800, "fontSize": "14px", "marginBottom": "6px"},
        ),
        html.P(
            "Ces valeurs sont issues du rapport intermédiaire (Logan, Tableau 4). "
            "Rw mesure la capacité du matériau à réduire le bruit transmis (plus c'est élevé, mieux c'est). "
            "fp est la fréquence à laquelle l'absorption est maximale — elle dépend directement de la tortuosité α∞. "
            "α_max est le pic d'absorption maximal possible pour ce matériau.",
            style={"fontSize": "12px", "color": "#92400E", "lineHeight": "1.65", "marginBottom": "12px"},
        ),
        html.Div(style={"border": "1px solid #FDE68A", "borderRadius": "8px", "overflow": "hidden"}, children=[
            header_row,
            *data_rows,
        ]),
        html.P(
            "Formules : Rw = 10·log₁₀(1/τ) en dB  |  fp = c₀ / (4·L·√α∞)  |  α_max = 1 − |Zs−Z₀|² / |Zs+Z₀|²",
            style={"fontSize": "11px", "color": "#B45309", "marginTop": "10px",
                   "marginBottom": "0", "fontStyle": "italic"},
        ),
    ])


def get_tab():
    return dcc.Tab(
        label=TABS["acoustics"]["label"],
        value="acoustics",
        style=BASE_TAB,
        selected_style=sel_tab("acoustics"),
        children=[html.Div(style={"padding": "28px 0 12px 0"}, children=[
            tab_banner(
                "acoustics",
                "Performances sonores et paramètres physiques des matériaux fibreux",
                "Ces mesures montrent combien de son chaque matériau absorbe selon la fréquence "
                "(grave, medium, aigu). L'objectif est de relier ces performances aux caractéristiques "
                "des fibres (épaisseur, porosité, tortuosité...) pour concevoir de meilleurs matériaux "
                "sans avoir à tout mesurer en laboratoire. "
                "Le modèle JCAL (Johnson-Champoux-Allard-Lafarge) est utilisé pour lier microstructure et acoustique.",
                [
                    "α : coefficient d'absorption (0 = le son rebondit, 1 = le son est totalement absorbé).",
                    "Résistivité σ : résistance au passage de l'air — une valeur intermédiaire est idéale.",
                    "Longueur visqueuse Λ et thermique Λ' : dimensions caractéristiques des pores (modèle JCAL).",
                    "Rw : indice d'affaiblissement acoustique en dB — mesure globale de l'isolation.",
                ],
            ),

            # Courbes d'absorption
            dbc.Row(className="px-1 g-3", children=[
                _absorption_card(),
            ]),

            # Résistivité vs porosité
            dbc.Row(className="px-1 g-3", children=[
                graph_card(
                    "graph-resistivity",
                    "Résistance à l'air vs quantité de vide (porosité)",
                    "Ce graphique montre tous les échantillons analysés. "
                    "On compare leur résistance au passage de l'air (axe vertical) "
                    "à leur porosité (axe horizontal), c'est-à-dire le pourcentage de vide dans le matériau. "
                    "Un matériau très poreux laisse passer l'air facilement (faible résistivité). "
                    "La ligne pointillée montre la tendance générale.",
                    "Survolez un point pour voir l'échantillon correspondant. "
                    "La résistivité est un paramètre clé du modèle JCAL.",
                    height="310px", col_width=12,
                    accent=TABS["acoustics"]["bg"],
                ),
            ]),

            # Paramètres JCAL
            dbc.Row(className="px-1 g-3", children=[
                graph_card(
                    "graph-jcal",
                    "Paramètres JCAL — Longueurs caractéristiques Λ et Λ' (µm)",
                    "Le modèle Johnson-Champoux-Allard-Lafarge (JCAL) utilise deux longueurs "
                    "caractéristiques pour décrire les pertes d'énergie dans le matériau. "
                    "Λ (longueur visqueuse) traduit les frottements de l'air dans les pores. "
                    "Λ' (longueur thermique) traduit les échanges thermiques entre l'air et les fibres. "
                    "Ces valeurs dépendent directement de la microstructure du réseau fibreux.",
                    "Des petites longueurs Λ et Λ' = pores fins = plus de frottement = meilleure absorption à hautes fréquences. "
                    "Barres pleines = Λ (visqueux), barres transparentes = Λ' (thermique).",
                    height="320px", col_width=12,
                    accent=TABS["acoustics"]["bg"],
                ),
            ]),

            # Tableau de référence Rw
            _rw_reference_block(),
        ])]
    )


def build_resistivity(samp_f, aco_res):
    fig_res = go.Figure()
    if not aco_res.empty and _has(aco_res, "porosity", "airflow_resistivity", "material"):
        for i, mat in enumerate(sorted(aco_res["material"].dropna().unique())):
            grp = aco_res[aco_res["material"] == mat].dropna(
                subset=["porosity", "airflow_resistivity"]
            )
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


def build_jcal(aco_f):
    """Longueurs caractéristiques Λ et Λ' du modèle JCAL par matériau."""
    if aco_f.empty or not _has(aco_f, "viscous_length_um", "thermal_length_um", "material"):
        return _empty_fig("Paramètres JCAL (Λ, Λ') non disponibles dans les données")

    fig = go.Figure()
    mats = sorted(aco_f["material"].dropna().unique())

    lam_vis = [aco_f[aco_f["material"] == m]["viscous_length_um"].mean() for m in mats]
    lam_th  = [aco_f[aco_f["material"] == m]["thermal_length_um"].mean()  for m in mats]
    colors  = [mat_color(m, i) for i, m in enumerate(mats)]

    fig.add_trace(go.Bar(
        name="Λ — longueur visqueuse",
        x=list(mats), y=lam_vis,
        marker_color=colors,
        marker_line=dict(color="white", width=1.5),
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Λ (visqueux) = %{y:.1f} µm<br>"
            "<i>Frottements de l'air dans les pores</i>"
            "<extra></extra>"
        ),
    ))

    fig.add_trace(go.Bar(
        name="Λ' — longueur thermique",
        x=list(mats), y=lam_th,
        marker_color=colors,
        marker_line=dict(color="white", width=1.5),
        opacity=0.50,
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Λ' (thermique) = %{y:.1f} µm<br>"
            "<i>Échanges thermiques entre l'air et les fibres</i>"
            "<extra></extra>"
        ),
    ))

    fig.update_layout(
        **PLOT_LAYOUT,
        barmode="group",
        xaxis_title="Matériau",
        yaxis_title="Longueur caractéristique (µm)",
        showlegend=True,
        legend=dict(orientation="h", y=-0.28, x=0.5, xanchor="center", font_size=11),
    )
    apply_grid(fig)
    return fig
