"""
FiberScope — Dashboard Microtomographie Fibres
Projet E4 MSME

COMPATIBILITÉ DONNÉES RÉELLES
══════════════════════════════
Quand vous remplacez les CSV simulés par les vraies données, vérifiez que :

  data/samples.csv  — une ligne par échantillon
    colonnes requises : sample_id, material, batch, porosity,
                        contact_density, quality_score
    colonnes optionnelles : fiber_count, contact_count, volume_mm3,
                            mean_diameter_um, mean_length_um, etc.

  data/fibers.csv   — une ligne par fibre détectée
    colonnes requises : fiber_id, sample_id, diameter_um, length_um,
                        orientation_theta, curvature

  data/contacts.csv — une ligne par contact fibre-fibre
    colonnes requises : contact_id, sample_id, contact_area_um2

  data/acoustic_thermal.csv — une ligne par échantillon avec mesures acoustiques
    colonnes requises : sample_id, porosity, airflow_resistivity,
                        absorption_250hz, absorption_500hz, absorption_1000hz,
                        absorption_2000hz, absorption_4000hz

Si une colonne est absente, le graphique correspondant affichera un message
explicatif plutôt que de faire planter l'application.
"""

import os
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# ─── Chargement des données ───────────────────────────────────────────────────
BASE = os.path.dirname(__file__)

def _load(filename):
    path = os.path.join(BASE, "data", filename)
    if not os.path.exists(path):
        return pd.DataFrame()
    return pd.read_csv(path)

samples  = _load("samples.csv")
fibers   = _load("fibers.csv")
contacts = _load("contacts.csv")
acoustic = _load("acoustic_thermal.csv")

def _has(df, *cols):
    """Retourne True si toutes les colonnes sont présentes dans le DataFrame."""
    return all(c in df.columns for c in cols)

# Enrichissement : matériau + lot sur chaque fibre / contact
if _has(samples, "sample_id", "material", "batch"):
    _meta = samples[["sample_id", "material", "batch"]]
    if not fibers.empty and _has(fibers, "sample_id"):
        fibers = fibers.merge(_meta, on="sample_id", how="left")
    if not contacts.empty and _has(contacts, "sample_id"):
        contacts = contacts.merge(_meta, on="sample_id", how="left")
    if not acoustic.empty and _has(acoustic, "sample_id"):
        acoustic = acoustic.merge(_meta, on="sample_id", how="left")

MATERIALS = sorted(samples["material"].unique().tolist()) if _has(samples, "material") else []
BATCHES   = sorted(samples["batch"].unique().tolist()) if _has(samples, "batch") else []

# ─── Palette de couleurs ──────────────────────────────────────────────────────
# Ajoutez ici vos matériaux réels avec une couleur hexadécimale.
MAT_COLORS = {
    "Nylon":       "#3B82F6",
    "Carbone":     "#EF4444",
    "Verre":       "#22C55E",
    "Cuivre":      "#F59E0B",
    "PET recyclé": "#8B5CF6",
    "Chanvre":     "#10B981",
}
# Couleur de secours si le matériau n'est pas dans le dictionnaire ci-dessus
FALLBACK_COLORS = ["#3B82F6","#EF4444","#22C55E","#F59E0B","#8B5CF6","#10B981",
                   "#F97316","#06B6D4","#EC4899","#84CC16"]

def mat_color(mat, idx=0):
    return MAT_COLORS.get(mat, FALLBACK_COLORS[idx % len(FALLBACK_COLORS)])

# ─── Constantes de style ──────────────────────────────────────────────────────
PLOT_CONFIG = {
    "displayModeBar": "hover",   # barre d'outils affichée au survol (zoom, export PNG…)
    "responsive": True,
    "modeBarButtonsToRemove": ["select2d", "lasso2d", "autoScale2d"],
    "displaylogo": False,
    "toImageButtonOptions": {"format": "png", "scale": 2},
}

PLOT_LAYOUT = dict(
    paper_bgcolor="white",
    plot_bgcolor="#F8FAFC",
    font=dict(family="Inter, system-ui, sans-serif", size=12, color="#334155"),
    margin=dict(l=60, r=20, t=30, b=55),
    hoverlabel=dict(bgcolor="white", bordercolor="#E2E8F0", font_size=12),
)

