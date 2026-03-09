"""
FiberScope — Dashboard Microtomographie Fibres
Projet E4 MSME — Page unique, visualisations essentielles
"""

import os
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# ─── Données ──────────────────────────────────────────────────────────────────
BASE = os.path.dirname(__file__)

samples  = pd.read_csv(os.path.join(BASE, "data/samples.csv"))
fibers   = pd.read_csv(os.path.join(BASE, "data/fibers.csv"))
contacts = pd.read_csv(os.path.join(BASE, "data/contacts.csv"))
acoustic = pd.read_csv(os.path.join(BASE, "data/acoustic_thermal.csv"))

fibers_m   = fibers.merge(samples[["sample_id","material","batch"]], on="sample_id", how="left")
contacts_m = contacts.merge(samples[["sample_id","material","batch"]], on="sample_id", how="left")
acoustic_m = acoustic.merge(samples[["sample_id","material","batch"]], on="sample_id", how="left")

MATERIALS = sorted(samples["material"].unique().tolist())
BATCHES   = sorted(samples["batch"].unique().tolist())

MAT_COLORS = {
    "Nylon":       "#3B82F6",
    "Carbone":     "#EF4444",
    "Verre":       "#22C55E",
    "Cuivre":      "#F59E0B",
    "PET recyclé": "#8B5CF6",
    "Chanvre":     "#10B981",
}

PLOT_CONFIG = {"displayModeBar": False, "responsive": True}

PLOT_LAYOUT = dict(
    paper_bgcolor="white",
    plot_bgcolor="#F8FAFC",
    font=dict(family="Inter, sans-serif", size=12, color="#334155"),
    margin=dict(l=55, r=20, t=30, b=50),
)


# ─── Composants réutilisables ─────────────────────────────────────────────────

def section_header(title, subtitle, color="#2563EB"):
    """Titre de section centré avec trait coloré et sous-titre explicatif."""
    return dbc.Row(className="px-3 mt-4 mb-3", children=[
        dbc.Col(html.Div([
            html.Div(style={
                "width": "48px", "height": "4px",
                "backgroundColor": color,
                "borderRadius": "2px",
                "margin": "0 auto 10px auto",
            }),
            html.H4(title, style={
                "textAlign": "center",
                "color": "#0F172A",
                "fontWeight": 700,
                "marginBottom": "8px",
                "fontSize": "20px",
            }),
            html.P(subtitle, style={
                "textAlign": "center",
                "color": "#64748B",
                "fontSize": "14px",
                "maxWidth": "720px",
                "margin": "0 auto",
                "lineHeight": "1.6",
            }),
        ]))
    ])


def graph_card(graph_id, title, description, read_guide, height="310px", col_width=6):
    """Carte graphique avec titre, description méthodologique et guide de lecture."""
    return dbc.Col(dbc.Card(style={
        "borderRadius": "12px",
        "border": "1px solid #E2E8F0",
        "boxShadow": "0 2px 8px rgba(0,0,0,0.06)",
        "height": "100%",
    }, children=[
        dbc.CardBody([
            # Titre
            html.H6(title, style={
                "fontWeight": 700,
                "color": "#0F172A",
                "marginBottom": "4px",
                "fontSize": "14px",
            }),
            # Description — ce que montre le graphique
            html.P(description, style={
                "fontSize": "12px",
                "color": "#64748B",
                "marginBottom": "6px",
                "lineHeight": "1.5",
            }),
            # Guide de lecture
            html.Div([
                html.Span("Comment lire ce graphique : ", style={
                    "fontWeight": 600,
                    "fontSize": "11px",
                    "color": "#475569",
                }),
                html.Span(read_guide, style={
                    "fontSize": "11px",
                    "color": "#475569",
                }),
            ], style={
                "backgroundColor": "#F1F5F9",
                "borderLeft": "3px solid #CBD5E1",
                "padding": "6px 10px",
                "borderRadius": "0 4px 4px 0",
                "marginBottom": "10px",
            }),
            # Graphique
            dcc.Graph(id=graph_id, config=PLOT_CONFIG, style={"height": height}),
        ])
    ]), md=col_width, className="mb-3")


