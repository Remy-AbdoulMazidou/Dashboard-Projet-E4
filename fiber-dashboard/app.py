"""
FiberScope — Dashboard Microtomographie Fibres
Projet E4 ESIEE Paris

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
                        absorption_250hz .. absorption_4000hz

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
    return pd.read_csv(path) if os.path.exists(path) else pd.DataFrame()

samples  = _load("samples.csv")
fibers   = _load("fibers.csv")
contacts = _load("contacts.csv")
acoustic = _load("acoustic_thermal.csv")

def _has(df, *cols):
    return all(c in df.columns for c in cols)

if _has(samples, "sample_id", "material", "batch"):
    _meta = samples[["sample_id", "material", "batch"]]
    for df_name, df_obj in [("fibers", fibers), ("contacts", contacts), ("acoustic", acoustic)]:
        if not df_obj.empty and "sample_id" in df_obj.columns:
            if df_name == "fibers":
                fibers   = df_obj.merge(_meta, on="sample_id", how="left")
            elif df_name == "contacts":
                contacts = df_obj.merge(_meta, on="sample_id", how="left")
            else:
                acoustic = df_obj.merge(_meta, on="sample_id", how="left")

MATERIALS = sorted(samples["material"].unique().tolist()) if _has(samples, "material") else []
BATCHES   = sorted(samples["batch"].unique().tolist()) if _has(samples, "batch") else []

# ─── Palette ──────────────────────────────────────────────────────────────────
MAT_COLORS = {
    "Nylon":       "#3B82F6",
    "Carbone":     "#EF4444",
    "Verre":       "#22C55E",
    "Cuivre":      "#F59E0B",
    "PET recyclé": "#8B5CF6",
    "Chanvre":     "#10B981",
}
FALLBACK = ["#3B82F6","#EF4444","#22C55E","#F59E0B","#8B5CF6","#10B981",
            "#F97316","#06B6D4","#EC4899","#84CC16"]

def mat_color(mat, idx=0):
    return MAT_COLORS.get(mat, FALLBACK[idx % len(FALLBACK)])

# ─── Couleurs des onglets ──────────────────────────────────────────────────────
TABS = {
    "overview":   {"bg": "#1D4ED8", "light": "#EFF6FF", "border": "#BFDBFE", "label": "Vue d'ensemble"},
    "morphology": {"bg": "#6D28D9", "light": "#F5F3FF", "border": "#DDD6FE", "label": "Morphologie des fibres"},
    "contacts":   {"bg": "#047857", "light": "#ECFDF5", "border": "#A7F3D0", "label": "Liaisons inter-fibres"},
    "acoustics":  {"bg": "#B45309", "light": "#FFFBEB", "border": "#FDE68A", "label": "Propriétés acoustiques"},
}

BASE_TAB = {
    "fontFamily": "Inter, system-ui, sans-serif",
    "fontWeight": 600,
    "fontSize":   "13px",
    "padding":    "11px 22px",
    "borderRadius": "10px 10px 0 0",
    "backgroundColor": "#F1F5F9",
    "color":      "#64748B",
    "border":     "1px solid #E2E8F0",
    "borderBottom": "none",
    "marginRight": "4px",
    "cursor":     "pointer",
}

def sel_tab(key):
    return {**BASE_TAB,
            "backgroundColor": TABS[key]["bg"],
            "color":           "white",
            "border":          f"1px solid {TABS[key]['bg']}",
            "boxShadow":       f"0 -3px 0 0 {TABS[key]['bg']} inset"}

# ─── Config & layout Plotly ───────────────────────────────────────────────────
PLOT_CONFIG = {
    "displayModeBar": "hover",
    "responsive": True,
    "modeBarButtonsToRemove": ["select2d", "lasso2d", "autoScale2d"],
    "displaylogo": False,
    "toImageButtonOptions": {"format": "png", "scale": 2},
}

PLOT_LAYOUT = dict(
    paper_bgcolor="white",
    plot_bgcolor="#F8FAFC",
    font=dict(family="Inter, system-ui, sans-serif", size=12, color="#334155"),
    margin=dict(l=70, r=24, t=32, b=60),
    hoverlabel=dict(bgcolor="white", bordercolor="#E2E8F0", font_size=12),
)

AXIS_STYLE = dict(
    showgrid=True,  gridcolor="#E2E8F0",  gridwidth=1,
    zeroline=True,  zerolinecolor="#CBD5E1", zerolinewidth=1,
    showline=True,  linecolor="#CBD5E1",  linewidth=1,
    title_font=dict(size=13, color="#1E293B", family="Inter, system-ui, sans-serif"),
    tickfont=dict(size=11, color="#475569"),
)

def apply_grid(fig):
    fig.update_xaxes(**AXIS_STYLE)
    fig.update_yaxes(**AXIS_STYLE)
    return fig

# ─── App ──────────────────────────────────────────────────────────────────────
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.FLATLY,
        "https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap",
    ],
    title="FiberScope — ESIEE Paris",
    suppress_callback_exceptions=True,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
server = app.server

# ─── Composants ────────────────────────────────────────────────────────────────

def tab_banner(key, subtitle, description, bullets):
    c = TABS[key]
    return html.Div(style={
        "backgroundColor": c["light"],
        "border":          f"1px solid {c['border']}",
        "borderLeft":      f"5px solid {c['bg']}",
        "borderRadius":    "10px",
        "padding":         "20px 26px",
        "marginBottom":    "28px",
    }, children=[
        html.H5(c["label"], style={
            "color": c["bg"], "fontWeight": 800,
            "fontSize": "17px", "marginBottom": "4px",
            "letterSpacing": "-0.3px",
        }),
        html.P(subtitle, style={
            "color": "#1E293B", "fontWeight": 600,
            "fontSize": "13px", "marginBottom": "10px",
        }),
        html.P(description, style={
            "color": "#475569", "fontSize": "13px",
            "lineHeight": "1.75", "marginBottom": "10px",
        }),
        html.Ul([
            html.Li(b, style={"fontSize": "12px", "color": "#64748B", "marginBottom": "4px"})
            for b in bullets
        ], style={"paddingLeft": "18px", "margin": 0}),
    ])


def section_label(text, color="#1E293B", size="14px", weight=700, center=True, mb="18px"):
    return html.P(text, style={
        "fontWeight": weight, "fontSize": size, "color": color,
        "textAlign": "center" if center else "left",
        "marginBottom": mb, "letterSpacing": "-0.2px",
    })


def graph_card(graph_id, title, description, read_guide, height="310px", col_width=6, accent="#2563EB"):
    return dbc.Col(dbc.Card(style={
        "borderRadius": "12px",
        "border":       "1px solid #E2E8F0",
        "boxShadow":    "0 2px 10px rgba(15,23,42,0.06)",
        "height":       "100%",
    }, children=[
        dbc.CardBody(style={"padding": "20px 20px 16px 20px"}, children=[
            # Titre centré avec accent coloré
            html.Div(style={"textAlign": "center", "marginBottom": "10px"}, children=[
                html.Div(style={
                    "width": "28px", "height": "3px",
                    "backgroundColor": accent, "borderRadius": "2px",
                    "margin": "0 auto 8px auto",
                }),
                html.H6(title, style={
                    "fontWeight": 700, "color": "#0F172A",
                    "fontSize": "13.5px", "marginBottom": "0",
                }),
            ]),
            # Description du graphique
            html.P(description, style={
                "fontSize": "12px", "color": "#64748B",
                "lineHeight": "1.6", "marginBottom": "8px",
                "textAlign": "center",
            }),
            # Guide de lecture
            html.Div([
                html.Span("Comment lire ce graphique : ", style={
                    "fontWeight": 700, "fontSize": "11px", "color": "#334155",
                }),
                html.Span(read_guide, style={
                    "fontSize": "11px", "color": "#64748B",
                }),
            ], style={
                "backgroundColor": "#F1F5F9",
                "borderLeft":      f"3px solid {accent}",
                "padding":         "7px 11px",
                "borderRadius":    "0 6px 6px 0",
                "marginBottom":    "14px",
                "lineHeight":      "1.55",
            }),
            # Graphique
            dcc.Graph(id=graph_id, config=PLOT_CONFIG, style={"height": height}),
        ])
    ]), md=col_width, className="mb-4")


def kpi_card(label, value, expl, color):
    return dbc.Col(dbc.Card(style={
        "borderRadius":  "12px",
        "border":        "1px solid #E2E8F0",
        "borderTop":     f"4px solid {color}",
        "boxShadow":     "0 2px 8px rgba(15,23,42,0.05)",
    }, children=[
        dbc.CardBody(style={"padding": "18px 16px"}, children=[
            html.P(label, style={
                "fontSize": "10px", "fontWeight": 700,
                "color": "#94A3B8", "textTransform": "uppercase",
                "letterSpacing": "0.09em", "marginBottom": "6px",
            }),
            html.H3(value, style={
                "fontSize": "28px", "fontWeight": 800,
                "color": color, "marginBottom": "4px", "lineHeight": 1,
            }),
            html.P(expl, style={
                "fontSize": "11px", "color": "#94A3B8",
                "margin": 0, "lineHeight": "1.45",
            }),
        ])
    ]), md=True, className="mb-3")


# ─── Layout ───────────────────────────────────────────────────────────────────
app.layout = dbc.Container(fluid=True, style={
    "backgroundColor": "#F1F5F9",
    "minHeight": "100vh",
    "fontFamily": "Inter, system-ui, sans-serif",
}, children=[

    # ── HEADER ──────────────────────────────────────────────────────────────
    html.Div(style={
        "background":  "linear-gradient(135deg, #0A1628 0%, #0F2D5E 55%, #1D4ED8 100%)",
        "padding":     "44px 32px 38px 32px",
        "textAlign":   "center",
    }, children=[
        html.Div("ESIEE PARIS — PROJET E4", style={
            "color": "#60A5FA", "fontSize": "11px", "fontWeight": 700,
            "letterSpacing": "0.18em", "textTransform": "uppercase",
            "marginBottom": "12px",
        }),
        html.H1("FiberScope", style={
            "color": "white", "fontWeight": 800,
            "fontSize": "44px", "letterSpacing": "-2px",
            "marginBottom": "10px",
        }),
        html.P(
            "Caractérisation morphologique des réseaux fibreux par microtomographie X",
            style={"color": "#BAE6FD", "fontSize": "15px", "marginBottom": "20px"}
        ),
        # Légende matériaux — texte blanc lisible
        html.Div([
            html.Span([
                html.Span(style={
                    "display": "inline-block",
                    "width": "11px", "height": "11px",
                    "borderRadius": "50%",
                    "backgroundColor": mat_color(m, i),
                    "marginRight": "6px",
                    "verticalAlign": "middle",
                    "border": "2px solid rgba(255,255,255,0.4)",
                }),
                html.Span(m, style={
                    "fontSize": "12px",
                    "color": "white",          # texte blanc, visible sur fond sombre
                    "fontWeight": 600,
                    "verticalAlign": "middle",
                }),
            ], style={"marginRight": "16px", "whiteSpace": "nowrap"})
            for i, m in enumerate(MATERIALS)
        ], style={
            "display": "flex", "flexWrap": "wrap",
            "justifyContent": "center", "gap": "6px",
            "marginTop": "4px",
        }) if MATERIALS else html.Span(),
    ]),

    # ── FILTRES ──────────────────────────────────────────────────────────────
    dbc.Row(className="mt-4 mb-3 px-3", children=[
        dbc.Col(dbc.Card(style={
            "borderRadius": "12px",
            "border":       "1px solid #E2E8F0",
            "boxShadow":    "0 2px 6px rgba(0,0,0,0.04)",
            "backgroundColor": "white",
        }, children=[
            dbc.CardBody(style={"padding": "16px 20px"}, children=[
                html.P(
                    "Filtrez les données par matériau et par lot de fabrication. "
                    "Tous les graphiques et indicateurs se mettent à jour instantanément.",
                    style={"fontSize": "12px", "color": "#64748B", "marginBottom": "14px"},
                ),
                dbc.Row(align="end", children=[
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
                            style={"fontSize": "13px"},
                        ),
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
                            style={"fontSize": "13px"},
                        ),
                    ], md=4),
                    dbc.Col([
                        dbc.Button(
                            "Tout afficher",
                            id="btn-reset",
                            style={
                                "border":           "1px solid #CBD5E1",
                                "backgroundColor":  "white",
                                "color":            "#475569",
                                "fontWeight":       700,
                                "fontSize":         "12px",
                                "width":            "100%",
                                "borderRadius":     "8px",
                                "padding":          "9px 0",
                            },
                        )
                    ], md=3),
                ]),
            ]),
        ]))
    ]),

    # ── ONGLETS ──────────────────────────────────────────────────────────────
    html.Div(style={"padding": "0 16px"}, children=[
        dcc.Tabs(
            id="main-tabs",
            value="overview",
            style={"borderBottom": "2px solid #E2E8F0", "marginBottom": "0"},
            children=[
                dcc.Tab(
                    label=TABS["overview"]["label"],
                    value="overview",
                    style=BASE_TAB,
                    selected_style=sel_tab("overview"),
                    children=[
                        html.Div(style={"padding": "28px 0 12px 0"}, children=[
                            tab_banner(
                                "overview",
                                "Tableau de bord général de l'analyse microtomographique",
                                "Cette vue synthétise l'ensemble des données disponibles pour la sélection en cours. "
                                "Elle présente les indicateurs clés issus de l'analyse des volumes 3D : "
                                "nombre de fibres détectées, porosité, qualité de reconstruction, "
                                "et densité du réseau de contacts. "
                                "C'est le point de départ pour comprendre un échantillon avant d'explorer les détails.",
                                [
                                    "Échantillons : volumes 3D numérisés par microtomographie X (scanner de haute résolution).",
                                    "Fibres : éléments fibreux individuels segmentés algorithmiquement dans chaque volume.",
                                    "Contacts : points où deux fibres se croisent et se touchent dans le réseau 3D.",
                                    "Porosité : proportion de vide dans le matériau — un indicateur clé des performances acoustiques.",
                                    "Score qualité : évaluation de la netteté de la reconstruction 3D (segmentation).",
                                ],
                            ),
                            dbc.Row(id="row-kpis", className="px-1"),
                        ])
                    ],
                ),
                dcc.Tab(
                    label=TABS["morphology"]["label"],
                    value="morphology",
                    style=BASE_TAB,
                    selected_style=sel_tab("morphology"),
                    children=[
                        html.Div(style={"padding": "28px 0 12px 0"}, children=[
                            tab_banner(
                                "morphology",
                                "Géométrie individuelle de chaque fibre mesurée dans les volumes 3D",
                                "La microtomographie X permet de reconstituer la forme exacte de chaque fibre "
                                "dans l'espace 3D. On mesure ainsi le diamètre (section transversale), "
                                "la longueur développée, l'angle d'inclinaison (orientation) et la courbure. "
                                "Ces quatre paramètres déterminent la micro-structure du réseau fibreux, "
                                "qui gouverne à son tour les propriétés mécaniques et acoustiques du matériau.",
                                [
                                    "Diamètre (µm) : épaisseur de la fibre — influe sur la surface de contact disponible.",
                                    "Longueur (µm) : extension de la fibre — détermine la capacité à former plusieurs liaisons.",
                                    "Orientation θ : angle par rapport au plan horizontal — caractérise l'anisotropie.",
                                    "Courbure κ : ondulation de la fibre — modifie la tortuosité des pores et l'absorption acoustique.",
                                ],
                            ),
                            dbc.Row(className="px-1", children=[
                                graph_card(
                                    "graph-diameter",
                                    "Diamètre des fibres par matériau (µm)",
                                    "Le diamètre mesure l'épaisseur de chaque fibre sur sa section transversale. "
                                    "Des fibres fines créent un réseau plus dense avec davantage de connexions par unité de volume, "
                                    "ce qui améliore généralement l'absorption acoustique.",
                                    "Chaque boîte couvre 50 % des fibres (du 1er au 3e quartile). "
                                    "La ligne centrale = médiane. Les points isolés = fibres atypiques. "
                                    "Survolez pour voir les statistiques exactes.",
                                    accent=TABS["morphology"]["bg"],
                                ),
                                graph_card(
                                    "graph-length",
                                    "Longueur des fibres par matériau (µm)",
                                    "Des fibres longues forment plus de liaisons avec leurs voisines, "
                                    "créant un réseau enchevêtré plus rigide. La variabilité de longueur "
                                    "au sein d'un même matériau reflète l'homogénéité de fabrication.",
                                    "Une grande hauteur de boîte = forte variabilité de longueur dans le matériau. "
                                    "Comparez la médiane (trait central) entre matériaux pour voir les différences typiques.",
                                    accent=TABS["morphology"]["bg"],
                                ),
                            ]),
                            dbc.Row(className="px-1", children=[
                                graph_card(
                                    "graph-orientation",
                                    "Distribution des orientations angulaires θ",
                                    "L'angle θ mesure l'inclinaison de chaque fibre par rapport au plan horizontal. "
                                    "θ = 0° → fibre horizontale (couchée). θ = 90° → fibre verticale (debout). "
                                    "Cette distribution caractérise l'isotropie ou l'anisotropie du matériau.",
                                    "Un pic marqué près de 0° = matériau plan (typique des non-tissés). "
                                    "Courbe plate = fibres orientées dans toutes les directions (matériau isotrope). "
                                    "Cliquez sur un matériau dans la légende pour l'isoler.",
                                    accent=TABS["morphology"]["bg"],
                                ),
                                graph_card(
                                    "graph-curvature",
                                    "Courbure des fibres par matériau (κ × 10³ mm⁻¹)",
                                    "κ = 1/R mesure l'écart d'une fibre par rapport à une droite parfaite. "
                                    "κ ≈ 0 = fibre rectiligne. κ élevé = fibre ondulée ou torsadée. "
                                    "Les fibres ondulées augmentent la tortuosité des pores, ce qui favorise l'absorption acoustique.",
                                    "Valeurs proches de 0 = fibres rectilignes (verre, carbone). "
                                    "Valeurs élevées = fibres très ondulées (naturelles, recyclées). "
                                    "Survolez pour voir la distribution exacte par matériau.",
                                    accent=TABS["morphology"]["bg"],
                                ),
                            ]),
                        ])
                    ],
                ),
                dcc.Tab(
                    label=TABS["contacts"]["label"],
                    value="contacts",
                    style=BASE_TAB,
                    selected_style=sel_tab("contacts"),
                    children=[
                        html.Div(style={"padding": "28px 0 12px 0"}, children=[
                            tab_banner(
                                "contacts",
                                "Liaisons physiques entre fibres et cohésion du réseau 3D",
                                "Lorsque deux fibres se croisent dans le volume 3D, elles forment une liaison appelée contact. "
                                "Le nombre et la surface de ces contacts définissent la cohésion mécanique du réseau. "
                                "Acoustiquement, ces contacts créent des résistances locales au passage de l'air : "
                                "plus le réseau est connecté, plus il dissipe l'énergie sonore. "
                                "La densité de connexions est donc un prédicteur important de la performance acoustique.",
                                [
                                    "Aire de contact (µm²) : surface de recouvrement entre deux fibres qui se croisent.",
                                    "Densité de connexions : nombre de contacts par mm³ de matériau.",
                                    "Porosité : fraction de vide — naturellement liée à la densité de connexions.",
                                    "Un réseau dense (faible porosité) crée plus de contacts, donc une meilleure absorption.",
                                ],
                            ),
                            dbc.Row(className="px-1", children=[
                                graph_card(
                                    "graph-contact-area",
                                    "Distribution des aires de contact fibre-fibre (µm²)",
                                    "Chaque contact est l'intersection de deux fibres. Sa surface dépend "
                                    "du diamètre des fibres, de leur angle de croisement et de la forme de leur section. "
                                    "Une grande aire = jonction solide. Une petite aire = liaison plus souple.",
                                    "La distribution est typiquement asymétrique : la plupart des contacts sont petits (pic à gauche), "
                                    "et quelques rares contacts très larges existent (queue à droite). "
                                    "Survolez les barres pour voir les effectifs précis.",
                                    accent=TABS["contacts"]["bg"],
                                ),
                                graph_card(
                                    "graph-density-porosity",
                                    "Densité de connexions vs Porosité",
                                    "Ces deux grandeurs sont intimement liées : un matériau peu poreux (dense) "
                                    "contient plus de fibres par unité de volume, donc naturellement plus de contacts. "
                                    "Un bon matériau acoustique trouve un compromis : assez poreux pour laisser entrer "
                                    "l'air, mais assez connecté pour le freiner.",
                                    "Tendance attendue : décroissante (plus la porosité est élevée, moins il y a de contacts). "
                                    "Les points s'écartant de cette tendance sont informatifs sur la géométrie particulière des fibres. "
                                    "Survolez pour voir l'identifiant de l'échantillon.",
                                    accent=TABS["contacts"]["bg"],
                                ),
                            ]),
                        ])
                    ],
                ),
                dcc.Tab(
                    label=TABS["acoustics"]["label"],
                    value="acoustics",
                    style=BASE_TAB,
                    selected_style=sel_tab("acoustics"),
                    children=[
                        html.Div(style={"padding": "28px 0 12px 0"}, children=[
                            tab_banner(
                                "acoustics",
                                "Lien entre micro-structure des fibres et absorption du son",
                                "Ces mesures expérimentales quantifient comment chaque matériau absorbe le son "
                                "à différentes fréquences. L'objectif central du projet est d'établir des corrélations "
                                "entre les paramètres morphologiques (porosité, diamètre, courbure) et les performances "
                                "acoustiques — pour concevoir des matériaux légers, durables et acoustiquement efficaces "
                                "sans avoir à tout mesurer en laboratoire.",
                                [
                                    "Coefficient d'absorption α : de 0 (son réfléchi) à 1 (son totalement absorbé).",
                                    "Fréquences mesurées : 250 Hz à 4 000 Hz (voix, bruit de route, moteur, HF).",
                                    "Résistivité au flux σ : résistance du matériau au passage de l'air — paramètre acoustique clé.",
                                    "Objectif : σ ni trop faible (son traverse) ni trop élevée (son réfléchi).",
                                ],
                            ),
                            dbc.Row(className="px-1", children=[
                                graph_card(
                                    "graph-absorption",
                                    "Coefficient d'absorption acoustique par fréquence",
                                    "Chaque courbe représente un échantillon mesuré en tube de Kundt. "
                                    "Les matériaux fibreux absorbent généralement mieux les hautes fréquences "
                                    "(voix, bruit moteur) que les basses (vibrations structurelles). "
                                    "La courbe en pointillés noirs est la médiane de la sélection.",
                                    "Un α élevé dès 500 Hz est très bon pour les applications transport. "
                                    "Cliquez sur un échantillon dans la légende pour l'isoler. "
                                    "Les écarts entre courbes d'un même matériau révèlent la variabilité de fabrication.",
                                    height="360px",
                                    col_width=7,
                                    accent=TABS["acoustics"]["bg"],
                                ),
                                graph_card(
                                    "graph-resistivity",
                                    "Résistivité au flux d'air vs Porosité",
                                    "La résistivité σ (Pa·s/m²) est le paramètre acoustique le plus prédictif "
                                    "pour les matériaux fibreux. Elle croît quand la porosité diminue. "
                                    "La droite de tendance montre la relation log-linéaire typique de ces matériaux.",
                                    "Axe vertical en échelle logarithmique — les valeurs couvrent plusieurs ordres de grandeur. "
                                    "La plage optimale dépend de l'application visée. "
                                    "Survolez pour voir l'identifiant de l'échantillon et les valeurs exactes.",
                                    height="360px",
                                    col_width=5,
                                    accent=TABS["acoustics"]["bg"],
                                ),
                            ]),
                        ])
                    ],
                ),
            ],
        ),
    ]),

    # ── FOOTER ──────────────────────────────────────────────────────────────
    html.Div(style={
        "textAlign": "center",
        "padding":   "24px 16px",
        "color":     "#94A3B8",
        "fontSize":  "12px",
    }, children=[
        html.Hr(style={"borderColor": "#E2E8F0", "marginBottom": "14px"}),
        html.P("FiberScope — Projet E4 — ESIEE Paris — Microtomographie X & Caractérisation fibreuse",
               style={"margin": 0}),
    ]),
])


# ─── Utilitaires callback ─────────────────────────────────────────────────────
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


def _empty_fig(msg="Données non disponibles"):
    fig = go.Figure()
    fig.update_layout(
        **PLOT_LAYOUT,
        annotations=[dict(
            text=msg, x=0.5, y=0.5,
            xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=13, color="#94A3B8"),
        )],
    )
    return apply_grid(fig)


def _boxplot(df, y_col, y_title=""):
    if df.empty or not _has(df, y_col, "material"):
        return _empty_fig(f"Colonne '{y_col}' non disponible dans les données")
    fig = go.Figure()
    for i, mat in enumerate(sorted(df["material"].dropna().unique())):
        vals = df[df["material"] == mat][y_col].dropna()
        if vals.empty:
            continue
        fig.add_trace(go.Box(
            y=vals, name=mat,
            marker_color=mat_color(mat, i),
            boxpoints="outliers",
            line_width=1.8, marker_size=3,
            hovertemplate=(
                f"<b>{mat}</b><br>"
                "Médiane : %{median:.2f}<br>"
                "Q1 : %{q1:.2f}<br>"
                "Q3 : %{q3:.2f}<br>"
                "Min : %{lowerfence:.2f}<br>"
                "Max : %{upperfence:.2f}"
                "<extra></extra>"
            ),
        ))
    fig.update_layout(
        **PLOT_LAYOUT,
        yaxis_title=y_title,
        showlegend=False,
    )
    return apply_grid(fig)


# ─── Callback principal ───────────────────────────────────────────────────────
@app.callback(
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

    def sub(df):
        if df.empty or "sample_id" not in df.columns:
            return pd.DataFrame()
        return df[df["sample_id"].isin(ids)]

    fib_f = sub(fibers)
    con_f = sub(contacts)
    aco_f = sub(acoustic)

    n_samples  = len(samp_f)
    n_fibers   = len(fib_f)
    n_contacts = len(con_f)
    mean_por   = samp_f["porosity"].mean() if _has(samp_f, "porosity") and n_samples else None
    mean_qual  = samp_f["quality_score"].mean() if _has(samp_f, "quality_score") and n_samples else None

    # ── KPIs ────────────────────────────────────────────────────────────────
    kpis = [
        kpi_card("Échantillons analysés", str(n_samples),
                 "Volumes 3D numérisés par microtomographie X", "#1D4ED8"),
        kpi_card("Fibres détectées", f"{n_fibers:,}",
                 "Fibres individuelles segmentées dans les volumes 3D", "#6D28D9"),
        kpi_card("Contacts fibre-fibre", f"{n_contacts:,}",
                 "Liaisons entre fibres identifiées dans le réseau", "#047857"),
        kpi_card("Porosité moyenne",
                 f"{mean_por:.3f}" if mean_por is not None else "—",
                 "Fraction de vide dans le matériau (0 = plein, 1 = creux)", "#B45309"),
        kpi_card("Score qualité moyen",
                 f"{mean_qual:.1f} / 5" if mean_qual is not None else "—",
                 "Qualité moyenne de la reconstruction 3D", "#DC2626"),
    ]

    # ── Diamètre ─────────────────────────────────────────────────────────────
    fig_diam = _boxplot(fib_f, "diameter_um", "Diamètre (µm)")

    # ── Longueur ─────────────────────────────────────────────────────────────
    fig_len = _boxplot(fib_f, "length_um", "Longueur (µm)")

    # ── Orientations ─────────────────────────────────────────────────────────
    fig_ori = go.Figure()
    if not fib_f.empty and _has(fib_f, "orientation_theta", "material"):
        for i, mat in enumerate(sorted(fib_f["material"].dropna().unique())):
            vals = fib_f[fib_f["material"] == mat]["orientation_theta"].dropna()
            if vals.empty:
                continue
            fig_ori.add_trace(go.Histogram(
                x=vals, name=mat,
                marker_color=mat_color(mat, i),
                opacity=0.72, nbinsx=20, histnorm="percent",
                hovertemplate=f"<b>{mat}</b><br>θ = %{{x:.0f}}°<br>%{{y:.1f}} % des fibres<extra></extra>",
            ))
    else:
        return kpis, _empty_fig(), _empty_fig(), _empty_fig("Colonne 'orientation_theta' non disponible"), \
               _empty_fig(), _empty_fig(), _empty_fig(), _empty_fig(), _empty_fig()

    fig_ori.update_layout(
        **PLOT_LAYOUT,
        barmode="overlay",
        xaxis_title="θ (degrés)",
        yaxis_title="% des fibres",
        legend=dict(orientation="h", y=1.06, x=0, font_size=11, bgcolor="rgba(0,0,0,0)"),
    )
    apply_grid(fig_ori)

    # ── Courbure ─────────────────────────────────────────────────────────────
    if not fib_f.empty and "curvature" in fib_f.columns:
        fc = fib_f.copy()
        fc["curvature_scaled"] = fc["curvature"] * 1000
        fig_curv = _boxplot(fc, "curvature_scaled", "κ × 10³ (mm⁻¹)")
    else:
        fig_curv = _empty_fig("Colonne 'curvature' non disponible")

    # ── Aires de contact ──────────────────────────────────────────────────────
    fig_ca = go.Figure()
    if not con_f.empty and _has(con_f, "contact_area_um2", "material"):
        for i, mat in enumerate(sorted(con_f["material"].dropna().unique())):
            vals = con_f[con_f["material"] == mat]["contact_area_um2"].dropna()
            if vals.empty:
                continue
            p99 = vals.quantile(0.99)
            vals = vals[vals <= p99]
            fig_ca.add_trace(go.Histogram(
                x=vals, name=mat,
                marker_color=mat_color(mat, i),
                opacity=0.72, nbinsx=30, histnorm="percent",
                hovertemplate=f"<b>{mat}</b><br>%{{x:.0f}} µm²<br>%{{y:.1f}} % des contacts<extra></extra>",
            ))
        fig_ca.update_layout(
            **PLOT_LAYOUT,
            barmode="overlay",
            xaxis_title="Aire de contact (µm²)",
            yaxis_title="% des contacts",
            legend=dict(orientation="h", y=1.06, x=0, font_size=11, bgcolor="rgba(0,0,0,0)"),
        )
        apply_grid(fig_ca)
    else:
        fig_ca = _empty_fig("Colonnes 'contact_area_um2' ou 'material' non disponibles")

    # ── Densité connexions vs Porosité ────────────────────────────────────────
    fig_dp = go.Figure()
    if not samp_f.empty and _has(samp_f, "porosity", "contact_density", "material"):
        for i, mat in enumerate(sorted(samp_f["material"].dropna().unique())):
            sub = samp_f[samp_f["material"] == mat]
            fig_dp.add_trace(go.Scatter(
                x=sub["porosity"], y=sub["contact_density"],
                mode="markers", name=mat,
                marker=dict(color=mat_color(mat, i), size=12,
                            line=dict(width=1.5, color="white")),
                text=sub.get("sample_id"),
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
            legend=dict(orientation="h", y=1.06, x=0, font_size=11, bgcolor="rgba(0,0,0,0)"),
        )
        apply_grid(fig_dp)
    else:
        fig_dp = _empty_fig("Colonnes 'porosity', 'contact_density' ou 'material' non disponibles")

    # ── Absorption acoustique ─────────────────────────────────────────────────
    freq_vals = [250, 500, 1000, 2000, 4000]
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
                x=freq_vals, y=vals,
                mode="lines+markers",
                name=f"{sid}",
                line=dict(color=mat_color(mat, i), width=2),
                marker=dict(size=5),
                opacity=0.8,
                hovertemplate=f"<b>{sid} ({mat})</b><br>%{{x}} Hz → α = %{{y:.3f}}<extra></extra>",
            ))
            shown += 1
        if shown > 1:
            medians = [aco_f[c].dropna().median() for c in freq_cols]
            fig_abs.add_trace(go.Scatter(
                x=freq_vals, y=medians, mode="lines",
                name="Médiane",
                line=dict(color="#0F172A", width=3, dash="dot"),
                hovertemplate="Médiane<br>%{x} Hz → α = %{y:.3f}<extra></extra>",
            ))
    fig_abs.update_layout(
        **PLOT_LAYOUT,
        xaxis=dict(
            title="Fréquence (Hz)",
            tickvals=freq_vals,
            ticktext=["250 Hz","500 Hz","1 kHz","2 kHz","4 kHz"],
            **{k: v for k, v in AXIS_STYLE.items() if k != "title_font"},
            title_font=AXIS_STYLE["title_font"],
        ),
        yaxis=dict(
            title="Coefficient d'absorption α",
            range=[0, 1.05],
            **{k: v for k, v in AXIS_STYLE.items() if k != "title_font"},
            title_font=AXIS_STYLE["title_font"],
        ),
        legend=dict(orientation="v", x=1.01, y=1, font_size=10, bgcolor="rgba(0,0,0,0)"),
    )

    # ── Résistivité vs Porosité ───────────────────────────────────────────────
    fig_res = go.Figure()
    if not aco_f.empty and _has(aco_f, "porosity", "airflow_resistivity", "material"):
        for i, mat in enumerate(sorted(aco_f["material"].dropna().unique())):
            sub = aco_f[aco_f["material"] == mat].dropna(
                subset=["porosity", "airflow_resistivity"])
            if sub.empty:
                continue
            fig_res.add_trace(go.Scatter(
                x=sub["porosity"], y=sub["airflow_resistivity"],
                mode="markers", name=mat,
                marker=dict(color=mat_color(mat, i), size=12,
                            line=dict(width=1.5, color="white")),
                text=sub.get("sample_id"),
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "Porosité : %{x:.3f}<br>"
                    "Résistivité σ : %{y:,.0f} Pa·s/m²"
                    "<extra></extra>"
                ),
            ))
        valid = aco_f.dropna(subset=["porosity", "airflow_resistivity"])
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
            xaxis_title="Porosité",
            yaxis_title="Résistivité σ (Pa·s/m²)",
            yaxis_type="log",
            legend=dict(orientation="h", y=1.06, x=0, font_size=11, bgcolor="rgba(0,0,0,0)"),
        )
        apply_grid(fig_res)
    else:
        fig_res = _empty_fig("Colonnes 'airflow_resistivity' ou 'porosity' non disponibles")

    return (kpis, fig_diam, fig_len, fig_ori, fig_curv,
            fig_ca, fig_dp, fig_abs, fig_res)


# ─── Reset filtres ────────────────────────────────────────────────────────────
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