# ─── App ──────────────────────────────────────────────────────────────────────
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY],
    title="FiberScope — MSME",
    suppress_callback_exceptions=True,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
server = app.server

# ─── Composants réutilisables ─────────────────────────────────────────────────

def empty_notice(message):
    """Affichage quand les données sont absentes ou incomplètes."""
    return html.Div([
        html.P("Données non disponibles", style={"fontWeight": 600, "color": "#94A3B8"}),
        html.P(message, style={"fontSize": "12px", "color": "#CBD5E1"}),
    ], style={"textAlign": "center", "padding": "60px 20px"})


def section_header(title, subtitle, color="#2563EB"):
    return html.Div(className="my-4 px-3", children=[
        html.Div(style={
            "width": "40px", "height": "4px",
            "backgroundColor": color, "borderRadius": "2px",
            "margin": "0 auto 10px auto",
        }),
        html.H4(title, style={
            "textAlign": "center", "color": "#0F172A",
            "fontWeight": 700, "fontSize": "20px", "marginBottom": "8px",
        }),
        html.P(subtitle, style={
            "textAlign": "center", "color": "#64748B",
            "fontSize": "13px", "maxWidth": "740px",
            "margin": "0 auto", "lineHeight": "1.7",
        }),
    ])


def graph_card(graph_id, title, description, read_guide, height="300px", col_width=6):
    return dbc.Col(dbc.Card(style={
        "borderRadius": "12px", "border": "1px solid #E2E8F0",
        "boxShadow": "0 2px 8px rgba(15,23,42,0.06)", "height": "100%",
    }, children=[
        dbc.CardBody(style={"padding": "18px"}, children=[
            html.H6(title, style={
                "fontWeight": 700, "color": "#0F172A",
                "marginBottom": "5px", "fontSize": "14px",
            }),
            html.P(description, style={
                "fontSize": "12px", "color": "#64748B",
                "marginBottom": "8px", "lineHeight": "1.55",
            }),
            html.Div([
                html.Span("Comment lire ce graphique : ", style={
                    "fontWeight": 700, "fontSize": "11px", "color": "#475569",
                }),
                html.Span(read_guide, style={
                    "fontSize": "11px", "color": "#64748B",
                }),
            ], style={
                "backgroundColor": "#F1F5F9",
                "borderLeft": "3px solid #CBD5E1",
                "padding": "7px 11px", "borderRadius": "0 6px 6px 0",
                "marginBottom": "12px",
            }),
            dcc.Graph(id=graph_id, config=PLOT_CONFIG, style={"height": height}),
        ])
    ]), md=col_width, className="mb-3")


def legend_dot(mat, idx):
    return html.Span([
        html.Span(style={
            "display": "inline-block",
            "width": "10px", "height": "10px",
            "borderRadius": "50%",
            "backgroundColor": mat_color(mat, idx),
            "marginRight": "5px",
        }),
        html.Span(mat, style={"fontSize": "12px", "color": "#475569"}),
    ], style={"marginRight": "14px", "whiteSpace": "nowrap"})