def kpi_card(kpi_id, label, explanation, color):
    """Carte KPI sans émoji, avec label et explication."""
    return dbc.Col(dbc.Card(style={
        "borderRadius": "12px",
        "borderTop": f"4px solid {color}",
        "border": "1px solid #E2E8F0",
        "boxShadow": "0 2px 6px rgba(0,0,0,0.05)",
    }, children=[
        dbc.CardBody([
            html.P(label, style={
                "fontSize": "11px",
                "fontWeight": 700,
                "color": "#64748B",
                "textTransform": "uppercase",
                "letterSpacing": "0.05em",
                "marginBottom": "4px",
            }),
            html.H3(id=kpi_id, style={
                "fontSize": "28px",
                "fontWeight": 800,
                "color": color,
                "marginBottom": "4px",
            }),
            html.P(explanation, style={
                "fontSize": "11px",
                "color": "#94A3B8",
                "margin": 0,
                "lineHeight": "1.4",
            }),
        ])
    ]), md=True, className="mb-3")


# ─── App ──────────────────────────────────────────────────────────────────────
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY],
    title="FiberScope — MSME",
    suppress_callback_exceptions=True,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
server = app.server

# ─── Layout ───────────────────────────────────────────────────────────────────
app.layout = dbc.Container(fluid=True, style={"backgroundColor": "#F8FAFC", "minHeight": "100vh"}, children=[

    # ── HEADER ──────────────────────────────────────────────────────────────
    html.Div(style={
        "background": "linear-gradient(135deg, #0F172A 0%, #1E40AF 60%, #2563EB 100%)",
        "padding": "36px 24px 32px 24px",
        "marginBottom": "0",
        "textAlign": "center",
    }, children=[
        html.H1("FiberScope", style={
            "color": "white",
            "fontWeight": 800,
            "fontSize": "36px",
            "letterSpacing": "-0.5px",
            "marginBottom": "8px",
        }),
        html.P(
            "Caractérisation morphologique des réseaux fibreux par microtomographie X",
            style={"color": "#BAE6FD", "fontSize": "15px", "marginBottom": "10px", "fontWeight": 400}
        ),
        html.P(
            "Ce tableau de bord présente les résultats issus de l'analyse d'images 3D obtenues "
            "par microtomographie axiale à rayons X. Il permet d'explorer les propriétés "
            "géométriques des fibres et leurs liens avec les performances acoustiques des matériaux étudiés.",
            style={
                "color": "#93C5FD",
                "fontSize": "13px",
                "maxWidth": "700px",
                "margin": "0 auto",
                "lineHeight": "1.7",
            }
        ),
    ]),

    # ── FILTRES ─────────────────────────────────────────────────────────────
    dbc.Row(className="my-4 px-3", children=[
        dbc.Col(dbc.Card(style={
            "borderRadius": "12px",
            "border": "1px solid #E2E8F0",
            "boxShadow": "0 2px 6px rgba(0,0,0,0.05)",
        }, children=[
            dbc.CardBody([
                html.P(
                    "Utilisez les filtres ci-dessous pour restreindre l'analyse à un matériau "
                    "ou un lot spécifique. Tous les graphiques et indicateurs se mettent à jour automatiquement.",
                    style={"fontSize": "12px", "color": "#64748B", "marginBottom": "14px"}
                ),
                dbc.Row([
                    dbc.Col([
                        html.Label("Filtrer par matériau", style={
                            "fontWeight": 700, "fontSize": "12px",
                            "color": "#334155", "marginBottom": "6px", "display": "block"
                        }),
                        dcc.Dropdown(
                            id="filter-material",
                            options=[{"label": m, "value": m} for m in MATERIALS],
                            multi=True,
                            placeholder="Tous les matériaux affichés",
                            style={"fontSize": "13px"},
                        )
                    ], md=5),
                    dbc.Col([
                        html.Label("Filtrer par lot de fabrication", style={
                            "fontWeight": 700, "fontSize": "12px",
                            "color": "#334155", "marginBottom": "6px", "display": "block"
                        }),
                        dcc.Dropdown(
                            id="filter-batch",
                            options=[{"label": b, "value": b} for b in BATCHES],
                            multi=True,
                            placeholder="Tous les lots affichés",
                            style={"fontSize": "13px"},
                        )
                    ], md=4),
                    dbc.Col([
                        html.Label(" ", style={"display": "block", "fontSize": "12px", "marginBottom": "6px"}),
                        dbc.Button(
                            "Réinitialiser les filtres",
                            id="btn-reset",
                            color="light",
                            style={
                                "border": "1px solid #CBD5E1",
                                "color": "#475569",
                                "fontWeight": 600,
                                "fontSize": "12px",
                                "width": "100%",
                            }
                        )
                    ], md=3, className="d-flex align-items-end"),
                ])
            ])
        ]))
    ]),

    # ── INDICATEURS CLÉS ────────────────────────────────────────────────────
    dbc.Row(className="px-3 mb-1", children=[
        dbc.Col(html.Div([
            html.H5("Vue d'ensemble", style={
                "textAlign": "center", "color": "#0F172A",
                "fontWeight": 700, "marginBottom": "4px", "fontSize": "18px",
            }),
            html.P(
                "Ces cinq indicateurs résument les données disponibles pour la sélection en cours. "
                "Ils permettent de saisir rapidement l'étendue du jeu de données analysé.",
                style={"textAlign": "center", "color": "#64748B", "fontSize": "13px", "marginBottom": "16px"}
            ),
        ]))
    ]),
    dbc.Row(id="row-kpis", className="px-3 mb-2"),

    # ── SECTION 1 : Morphologie des fibres ──────────────────────────────────
    section_header(
        "Morphologie des fibres",
        "La microtomographie X permet de mesurer chaque fibre individuellement dans un volume 3D. "
        "Ces graphiques montrent comment les dimensions (diamètre, longueur), la forme (courbure) "
        "et l'orientation des fibres varient selon le matériau — des informations inaccessibles sans cette technique d'imagerie.",
        color="#2563EB"
    ),
    dbc.Row(className="px-3", children=[
        graph_card(
            "graph-diameter",
            "Diametre des fibres par materiau (µm)",
            "Chaque boîte représente la distribution des diamètres de toutes les fibres d'un même matériau. "
            "Le diamètre influence directement la surface de contact disponible et la perméabilité du réseau.",
            "La ligne centrale est la médiane. La boîte contient 50 % des fibres. "
            "Les points isolés sont des fibres atypiques (outliers). "
            "Un écart important entre matériaux signale des microstructures très différentes.",
        ),
        graph_card(
            "graph-length",
            "Longueur des fibres par materiau (µm)",
            "La longueur des fibres conditionne leur capacité à former des connexions dans le réseau "
            "et leur comportement sous contrainte mécanique. "
            "Des fibres longues créent un réseau plus enchevêtré, favorable à l'absorption acoustique.",
            "Même lecture que le diamètre. Comparez les médianes entre matériaux pour identifier "
            "les différences structurelles. Une boîte étendue indique une grande variabilité de fabrication.",
        ),
    ]),
    dbc.Row(className="px-3", children=[
        graph_card(
            "graph-orientation",
            "Distribution des orientations angulaires θ",
            "L'angle θ mesure l'inclinaison de chaque fibre par rapport au plan horizontal de l'échantillon. "
            "θ = 0° signifie que la fibre est couchée dans le plan ; θ = 90° signifie qu'elle est perpendiculaire au plan. "
            "Cette distribution est essentielle pour comprendre l'anisotropie du matériau.",
            "Un pic marqué près de 0° indique un matériau fortement plan (fibres alignées horizontalement). "
            "Une distribution étalée signifie des fibres orientées dans toutes les directions (matériau isotrope). "
            "L'anisotropie rend les propriétés acoustiques directionnelles.",
        ),
        graph_card(
            "graph-curvature",
            "Courbure des fibres par materiau (κ × 10³ mm⁻¹)",
            "La courbure κ = 1/R mesure à quel point une fibre s'écarte d'une droite parfaite. "
            "Une fibre parfaitement rectiligne a κ ≈ 0. "
            "Plus κ est élevé, plus la fibre est ondulée — ce qui modifie sa surface effective et son comportement mécanique.",
            "Des valeurs proches de zéro indiquent des fibres rectilignes (typique du verre ou du carbone). "
            "Des valeurs plus élevées signalent des fibres ondulées ou torsadées (naturelles ou recyclées). "
            "La courbure influe sur la densité de liaisons et la tortuosité des chemins acoustiques.",
        ),
    ]),

    # ── SECTION 2 : Liaisons inter-fibres ───────────────────────────────────
    section_header(
        "Liaisons inter-fibres",
        "Lorsque deux fibres se croisent ou se touchent dans le volume 3D, elles forment une liaison. "
        "Le nombre, la distribution et la surface de ces liaisons sont des paramètres clés : "
        "ils gouvernent à la fois la rigidité mécanique du réseau et la résistance au passage de l'air, "
        "qui est le principal mécanisme d'absorption acoustique.",
        color="#16A34A"
    ),
    dbc.Row(className="px-3", children=[
        graph_card(
            "graph-contact-area",
            "Distribution des aires de contact fibre-fibre (µm²)",
            "Quand deux fibres se touchent, leur surface de contact détermine la solidité de la liaison. "
            "Une grande aire de contact crée une jonction rigide ; une petite aire donne une liaison plus souple. "
            "Ce paramètre est lié à la forme des sections transversales et à l'angle de croisement.",
            "La majorité des contacts ont une petite surface (pic à gauche). "
            "Une queue étendue vers la droite indique l'existence de quelques jonctions larges — souvent dues "
            "à des fibres qui se croisent à faible angle. Comparez les matériaux pour identifier les différences de cohésion.",
        ),
        graph_card(
            "graph-density-porosity",
            "Densite de connexions vs Porosite",
            "La densité de connexions (nombre de liaisons par mm³ de volume) est mise en regard de la porosité "
            "(fraction de vide dans le matériau). Ces deux grandeurs sont étroitement liées : "
            "plus un matériau est dense (porosité faible), plus les fibres sont proches et forment de connexions.",
            "Une tendance décroissante est attendue : plus la porosité est élevée, moins il y a de connexions. "
            "Les points qui s'écartent de cette tendance signalent des matériaux atypiques — "
            "par exemple des fibres très fines (beaucoup de connexions malgré une faible densité volumique).",
        ),
    ]),

    # ── SECTION 3 : Propriétés acoustiques ──────────────────────────────────
    section_header(
        "Proprietes acoustiques",
        "Ces mesures expérimentales quantifient comment chaque matériau absorbe les ondes sonores. "
        "Les données proviennent de 17 échantillons pour lesquels des mesures acoustiques complètes ont été réalisées. "
        "L'objectif est de relier la microstructure (porosité, diamètre des fibres) à la performance acoustique — "
        "ce lien est la clé pour concevoir des matériaux légers et performants.",
        color="#D97706"
    ),
    dbc.Row(className="px-3", children=[
        graph_card(
            "graph-absorption",
            "Coefficient d'absorption acoustique par frequence",
            "Le coefficient d'absorption α varie entre 0 (le son est totalement réfléchi) et 1 (le son est totalement absorbé). "
            "Chaque courbe représente un échantillon. Les matériaux fibreux absorbent généralement mieux les "
            "hautes fréquences (voix, bruits de moteur) que les basses fréquences.",
            "Un coefficient élevé à 1000-4000 Hz est caractéristique des bons absorbants acoustiques. "
            "Les courbes qui montent fortement dès 500 Hz sont les plus intéressantes pour les applications transport. "
            "La courbe en pointillés noirs représente la valeur médiane sur tous les échantillons affichés.",
            height="330px",
            col_width=7,
        ),
        graph_card(
            "graph-resistivity",
            "Resistivite au flux d'air vs Porosite",
            "La résistivité au flux σ (Pa·s/m²) mesure combien un matériau s'oppose au passage de l'air. "
            "C'est le paramètre acoustique le plus important pour les matériaux fibreux. "
            "Elle dépend directement de la porosité : un matériau dense (peu poreux) bloque davantage l'air.",
            "L'axe vertical est en échelle logarithmique car les valeurs couvrent plusieurs ordres de grandeur. "
            "La courbe en pointillés montre la tendance générale. "
            "Un bon absorbant acoustique possède une résistivité dans une plage optimale — "
            "ni trop faible (le son passe sans être atténué), ni trop élevée (le son est réfléchi).",
            height="330px",
            col_width=5,
        ),
    ]),

    # ── FOOTER ──────────────────────────────────────────────────────────────
    dbc.Row(className="px-3 pb-5 mt-2", children=[
        dbc.Col([
            html.Hr(style={"borderColor": "#E2E8F0"}),
            html.P(
                "FiberScope — Projet E4 MSME — Analyse par microtomographie X",
                style={"textAlign": "center", "color": "#94A3B8", "fontSize": "12px", "margin": 0}
            )
        ])
    ]),
])