# ─── Layout ───────────────────────────────────────────────────────────────────
app.layout = dbc.Container(fluid=True, style={"backgroundColor": "#F8FAFC", "minHeight": "100vh"}, children=[

    # ── HEADER ──────────────────────────────────────────────────────────────
    html.Div(style={
        "background": "linear-gradient(135deg, #0F172A 0%, #1E3A5F 50%, #2563EB 100%)",
        "padding": "40px 24px 36px 24px",
        "textAlign": "center",
    }, children=[
        html.Div("PROJET E4 — MSME", style={
            "color": "#60A5FA", "fontSize": "11px", "fontWeight": 700,
            "letterSpacing": "0.15em", "textTransform": "uppercase", "marginBottom": "10px",
        }),
        html.H1("FiberScope", style={
            "color": "white", "fontWeight": 800,
            "fontSize": "40px", "letterSpacing": "-1px", "marginBottom": "10px",
        }),
        html.P(
            "Caractérisation morphologique des réseaux fibreux par microtomographie X",
            style={"color": "#BAE6FD", "fontSize": "15px", "marginBottom": "14px", "fontWeight": 400}
        ),
        html.P(
            "Ce tableau de bord permet d'explorer les propriétés géométriques des fibres "
            "(diamètre, longueur, orientation, courbure) et leurs liaisons (contacts fibre-fibre), "
            "mesurées dans des volumes 3D par scanner X. Il met également en regard ces données "
            "structurelles avec les propriétés d'absorption acoustique des matériaux.",
            style={
                "color": "#93C5FD", "fontSize": "13px", "maxWidth": "680px",
                "margin": "0 auto", "lineHeight": "1.75",
            }
        ),
        # Légende matériaux
        html.Div([legend_dot(m, i) for i, m in enumerate(MATERIALS)], style={
            "marginTop": "20px", "display": "flex", "flexWrap": "wrap",
            "justifyContent": "center", "gap": "4px",
        }) if MATERIALS else html.Span(),
    ]),

    # ── FILTRES ─────────────────────────────────────────────────────────────
    dbc.Row(className="mt-4 mb-2 px-3", children=[
        dbc.Col(dbc.Card(style={
            "borderRadius": "12px", "border": "1px solid #E2E8F0",
            "boxShadow": "0 2px 6px rgba(0,0,0,0.05)",
        }, children=[
            dbc.CardBody(style={"padding": "16px 20px"}, children=[
                html.P(
                    "Filtrez les données par matériau et/ou par lot de fabrication. "
                    "Tous les graphiques et indicateurs se mettent à jour instantanément.",
                    style={"fontSize": "12px", "color": "#64748B", "marginBottom": "14px"}
                ),
                dbc.Row([
                    dbc.Col([
                        html.Label("Matériau", style={
                            "fontWeight": 700, "fontSize": "12px",
                            "color": "#334155", "marginBottom": "5px", "display": "block",
                        }),
                        dcc.Dropdown(
                            id="filter-material",
                            options=[{"label": m, "value": m} for m in MATERIALS],
                            multi=True,
                            placeholder="Tous les matériaux",
                            clearable=True,
                            style={"fontSize": "13px"},
                        )
                    ], md=5),
                    dbc.Col([
                        html.Label("Lot de fabrication", style={
                            "fontWeight": 700, "fontSize": "12px",
                            "color": "#334155", "marginBottom": "5px", "display": "block",
                        }),
                        dcc.Dropdown(
                            id="filter-batch",
                            options=[{"label": b, "value": b} for b in BATCHES],
                            multi=True,
                            placeholder="Tous les lots",
                            clearable=True,
                            style={"fontSize": "13px"},
                        )
                    ], md=4),
                    dbc.Col(className="d-flex align-items-end", children=[
                        dbc.Button(
                            "Tout afficher",
                            id="btn-reset",
                            outline=True,
                            style={
                                "border": "1px solid #CBD5E1", "color": "#475569",
                                "fontWeight": 600, "fontSize": "12px", "width": "100%",
                                "borderRadius": "8px",
                            }
                        )
                    ], md=3),
                ]),
                # Résumé de la sélection
                html.Div(id="selection-summary", style={"marginTop": "12px"}),
            ])
        ]))
    ]),

    # ── VUE D'ENSEMBLE — KPIs ────────────────────────────────────────────────
    dbc.Row(className="mt-3 mb-1 px-3", children=[
        dbc.Col(html.Div([
            html.H5("Vue d'ensemble", style={
                "textAlign": "center", "color": "#0F172A",
                "fontWeight": 700, "marginBottom": "4px",
            }),
            html.P(
                "Indicateurs clés résumant les données de la sélection en cours.",
                style={"textAlign": "center", "color": "#94A3B8", "fontSize": "12px", "marginBottom": "16px"}
            ),
        ]))
    ]),
    dbc.Row(id="row-kpis", className="px-3 mb-2"),

    # ── SECTION 1 : Morphologie ──────────────────────────────────────────────
    section_header(
        "Morphologie des fibres",
        "La microtomographie X permet d'observer et de mesurer chaque fibre individuellement "
        "dans un volume 3D. Ces graphiques montrent comment les dimensions (diamètre, longueur), "
        "la forme (courbure) et l'orientation des fibres varient selon le matériau. "
        "Ces paramètres morphologiques gouvernent directement les propriétés mécaniques et acoustiques.",
        color="#2563EB"
    ),
    dbc.Row(className="px-3", children=[
        graph_card(
            "graph-diameter",
            "Diamètre des fibres par matériau (µm)",
            "Le diamètre d'une fibre est mesuré sur sa section transversale. "
            "Il influe directement sur la surface de contact disponible entre fibres et sur la perméabilité du réseau fibreux. "
            "Des fibres fines créent un réseau plus dense avec plus de connexions par unité de volume.",
            "Chaque boîte couvre 50 % des fibres d'un matériau (du 1er au 3e quartile). "
            "La ligne centrale est la médiane. Les points isolés sont des fibres atypiques. "
            "Cliquez sur un matériau dans la légende pour le masquer. "
            "Survolez une boîte pour voir les statistiques détaillées.",
            height="310px",
        ),
        graph_card(
            "graph-length",
            "Longueur des fibres par matériau (µm)",
            "La longueur détermine la capacité d'une fibre à former plusieurs liaisons avec ses voisines "
            "et sa contribution à l'enchevêtrement du réseau. Des fibres longues créent un réseau plus rigide "
            "et généralement plus performant acoustiquement.",
            "Même lecture que le diamètre. Une grande dispersion (boîte haute) signale une variabilité "
            "de fabrication importante — ce qui peut affecter la reproductibilité des propriétés acoustiques.",
            height="310px",
        ),
    ]),
    dbc.Row(className="px-3", children=[
        graph_card(
            "graph-orientation",
            "Distribution des orientations angulaires θ",
            "L'angle θ mesure l'inclinaison de chaque fibre par rapport au plan horizontal de l'échantillon. "
            "θ = 0° : fibre couchée dans le plan. θ = 90° : fibre perpendiculaire au plan (debout). "
            "Cette distribution caractérise l'anisotropie du matériau.",
            "Un pic marqué près de 0° indique un matériau plan (fibres alignées horizontalement, typique des non-tissés). "
            "Une courbe plate signifie que les fibres pointent dans toutes les directions (matériau isotrope). "
            "Cliquez sur un matériau dans la légende pour le masquer ou l'isoler.",
            height="310px",
        ),
        graph_card(
            "graph-curvature",
            "Courbure des fibres par matériau (κ × 10³ mm⁻¹)",
            "La courbure κ = 1/R mesure l'écart d'une fibre par rapport à une droite parfaite. "
            "Une fibre rectiligne a κ ≈ 0. Plus κ est grand, plus la fibre est ondulée ou torsadée. "
            "La courbure modifie la surface effective, l'enchevêtrement et la tortuosité des pores.",
            "Valeurs proches de 0 = fibres rectilignes (carbone, verre). "
            "Valeurs élevées = fibres ondulées (naturelles, recyclées). "
            "Une forte courbure peut augmenter la tortuosité des chemins acoustiques, ce qui améliore l'absorption.",
            height="310px",
        ),
    ]),

    # ── SECTION 2 : Liaisons ─────────────────────────────────────────────────
    section_header(
        "Liaisons inter-fibres",
        "Quand deux fibres se croisent dans le volume 3D, elles forment une liaison. "
        "Le nombre et la surface de ces contacts définissent la cohésion du réseau : "
        "ils gouvernent la rigidité mécanique mais aussi la résistance au passage de l'air, "
        "qui est le mécanisme principal d'absorption acoustique dans les matériaux fibreux.",
        color="#16A34A"
    ),
    dbc.Row(className="px-3", children=[
        graph_card(
            "graph-contact-area",
            "Distribution des aires de contact fibre-fibre (µm²)",
            "La surface de contact entre deux fibres détermine la solidité de leur liaison. "
            "Une grande aire = jonction rigide. Une petite aire = liaison plus souple. "
            "Cette surface dépend du diamètre des fibres, de l'angle de croisement et de la forme de leur section.",
            "La grande majorité des contacts ont une petite surface (pic à gauche). "
            "La queue étendue vers la droite représente de rares jonctions larges "
            "(fibres qui se croisent à faible angle, longue zone de contact). "
            "Survolez les barres pour voir les effectifs précis.",
            height="310px",
        ),
        graph_card(
            "graph-density-porosity",
            "Densité de connexions vs Porosité",
            "La densité de connexions (nombre de liaisons par mm³) est comparée à la porosité "
            "(fraction de vide dans le matériau). Ces deux grandeurs sont naturellement liées : "
            "un matériau dense (peu poreux) contient plus de fibres proches, donc plus de contacts.",
            "Attendez-vous à une tendance décroissante de gauche à droite. "
            "Les points qui s'écartent de cette tendance sont informatifs : "
            "des fibres très fines peuvent créer beaucoup de connexions même à forte porosité. "
            "Survolez un point pour voir l'identifiant de l'échantillon.",
            height="310px",
        ),
    ]),

    # ── SECTION 3 : Acoustique ───────────────────────────────────────────────
    section_header(
        "Propriétés acoustiques",
        "Ces mesures expérimentales quantifient comment chaque matériau absorbe le son. "
        "Les données proviennent des échantillons pour lesquels des mesures acoustiques ont été réalisées. "
        "L'objectif est de relier la micro-structure (porosité, diamètre) à la performance acoustique "
        "— ce lien est la clé pour concevoir des matériaux légers et performants.",
        color="#D97706"
    ),
    dbc.Row(className="px-3", children=[
        graph_card(
            "graph-absorption",
            "Coefficient d'absorption acoustique selon la fréquence",
            "Le coefficient α varie entre 0 (le son est entièrement réfléchi) et 1 (entièrement absorbé). "
            "Chaque courbe représente un échantillon mesuré. "
            "Les matériaux fibreux absorbent généralement mieux les hautes fréquences (voix, moteur) "
            "que les basses (rumble, vibrations de structure).",
            "Un α élevé dès 500 Hz est excellent pour les applications transport. "
            "La courbe en pointillés noirs est la médiane de tous les échantillons affichés — "
            "elle représente le comportement 'typique' du jeu de données. "
            "Cliquez sur un échantillon dans la légende pour l'isoler.",
            height="340px",
            col_width=7,
        ),
        graph_card(
            "graph-resistivity",
            "Résistivité au flux d'air vs Porosité",
            "La résistivité au flux σ (Pa·s/m²) mesure combien le matériau s'oppose au passage de l'air. "
            "C'est le paramètre acoustique le plus important pour les absorbants fibreux. "
            "Un matériau dense (porosité faible) bloque davantage l'air et a donc une résistivité plus élevée.",
            "L'axe vertical est en échelle logarithmique (les valeurs couvrent plusieurs ordres de grandeur). "
            "Un bon absorbant acoustique se situe dans une plage optimale : "
            "σ trop faible → le son traverse sans être atténué. "
            "σ trop élevée → le son est réfléchi en surface. "
            "La droite pointillée montre la tendance générale.",
            height="340px",
            col_width=5,
        ),
    ]),

    # ── FOOTER ──────────────────────────────────────────────────────────────
    html.Div(style={"textAlign": "center", "padding": "24px", "color": "#94A3B8", "fontSize": "12px"}, children=[
        html.Hr(style={"borderColor": "#E2E8F0", "marginBottom": "12px"}),
        html.P("FiberScope — Projet E4 MSME — Analyse par microtomographie X", style={"margin": 0}),
    ]),
])


# ─── Utilitaires ──────────────────────────────────────────────────────────────

def _filter(mat_sel, bat_sel):
    if samples.empty:
        return [], pd.DataFrame()
    mask = pd.Series([True] * len(samples))
    if mat_sel:
        mask &= samples["material"].isin(mat_sel)
    if bat_sel:
        mask &= samples["batch"].isin(bat_sel)
    filtered = samples[mask]
    return filtered["sample_id"].tolist(), filtered


def _boxplot(df, y_col, title_y=""):
    if df.empty or y_col not in df.columns or "material" not in df.columns:
        return go.Figure(layout=dict(**PLOT_LAYOUT, annotations=[dict(
            text="Colonne non disponible dans les données",
            x=0.5, y=0.5, xref="paper", yref="paper",
            showarrow=False, font_color="#94A3B8", font_size=13,
        )]))
    fig = go.Figure()
    for i, mat in enumerate(sorted(df["material"].dropna().unique())):
        vals = df[df["material"] == mat][y_col].dropna()
        if len(vals) == 0:
            continue
        fig.add_trace(go.Box(
            y=vals, name=mat,
            marker_color=mat_color(mat, i),
            boxpoints="outliers",
            line_width=1.8, marker_size=3,
            hovertemplate=(
                f"<b>{mat}</b><br>"
                "Médiane : %{median:.1f}<br>"
                "Q1–Q3 : %{q1:.1f} – %{q3:.1f}<br>"
                "Min / Max : %{lowerfence:.1f} / %{upperfence:.1f}"
                "<extra></extra>"
            ),
        ))
    fig.update_layout(**PLOT_LAYOUT, yaxis_title=title_y, showlegend=False)
    return fig