# ─── Helpers ──────────────────────────────────────────────────────────────────
def _filter(mat_sel, bat_sel):
    mask = pd.Series([True] * len(samples))
    if mat_sel:
        mask &= samples["material"].isin(mat_sel)
    if bat_sel:
        mask &= samples["batch"].isin(bat_sel)
    return samples[mask]["sample_id"].tolist(), samples[mask]


def _boxplot(df, y_col, color_col="material", title_y=""):
    fig = go.Figure()
    for mat in sorted(df[color_col].dropna().unique()):
        vals = df[df[color_col] == mat][y_col].dropna()
        if len(vals) == 0:
            continue
        fig.add_trace(go.Box(
            y=vals, name=mat,
            marker_color=MAT_COLORS.get(mat, "#94A3B8"),
            boxpoints="outliers",
            line_width=1.8,
            marker_size=3,
        ))
    fig.update_layout(**PLOT_LAYOUT, yaxis_title=title_y, showlegend=False)
    return fig


# ─── Callback principal ───────────────────────────────────────────────────────
@app.callback(
    Output("row-kpis",           "children"),
    Output("graph-diameter",     "figure"),
    Output("graph-length",       "figure"),
    Output("graph-orientation",  "figure"),
    Output("graph-curvature",    "figure"),
    Output("graph-contact-area", "figure"),
    Output("graph-density-porosity", "figure"),
    Output("graph-absorption",   "figure"),
    Output("graph-resistivity",  "figure"),
    Input("filter-material", "value"),
    Input("filter-batch",    "value"),
)
def update_all(mat_sel, bat_sel):
    ids, samp_f = _filter(mat_sel, bat_sel)
    fib_f = fibers_m[fibers_m["sample_id"].isin(ids)]
    con_f = contacts_m[contacts_m["sample_id"].isin(ids)]
    aco_f = acoustic_m[acoustic_m["sample_id"].isin(ids)]

    # ── KPIs ────────────────────────────────────────────────────────────────
    n_samples  = len(samp_f)
    n_fibers   = len(fib_f)
    n_contacts = len(con_f)
    mean_por   = samp_f["porosity"].mean()
    mean_qual  = samp_f["quality_score"].mean()

    kpis = [
        kpi_card("kpi-samples",  "Echantillons analysés",
                 "Blocs de matériau imagés par microtomographie X", "#2563EB"),
        kpi_card("kpi-fibers",   "Fibres détectées",
                 "Fibres individuelles segmentées dans les volumes 3D", "#8B5CF6"),
        kpi_card("kpi-contacts", "Liaisons fibre-fibre",
                 "Points de contact entre fibres identifiés dans le réseau", "#22C55E"),
        kpi_card("kpi-porosity", "Porosité moyenne",
                 "Fraction de vide dans le matériau (0 = dense, 1 = creux)", "#F59E0B"),
        kpi_card("kpi-quality",  "Score qualité moyen",
                 "Note de 1 à 5 évaluant la qualité de la reconstruction 3D", "#EF4444"),
    ]

    # Valeurs (injectées via IDs séparés ou directement dans le children)
    # On retourne les KPIs avec les valeurs déjà intégrées
    def val(v): return str(v)

    kpis_filled = [
        dbc.Col(dbc.Card(style={
            "borderRadius": "12px",
            "borderTop": f"4px solid {c}",
            "border": "1px solid #E2E8F0",
            "boxShadow": "0 2px 6px rgba(0,0,0,0.05)",
        }, children=[dbc.CardBody([
            html.P(label, style={
                "fontSize": "10px", "fontWeight": 700, "color": "#64748B",
                "textTransform": "uppercase", "letterSpacing": "0.06em", "marginBottom": "4px",
            }),
            html.H3(value, style={
                "fontSize": "26px", "fontWeight": 800, "color": c, "marginBottom": "4px",
            }),
            html.P(expl, style={"fontSize": "11px", "color": "#94A3B8", "margin": 0, "lineHeight": "1.4"}),
        ])]), md=True, className="mb-3")
        for label, value, expl, c in [
            ("Echantillons analysés", str(n_samples),
             "Blocs de matériau imagés par microtomographie X", "#2563EB"),
            ("Fibres détectées", f"{n_fibers:,}",
             "Fibres individuelles segmentées dans les volumes 3D", "#8B5CF6"),
            ("Liaisons fibre-fibre", f"{n_contacts:,}",
             "Points de contact entre fibres identifiés dans le réseau", "#22C55E"),
            ("Porosité moyenne", f"{mean_por:.2f}" if n_samples else "—",
             "Fraction de vide (0 = matériau dense, 1 = entièrement creux)", "#F59E0B"),
            ("Score qualité", f"{mean_qual:.1f} / 5" if n_samples else "—",
             "Qualité de la reconstruction 3D (algorithme de segmentation)", "#EF4444"),
        ]
    ]

    # ── Diamètre ────────────────────────────────────────────────────────────
    fig_diam = _boxplot(fib_f, "diameter_um", title_y="Diamètre (µm)")

    # ── Longueur ────────────────────────────────────────────────────────────
    fig_len = _boxplot(fib_f, "length_um", title_y="Longueur (µm)")

    # ── Orientations θ ─────────────────────────────────────────────────────
    fig_ori = go.Figure()
    for mat in sorted(fib_f["material"].dropna().unique()):
        vals = fib_f[fib_f["material"] == mat]["orientation_theta"].dropna()
        if len(vals) == 0:
            continue
        fig_ori.add_trace(go.Histogram(
            x=vals, name=mat,
            marker_color=MAT_COLORS.get(mat, "#94A3B8"),
            opacity=0.72, nbinsx=18, histnorm="percent",
        ))
    fig_ori.update_layout(
        **PLOT_LAYOUT, barmode="overlay",
        xaxis_title="θ (degrés)", yaxis_title="% des fibres",
        legend=dict(orientation="h", y=1.05, x=0, font_size=11),
    )

    # ── Courbure ────────────────────────────────────────────────────────────
    fib_f2 = fib_f.copy()
    fib_f2["curvature_scaled"] = fib_f2["curvature"] * 1000
    fig_curv = _boxplot(fib_f2, "curvature_scaled", title_y="κ × 10³ (mm⁻¹)")

    # ── Aires de contact ────────────────────────────────────────────────────
    fig_ca = go.Figure()
    for mat in sorted(con_f["material"].dropna().unique()):
        vals = con_f[con_f["material"] == mat]["contact_area_um2"].dropna()
        if len(vals) == 0:
            continue
        p99 = vals.quantile(0.99)
        vals = vals[vals <= p99]
        fig_ca.add_trace(go.Histogram(
            x=vals, name=mat,
            marker_color=MAT_COLORS.get(mat, "#94A3B8"),
            opacity=0.72, nbinsx=30, histnorm="percent",
        ))
    fig_ca.update_layout(
        **PLOT_LAYOUT, barmode="overlay",
        xaxis_title="Aire de contact (µm²)", yaxis_title="% des contacts",
        legend=dict(orientation="h", y=1.05, x=0, font_size=11),
    )

    # ── Densité connexions vs Porosité ──────────────────────────────────────
    fig_dp = go.Figure()
    for mat in sorted(samp_f["material"].dropna().unique()):
        sub = samp_f[samp_f["material"] == mat]
        fig_dp.add_trace(go.Scatter(
            x=sub["porosity"], y=sub["contact_density"],
            mode="markers", name=mat,
            marker=dict(color=MAT_COLORS.get(mat, "#94A3B8"), size=10,
                        line=dict(width=1.5, color="white")),
            text=sub["sample_id"],
            hovertemplate="<b>%{text}</b><br>Porosité : %{x:.3f}<br>Densité : %{y:.1f} N/mm³<extra></extra>",
        ))
    fig_dp.update_layout(
        **PLOT_LAYOUT,
        xaxis_title="Porosité",
        yaxis_title="Densité de connexions (N/mm³)",
        legend=dict(orientation="h", y=1.05, x=0, font_size=11),
    )

    # ── Absorption acoustique ────────────────────────────────────────────────
    freqs     = [250, 500, 1000, 2000, 4000]
    freq_cols = ["absorption_250hz","absorption_500hz","absorption_1000hz",
                 "absorption_2000hz","absorption_4000hz"]
    fig_abs = go.Figure()
    if len(aco_f) > 0:
        for _, row in aco_f.iterrows():
            vals = [row[c] for c in freq_cols if c in row.index]
            if len(vals) < 5 or any(pd.isna(v) for v in vals):
                continue
            mat = row.get("material", "—")
            fig_abs.add_trace(go.Scatter(
                x=freqs, y=vals,
                mode="lines+markers",
                name=f"{row['sample_id']} ({mat})",
                line=dict(color=MAT_COLORS.get(mat, "#94A3B8"), width=1.8),
                marker=dict(size=5),
                opacity=0.85,
                hovertemplate=f"<b>{row['sample_id']}</b><br>%{{x}} Hz : α = %{{y:.3f}}<extra></extra>",
            ))
        medians = [aco_f[c].dropna().median() for c in freq_cols if c in aco_f.columns]
        if len(medians) == 5:
            fig_abs.add_trace(go.Scatter(
                x=freqs, y=medians, mode="lines", name="Médiane globale",
                line=dict(color="#0F172A", width=3, dash="dot"),
            ))
    fig_abs.update_layout(
        **PLOT_LAYOUT,
        xaxis=dict(title="Fréquence (Hz)", tickvals=freqs,
                   ticktext=["250 Hz","500 Hz","1 kHz","2 kHz","4 kHz"]),
        yaxis=dict(title="Coefficient α", range=[0, 1.05]),
        legend=dict(orientation="v", x=1.01, y=1, font_size=10),
    )

    # ── Résistivité vs Porosité ─────────────────────────────────────────────
    fig_res = go.Figure()
    if len(aco_f) > 0:
        for mat in sorted(aco_f["material"].dropna().unique()):
            sub = aco_f[aco_f["material"] == mat]
            fig_res.add_trace(go.Scatter(
                x=sub["porosity"], y=sub["airflow_resistivity"],
                mode="markers", name=mat,
                marker=dict(color=MAT_COLORS.get(mat, "#94A3B8"), size=11,
                            line=dict(width=1.5, color="white")),
                text=sub["sample_id"],
                hovertemplate="<b>%{text}</b><br>Porosité : %{x:.3f}<br>σ = %{y:,.0f} Pa·s/m²<extra></extra>",
            ))
        x_v = aco_f["porosity"].dropna().values
        y_v = aco_f["airflow_resistivity"].dropna().values
        idx = aco_f["porosity"].dropna().index.intersection(aco_f["airflow_resistivity"].dropna().index)
        if len(idx) >= 3:
            xv = aco_f.loc[idx, "porosity"].values
            yv = np.log(aco_f.loc[idx, "airflow_resistivity"].values + 1)
            z = np.polyfit(xv, yv, 1)
            xl = np.linspace(xv.min(), xv.max(), 80)
            yl = np.exp(np.polyval(z, xl))
            fig_res.add_trace(go.Scatter(
                x=xl, y=yl, mode="lines", name="Tendance",
                line=dict(color="#0F172A", width=2, dash="dash"),
            ))
    fig_res.update_layout(
        **PLOT_LAYOUT,
        xaxis_title="Porosité",
        yaxis_title="Résistivité σ (Pa·s/m²)",
        yaxis_type="log",
        legend=dict(orientation="h", y=1.05, x=0, font_size=11),
    )

    return kpis_filled, fig_diam, fig_len, fig_ori, fig_curv, fig_ca, fig_dp, fig_abs, fig_res


# ── Reset filtres ──────────────────────────────────────────────────────────────
@app.callback(
    Output("filter-material", "value"),
    Output("filter-batch",    "value"),
    Input("btn-reset", "n_clicks"),
    prevent_initial_call=True,
)
def reset_filters(_):
    return None, None


if __name__ == "__main__":
    PORT  = int(os.environ.get("PORT", 8050))
    DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=PORT, debug=DEBUG)