# ─── Callback principal ───────────────────────────────────────────────────────
@app.callback(
    Output("selection-summary",      "children"),
    Output("row-kpis",               "children"),
    Output("graph-diameter",         "figure"),
    Output("graph-length",           "figure"),
    Output("graph-orientation",      "figure"),
    Output("graph-curvature",        "figure"),
    Output("graph-contact-area",     "figure"),
    Output("graph-density-porosity", "figure"),
    Output("graph-absorption",       "figure"),
    Output("graph-resistivity",      "figure"),
    Input("filter-material", "value"),
    Input("filter-batch",    "value"),
)
def update_all(mat_sel, bat_sel):
    ids, samp_f = _filter(mat_sel, bat_sel)
    fib_f = fibers[fibers["sample_id"].isin(ids)] if not fibers.empty and "sample_id" in fibers.columns else pd.DataFrame()
    con_f = contacts[contacts["sample_id"].isin(ids)] if not contacts.empty and "sample_id" in contacts.columns else pd.DataFrame()
    aco_f = acoustic[acoustic["sample_id"].isin(ids)] if not acoustic.empty and "sample_id" in acoustic.columns else pd.DataFrame()

    n_samples  = len(samp_f)
    n_fibers   = len(fib_f)
    n_contacts = len(con_f)
    n_acoustic = len(aco_f)

    # ── Résumé de sélection ──────────────────────────────────────────────────
    summary = html.Div([
        html.Span(f"{n_samples} échantillon{'s' if n_samples > 1 else ''}",
                  style={"fontWeight": 700, "color": "#2563EB"}),
        html.Span("  ·  ", style={"color": "#CBD5E1"}),
        html.Span(f"{n_fibers:,} fibres",
                  style={"fontWeight": 600, "color": "#8B5CF6"}),
        html.Span("  ·  ", style={"color": "#CBD5E1"}),
        html.Span(f"{n_contacts:,} contacts",
                  style={"fontWeight": 600, "color": "#22C55E"}),
        html.Span("  ·  ", style={"color": "#CBD5E1"}),
        html.Span(f"{n_acoustic} éch. acoustiques",
                  style={"fontWeight": 600, "color": "#D97706"}),
    ], style={"fontSize": "13px", "padding": "6px 0 0 0"})

    # ── KPIs ────────────────────────────────────────────────────────────────
    mean_por  = samp_f["porosity"].mean() if _has(samp_f, "porosity") and n_samples else None
    mean_qual = samp_f["quality_score"].mean() if _has(samp_f, "quality_score") and n_samples else None

    def kpi_col(label, value, expl, color):
        return dbc.Col(dbc.Card(style={
            "borderRadius": "12px",
            "borderTop": f"4px solid {color}",
            "border": "1px solid #E2E8F0",
            "boxShadow": "0 2px 6px rgba(0,0,0,0.04)",
        }, children=[
            dbc.CardBody(style={"padding": "16px"}, children=[
                html.P(label, style={
                    "fontSize": "10px", "fontWeight": 700, "color": "#64748B",
                    "textTransform": "uppercase", "letterSpacing": "0.08em", "marginBottom": "5px",
                }),
                html.H3(value, style={
                    "fontSize": "26px", "fontWeight": 800,
                    "color": color, "marginBottom": "4px",
                }),
                html.P(expl, style={"fontSize": "11px", "color": "#94A3B8", "margin": 0, "lineHeight": "1.4"}),
            ])
        ]), md=True, className="mb-3")

    kpis = [
        kpi_col("Échantillons",      str(n_samples),
                "Volumes 3D analysés par microtomographie", "#2563EB"),
        kpi_col("Fibres détectées",  f"{n_fibers:,}",
                "Fibres individuelles segmentées dans les volumes", "#8B5CF6"),
        kpi_col("Contacts fibre-fibre", f"{n_contacts:,}",
                "Liaisons entre fibres identifiées dans le réseau", "#22C55E"),
        kpi_col("Porosité moyenne",
                f"{mean_por:.2f}" if mean_por is not None else "—",
                "Fraction de vide dans le matériau (0 = dense, 1 = creux)", "#F59E0B"),
        kpi_col("Score qualité",
                f"{mean_qual:.1f} / 5" if mean_qual is not None else "—",
                "Qualité de la reconstruction 3D (segmentation)", "#EF4444"),
    ]

    # ── Diamètre ────────────────────────────────────────────────────────────
    fig_diam = _boxplot(fib_f, "diameter_um", title_y="Diamètre (µm)")

    # ── Longueur ────────────────────────────────────────────────────────────
    fig_len = _boxplot(fib_f, "length_um", title_y="Longueur (µm)")

    # ── Orientations θ ─────────────────────────────────────────────────────
    fig_ori = go.Figure()
    if not fib_f.empty and _has(fib_f, "orientation_theta", "material"):
        for i, mat in enumerate(sorted(fib_f["material"].dropna().unique())):
            vals = fib_f[fib_f["material"] == mat]["orientation_theta"].dropna()
            if len(vals) == 0:
                continue
            fig_ori.add_trace(go.Histogram(
                x=vals, name=mat,
                marker_color=mat_color(mat, i),
                opacity=0.72, nbinsx=18, histnorm="percent",
                hovertemplate=f"<b>{mat}</b><br>θ = %{{x:.0f}}°<br>%{{y:.1f}} % des fibres<extra></extra>",
            ))
    fig_ori.update_layout(
        **PLOT_LAYOUT, barmode="overlay",
        xaxis_title="θ (degrés)", yaxis_title="% des fibres",
        legend=dict(orientation="h", y=1.05, x=0, font_size=11, bgcolor="rgba(0,0,0,0)"),
    )

    # ── Courbure ────────────────────────────────────────────────────────────
    if not fib_f.empty and "curvature" in fib_f.columns:
        fib_curv = fib_f.copy()
        fib_curv["curvature_scaled"] = fib_curv["curvature"] * 1000
        fig_curv = _boxplot(fib_curv, "curvature_scaled", title_y="κ × 10³ (mm⁻¹)")
    else:
        fig_curv = go.Figure(layout=dict(**PLOT_LAYOUT, annotations=[dict(
            text="Colonne 'curvature' non disponible",
            x=0.5, y=0.5, xref="paper", yref="paper",
            showarrow=False, font_color="#94A3B8",
        )]))

    # ── Aires de contact ────────────────────────────────────────────────────
    fig_ca = go.Figure()
    if not con_f.empty and _has(con_f, "contact_area_um2", "material"):
        for i, mat in enumerate(sorted(con_f["material"].dropna().unique())):
            vals = con_f[con_f["material"] == mat]["contact_area_um2"].dropna()
            if len(vals) == 0:
                continue
            p99 = vals.quantile(0.99)
            vals = vals[vals <= p99]
            fig_ca.add_trace(go.Histogram(
                x=vals, name=mat, marker_color=mat_color(mat, i),
                opacity=0.72, nbinsx=30, histnorm="percent",
                hovertemplate=f"<b>{mat}</b><br>%{{x:.0f}} µm²<br>%{{y:.1f}} % des contacts<extra></extra>",
            ))
    fig_ca.update_layout(
        **PLOT_LAYOUT, barmode="overlay",
        xaxis_title="Aire de contact (µm²)", yaxis_title="% des contacts",
        legend=dict(orientation="h", y=1.05, x=0, font_size=11, bgcolor="rgba(0,0,0,0)"),
    )

    # ── Densité connexions vs Porosité ──────────────────────────────────────
    fig_dp = go.Figure()
    if not samp_f.empty and _has(samp_f, "porosity", "contact_density", "material"):
        for i, mat in enumerate(sorted(samp_f["material"].dropna().unique())):
            sub = samp_f[samp_f["material"] == mat]
            fig_dp.add_trace(go.Scatter(
                x=sub["porosity"], y=sub["contact_density"],
                mode="markers", name=mat,
                marker=dict(
                    color=mat_color(mat, i), size=11,
                    line=dict(width=1.5, color="white"),
                ),
                text=sub["sample_id"] if "sample_id" in sub.columns else None,
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "Porosité : %{x:.3f}<br>"
                    "Densité de connexions : %{y:.1f} N/mm³"
                    "<extra></extra>"
                ),
            ))
    fig_dp.update_layout(
        **PLOT_LAYOUT,
        xaxis_title="Porosité",
        yaxis_title="Densité de connexions (N/mm³)",
        legend=dict(orientation="h", y=1.05, x=0, font_size=11, bgcolor="rgba(0,0,0,0)"),
    )

    # ── Absorption acoustique ────────────────────────────────────────────────
    freqs     = [250, 500, 1000, 2000, 4000]
    freq_cols = ["absorption_250hz","absorption_500hz","absorption_1000hz",
                 "absorption_2000hz","absorption_4000hz"]
    fig_abs = go.Figure()
    if not aco_f.empty and all(c in aco_f.columns for c in freq_cols):
        shown = 0
        for i, (_, row) in enumerate(aco_f.iterrows()):
            vals = [row[c] for c in freq_cols]
            if any(pd.isna(v) for v in vals):
                continue
            mat = row.get("material", "—")
            sid = row.get("sample_id", f"#{i}")
            fig_abs.add_trace(go.Scatter(
                x=freqs, y=vals,
                mode="lines+markers",
                name=f"{sid} ({mat})",
                line=dict(color=mat_color(mat, i), width=2),
                marker=dict(size=5),
                opacity=0.82,
                hovertemplate=f"<b>{sid}</b><br>%{{x}} Hz → α = %{{y:.3f}}<extra></extra>",
            ))
            shown += 1
        # Médiane
        if shown > 1:
            medians = [aco_f[c].dropna().median() for c in freq_cols]
            fig_abs.add_trace(go.Scatter(
                x=freqs, y=medians, mode="lines",
                name="Médiane globale",
                line=dict(color="#0F172A", width=3, dash="dot"),
                hovertemplate="Médiane<br>%{x} Hz → α = %{y:.3f}<extra></extra>",
            ))
    fig_abs.update_layout(
        **PLOT_LAYOUT,
        xaxis=dict(
            title="Fréquence (Hz)",
            tickvals=freqs,
            ticktext=["250 Hz","500 Hz","1 kHz","2 kHz","4 kHz"],
        ),
        yaxis=dict(title="Coefficient d'absorption α", range=[0, 1.05]),
        legend=dict(orientation="v", x=1.01, y=1, font_size=10, bgcolor="rgba(0,0,0,0)"),
    )

    # ── Résistivité vs Porosité ─────────────────────────────────────────────
    fig_res = go.Figure()
    if not aco_f.empty and _has(aco_f, "porosity", "airflow_resistivity", "material"):
        for i, mat in enumerate(sorted(aco_f["material"].dropna().unique())):
            sub = aco_f[aco_f["material"] == mat].dropna(subset=["porosity","airflow_resistivity"])
            if sub.empty:
                continue
            fig_res.add_trace(go.Scatter(
                x=sub["porosity"], y=sub["airflow_resistivity"],
                mode="markers", name=mat,
                marker=dict(
                    color=mat_color(mat, i), size=12,
                    line=dict(width=1.5, color="white"),
                ),
                text=sub["sample_id"] if "sample_id" in sub.columns else None,
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "Porosité : %{x:.3f}<br>"
                    "Résistivité σ : %{y:,.0f} Pa·s/m²"
                    "<extra></extra>"
                ),
            ))
        # Courbe de tendance
        valid = aco_f.dropna(subset=["porosity","airflow_resistivity"])
        if len(valid) >= 3:
            xv = valid["porosity"].values
            yv = np.log(valid["airflow_resistivity"].values + 1)
            z  = np.polyfit(xv, yv, 1)
            xl = np.linspace(xv.min(), xv.max(), 80)
            fig_res.add_trace(go.Scatter(
                x=xl, y=np.exp(np.polyval(z, xl)),
                mode="lines", name="Tendance log-linéaire",
                line=dict(color="#0F172A", width=2, dash="dash"),
                hovertemplate="Tendance → σ = %{y:,.0f} Pa·s/m²<extra></extra>",
            ))
    fig_res.update_layout(
        **PLOT_LAYOUT,
        xaxis_title="Porosité",
        yaxis_title="Résistivité σ (Pa·s/m²)",
        yaxis_type="log",
        legend=dict(orientation="h", y=1.05, x=0, font_size=11, bgcolor="rgba(0,0,0,0)"),
    )

    return summary, kpis, fig_diam, fig_len, fig_ori, fig_curv, fig_ca, fig_dp, fig_abs, fig_res


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
