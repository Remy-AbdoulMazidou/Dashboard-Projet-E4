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
from dash import dcc, html, Input, Output, State, ctx
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

FREQ_VALS = [250, 500, 1000, 2000, 4000]
FREQ_COLS = ["absorption_250hz", "absorption_500hz", "absorption_1000hz",
             "absorption_2000hz", "absorption_4000hz"]

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
    margin=dict(l=70, r=24, t=48, b=60),
    hoverlabel=dict(bgcolor="#1E293B", bordercolor="#0F172A", font_size=12, font_color="white"),
)

AXIS_STYLE = dict(
    showgrid=True,  gridcolor="#94A3B8",  gridwidth=1,
    zeroline=True,  zerolinecolor="#64748B", zerolinewidth=1.5,
    showline=True,  linecolor="#64748B",  linewidth=1,
    title_font=dict(size=13, color="#1E293B", family="Inter, system-ui, sans-serif"),
    tickfont=dict(size=11, color="#334155"),
)

# Légende uniforme sur tous les graphiques
LEGEND_STYLE = dict(
    title=dict(
        text="Matériaux  —  cliquez pour afficher / double-clic pour isoler",
        font=dict(size=10, color="#64748B"),
    ),
    bgcolor="rgba(248,250,252,0.95)",
    bordercolor="#CBD5E1",
    borderwidth=1,
    font=dict(size=11, color="#334155"),
    itemclick="toggle",
    itemdoubleclick="toggleothers",
    tracegroupgap=3,
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


def graph_card(graph_id, title, description, read_guide, height="310px", col_width=6, accent="#2563EB"):
    return dbc.Col(dbc.Card(style={
        "borderRadius": "12px",
        "border":       "1px solid #E2E8F0",
        "boxShadow":    "0 2px 10px rgba(15,23,42,0.06)",
        "height":       "100%",
    }, children=[
        dbc.CardBody(style={"padding": "20px 20px 16px 20px"}, children=[
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
            html.P(description, style={
                "fontSize": "12px", "color": "#64748B",
                "lineHeight": "1.6", "marginBottom": "8px",
                "textAlign": "center",
            }),
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
            dcc.Graph(id=graph_id, config=PLOT_CONFIG, style={"height": height}),
        ])
    ]), xs=12, md=col_width, className="mb-4")


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


def _sample_selector_panel():
    """Panneau de sélection des échantillons pour le graphique d'absorption."""
    accent = TABS["acoustics"]["bg"]
    return dbc.Col(dbc.Card(style={
        "borderRadius": "12px",
        "border":       "1px solid #E2E8F0",
        "boxShadow":    "0 2px 10px rgba(15,23,42,0.06)",
        "height":       "100%",
    }, children=[
        dbc.CardBody(style={"padding": "16px 14px"}, children=[
            # En-tête
            html.Div(style={"textAlign": "center", "marginBottom": "12px"}, children=[
                html.Div(style={
                    "width": "28px", "height": "3px",
                    "backgroundColor": accent, "borderRadius": "2px",
                    "margin": "0 auto 8px auto",
                }),
                html.H6("Sélection", style={
                    "fontWeight": 700, "color": "#0F172A",
                    "fontSize": "13px", "marginBottom": "3px",
                }),
                html.P("Cochez les échantillons à afficher sur le graphique",
                       style={"fontSize": "10.5px", "color": "#64748B", "margin": 0,
                              "lineHeight": "1.4"}),
            ]),
            # Barre de recherche
            dcc.Input(
                id="acou-search",
                type="text",
                placeholder="🔍 Rechercher...",
                debounce=True,
                style={
                    "width": "100%", "padding": "6px 10px",
                    "border": "1px solid #E2E8F0", "borderRadius": "8px",
                    "fontSize": "12px", "marginBottom": "8px",
                    "color": "#334155", "boxSizing": "border-box",
                    "outline": "none",
                },
            ),
            # Boutons tout/aucun
            html.Div(style={"display": "flex", "gap": "6px", "marginBottom": "10px"}, children=[
                dbc.Button("Tout afficher", id="acou-select-all", size="sm", style={
                    "flex": 1, "fontSize": "11px", "padding": "5px 4px",
                    "backgroundColor": accent, "color": "white",
                    "border": "none", "borderRadius": "6px", "fontWeight": 600,
                }),
                dbc.Button("Tout masquer", id="acou-deselect-all", size="sm", style={
                    "flex": 1, "fontSize": "11px", "padding": "5px 4px",
                    "backgroundColor": "white", "color": "#64748B",
                    "border": "1px solid #CBD5E1", "borderRadius": "6px",
                }),
            ]),
            # Liste avec cases à cocher
            html.Div(style={
                "maxHeight": "270px", "overflowY": "auto",
                "border": "1px solid #F1F5F9", "borderRadius": "8px",
                "padding": "6px 8px",
            }, children=[
                dcc.Checklist(
                    id="acou-checklist",
                    options=[],
                    value=[],
                    labelStyle={
                        "display": "flex", "alignItems": "center",
                        "marginBottom": "6px", "cursor": "pointer",
                        "lineHeight": "1.3",
                    },
                    inputStyle={
                        "marginRight": "8px", "cursor": "pointer",
                        "accentColor": accent, "width": "14px", "height": "14px",
                    },
                ),
            ]),
        ]),
    ]), xs=12, md=4, className="mb-4")


# ─── Layout ───────────────────────────────────────────────────────────────────
app.layout = dbc.Container(fluid=True, style={
    "backgroundColor": "#F1F5F9",
    "minHeight": "100vh",
    "fontFamily": "Inter, system-ui, sans-serif",
}, children=[

    # ── Store données acoustiques ────────────────────────────────────────────
    dcc.Store(id="acou-data-store"),

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
                    "fontSize": "12px", "color": "white",
                    "fontWeight": 600, "verticalAlign": "middle",
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
                    "Tous les graphiques se mettent à jour instantanément.",
                    style={"fontSize": "12px", "color": "#64748B", "marginBottom": "14px"},
                ),
                # ── 3 éléments sur la même ligne ──
                html.Div(style={
                    "display": "flex", "gap": "16px",
                    "alignItems": "flex-end", "flexWrap": "wrap",
                }, children=[
                    html.Div(style={"flex": "2 1 180px"}, children=[
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
                    ]),
                    html.Div(style={"flex": "2 1 180px"}, children=[
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
                    ]),
                    dbc.Button(
                        "Tout afficher",
                        id="btn-reset",
                        style={
                            "border":          "1px solid #CBD5E1",
                            "backgroundColor": "white",
                            "color":           "#475569",
                            "fontWeight":      700,
                            "fontSize":        "12px",
                            "whiteSpace":      "nowrap",
                            "borderRadius":    "8px",
                            "padding":         "9px 18px",
                            "flexShrink":      0,
                            "alignSelf":       "flex-end",
                        },
                    ),
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

                # ── VUE D'ENSEMBLE ──────────────────────────────────────────
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
                                "nombre de fibres détectées, porosité et densité du réseau de contacts. "
                                "C'est le point de départ pour comprendre un échantillon avant d'explorer les détails.",
                                [
                                    "Échantillons : volumes 3D numérisés par microtomographie X (scanner de haute résolution).",
                                    "Fibres : éléments fibreux individuels segmentés algorithmiquement dans chaque volume.",
                                    "Contacts : points où deux fibres se croisent et se touchent dans le réseau 3D.",
                                    "Porosité : proportion de vide dans le matériau — un indicateur clé des performances acoustiques.",
                                ],
                            ),
                            dbc.Row(id="row-kpis", className="px-1"),
                        ])
                    ],
                ),

                # ── MORPHOLOGIE ─────────────────────────────────────────────
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
                            dbc.Row(className="px-1 g-3", children=[
                                graph_card(
                                    "graph-diameter",
                                    "Diamètre des fibres par matériau (µm)",
                                    "Le diamètre mesure l'épaisseur de chaque fibre sur sa section transversale. "
                                    "Des fibres fines créent un réseau plus dense avec davantage de connexions par unité de volume, "
                                    "ce qui améliore généralement l'absorption acoustique.",
                                    "Chaque boîte couvre 50 % des fibres (1er → 3e quartile). "
                                    "Le trait central = valeur médiane. Les points isolés = fibres atypiques. "
                                    "Survolez pour voir les statistiques complètes.",
                                    accent=TABS["morphology"]["bg"],
                                ),
                                graph_card(
                                    "graph-length",
                                    "Longueur des fibres par matériau (µm)",
                                    "Des fibres longues forment plus de liaisons avec leurs voisines, "
                                    "créant un réseau enchevêtré plus rigide. La variabilité de longueur "
                                    "au sein d'un même matériau reflète l'homogénéité de fabrication.",
                                    "Une boîte haute = forte variabilité de longueur dans ce matériau. "
                                    "Comparez la médiane entre matériaux pour voir les différences typiques. "
                                    "Survolez pour voir les chiffres exacts.",
                                    accent=TABS["morphology"]["bg"],
                                ),
                            ]),
                            dbc.Row(className="px-1 g-3", children=[
                                graph_card(
                                    "graph-orientation",
                                    "Distribution des orientations angulaires θ",
                                    "L'angle θ mesure l'inclinaison de chaque fibre par rapport au plan horizontal. "
                                    "θ = 0° → fibre couchée (horizontale). θ = 90° → fibre debout (verticale). "
                                    "Cette distribution caractérise l'isotropie ou l'anisotropie du matériau.",
                                    "Un pic marqué près de 0° = matériau plan (typique des non-tissés). "
                                    "Courbe plate = fibres dans toutes les directions (matériau isotrope). "
                                    "Cliquez sur un matériau dans la légende pour l'afficher seul.",
                                    accent=TABS["morphology"]["bg"],
                                ),
                                graph_card(
                                    "graph-curvature",
                                    "Courbure des fibres par matériau (κ × 10³ mm⁻¹)",
                                    "κ = 1/R mesure l'écart d'une fibre par rapport à une droite parfaite. "
                                    "κ ≈ 0 = fibre rectiligne. κ élevé = fibre très ondulée. "
                                    "Les fibres ondulées augmentent la tortuosité des pores, favorisant l'absorption acoustique.",
                                    "Valeurs proches de 0 = fibres rectilignes (verre, carbone). "
                                    "Valeurs élevées = fibres très ondulées (naturelles, recyclées). "
                                    "Survolez pour voir la distribution exacte par matériau.",
                                    accent=TABS["morphology"]["bg"],
                                ),
                            ]),
                        ])
                    ],
                ),

                # ── LIAISONS INTER-FIBRES ────────────────────────────────────
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
                            dbc.Row(className="px-1 g-3", children=[
                                graph_card(
                                    "graph-contact-area",
                                    "Distribution des aires de contact fibre-fibre (µm²)",
                                    "Chaque contact est l'intersection de deux fibres. Sa surface dépend "
                                    "du diamètre des fibres, de leur angle de croisement et de la forme de leur section. "
                                    "Une grande aire = jonction solide. Une petite aire = liaison plus souple.",
                                    "Distribution typiquement asymétrique : plupart des contacts sont petits (pic à gauche), "
                                    "avec quelques rares contacts très larges (queue à droite). "
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
                                    "Les points hors tendance révèlent une géométrie de fibres particulière. "
                                    "Survolez pour voir l'identifiant de l'échantillon.",
                                    accent=TABS["contacts"]["bg"],
                                ),
                            ]),
                        ])
                    ],
                ),

                # ── PROPRIÉTÉS ACOUSTIQUES ───────────────────────────────────
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

                            # Ligne 1 : courbes d'absorption + panneau de sélection
                            dbc.Row(className="px-1 g-3 mb-0", children=[
                                graph_card(
                                    "graph-absorption",
                                    "Coefficient d'absorption acoustique par fréquence",
                                    "Chaque courbe représente un échantillon mesuré en tube de Kundt. "
                                    "Sélectionnez les échantillons à comparer dans le panneau de droite.",
                                    "α élevé dès 500 Hz = très bon pour les applications transport. "
                                    "Comparez les courbes pour évaluer la variabilité inter-lots. "
                                    "Survolez pour lire la valeur exacte à chaque fréquence.",
                                    height="340px",
                                    col_width=8,
                                    accent=TABS["acoustics"]["bg"],
                                ),
                                _sample_selector_panel(),
                            ]),

                            # Ligne 2 : résistivité + classement comparatif
                            dbc.Row(className="px-1 g-3", children=[
                                graph_card(
                                    "graph-resistivity",
                                    "Résistivité au flux d'air vs Porosité",
                                    "La résistivité σ (Pa·s/m²) est le paramètre acoustique le plus prédictif "
                                    "pour les matériaux fibreux. Elle croît quand la porosité diminue. "
                                    "La droite de tendance montre la relation log-linéaire typique de ces matériaux.",
                                    "Axe vertical en échelle logarithmique (les valeurs couvrent plusieurs ordres de grandeur). "
                                    "La plage optimale σ dépend de l'application visée. "
                                    "Survolez pour voir l'identifiant de l'échantillon et les valeurs exactes.",
                                    height="310px",
                                    col_width=6,
                                    accent=TABS["acoustics"]["bg"],
                                ),
                                graph_card(
                                    "graph-absorption-ranking",
                                    "Classement acoustique — absorption moyenne par matériau",
                                    "Ce graphique compare directement les matériaux sur l'ensemble du spectre. "
                                    "Chaque courbe est la moyenne de tous les échantillons d'un même matériau, "
                                    "permettant d'identifier rapidement le matériau le plus performant acoustiquement.",
                                    "Les courbes hautes = meilleure absorption. Focalisez-vous sur 500–2000 Hz "
                                    "(plage critique pour le confort acoustique en transport). "
                                    "Double-cliquez sur un matériau pour l'isoler.",
                                    height="310px",
                                    col_width=6,
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


def _boxplot(df, y_col, y_title="", unit=""):
    """Boxplot par matériau avec tooltip clair en français."""
    if df.empty or not _has(df, y_col, "material"):
        return _empty_fig(f"Colonne '{y_col}' non disponible dans les données")
    u = f" {unit}" if unit else ""
    fig = go.Figure()
    for i, mat in enumerate(sorted(df["material"].dropna().unique())):
        vals = df[df["material"] == mat][y_col].dropna()
        if vals.empty:
            continue
        q1_v   = vals.quantile(0.25)
        med_v  = vals.median()
        q3_v   = vals.quantile(0.75)
        iqr_v  = q3_v - q1_v
        low_v  = max(vals.min(), q1_v - 1.5 * iqr_v)
        high_v = min(vals.max(), q3_v + 1.5 * iqr_v)
        n_v    = len(vals)
        fig.add_trace(go.Box(
            y=vals, name=mat,
            marker_color=mat_color(mat, i),
            boxpoints="outliers",
            line_width=1.8, marker_size=3,
            hovertemplate=(
                f"<b>{mat}</b><br>"
                f"Médiane : <b>{med_v:.2f}{u}</b><br>"
                f"50 % des fibres entre {q1_v:.2f} et {q3_v:.2f}{u}<br>"
                f"Plage typique : {low_v:.2f} – {high_v:.2f}{u}<br>"
                f"Nombre de mesures : {n_v:,}"
                "<extra></extra>"
            ),
        ))
    fig.update_layout(
        **PLOT_LAYOUT,
        yaxis_title=y_title,
        showlegend=False,
    )
    return apply_grid(fig)


def _legend_h():
    """Légende horizontale au-dessus du graphique."""
    return dict(**LEGEND_STYLE, orientation="h", y=1.18, x=0)


def _legend_v():
    """Légende verticale à droite du graphique."""
    return dict(**LEGEND_STYLE, orientation="v", x=1.02, y=1)


# ─── Callback principal (tout sauf graph-absorption) ─────────────────────────
@app.callback(
    Output("row-kpis",               "children"),
    Output("graph-diameter",         "figure"),
    Output("graph-length",           "figure"),
    Output("graph-orientation",      "figure"),
    Output("graph-curvature",        "figure"),
    Output("graph-contact-area",     "figure"),
    Output("graph-density-porosity", "figure"),
    Output("graph-resistivity",      "figure"),
    Output("graph-absorption-ranking", "figure"),
    Output("acou-data-store",        "data"),
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
    ]

    # ── Diamètre / Longueur ───────────────────────────────────────────────
    fig_diam = _boxplot(fib_f, "diameter_um", "Diamètre (µm)", "µm")
    fig_len  = _boxplot(fib_f, "length_um",   "Longueur (µm)", "µm")

    # ── Orientations ─────────────────────────────────────────────────────
    fig_ori = go.Figure()
    if not fib_f.empty and _has(fib_f, "orientation_theta", "material"):
        mats = sorted(fib_f["material"].dropna().unique())
        for i, mat in enumerate(mats):
            vals = fib_f[fib_f["material"] == mat]["orientation_theta"].dropna()
            if vals.empty:
                continue
            fig_ori.add_trace(go.Histogram(
                x=vals, name=mat,
                marker_color=mat_color(mat, i),
                marker_line=dict(color="white", width=0.8),
                opacity=0.55, nbinsx=20, histnorm="percent",
                visible=True if i == 0 else "legendonly",
                hovertemplate=f"<b>{mat}</b><br>θ = %{{x:.0f}}°<br>%{{y:.1f}} % des fibres<extra></extra>",
            ))
        fig_ori.update_layout(
            **PLOT_LAYOUT,
            barmode="overlay",
            xaxis_title="θ (degrés)",
            yaxis_title="% des fibres",
            legend=_legend_h(),
        )
        apply_grid(fig_ori)
    else:
        fig_ori = _empty_fig("Colonne 'orientation_theta' non disponible")

    # ── Courbure ─────────────────────────────────────────────────────────
    if not fib_f.empty and "curvature" in fib_f.columns:
        fc = fib_f.copy()
        fc["curvature_scaled"] = fc["curvature"] * 1000
        fig_curv = _boxplot(fc, "curvature_scaled", "κ × 10³ (mm⁻¹)", "×10³ mm⁻¹")
    else:
        fig_curv = _empty_fig("Colonne 'curvature' non disponible")

    # ── Aires de contact ──────────────────────────────────────────────────
    fig_ca = go.Figure()
    if not con_f.empty and _has(con_f, "contact_area_um2", "material"):
        mats = sorted(con_f["material"].dropna().unique())
        for i, mat in enumerate(mats):
            vals = con_f[con_f["material"] == mat]["contact_area_um2"].dropna()
            if vals.empty:
                continue
            p99  = vals.quantile(0.99)
            vals = vals[vals <= p99]
            fig_ca.add_trace(go.Histogram(
                x=vals, name=mat,
                marker_color=mat_color(mat, i),
                marker_line=dict(color="white", width=0.8),
                opacity=0.55, nbinsx=30, histnorm="percent",
                visible=True if i == 0 else "legendonly",
                hovertemplate=f"<b>{mat}</b><br>Aire = %{{x:.0f}} µm²<br>%{{y:.1f}} % des contacts<extra></extra>",
            ))
        fig_ca.update_layout(
            **PLOT_LAYOUT,
            barmode="overlay",
            xaxis_title="Aire de contact (µm²)",
            yaxis_title="% des contacts",
            legend=_legend_h(),
        )
        apply_grid(fig_ca)
    else:
        fig_ca = _empty_fig("Colonnes 'contact_area_um2' ou 'material' non disponibles")

    # ── Densité connexions vs Porosité ────────────────────────────────────
    fig_dp = go.Figure()
    if not samp_f.empty and _has(samp_f, "porosity", "contact_density", "material"):
        for i, mat in enumerate(sorted(samp_f["material"].dropna().unique())):
            grp = samp_f[samp_f["material"] == mat]
            fig_dp.add_trace(go.Scatter(
                x=grp["porosity"], y=grp["contact_density"],
                mode="markers", name=mat,
                marker=dict(color=mat_color(mat, i), size=12,
                            line=dict(width=1.5, color="white")),
                text=grp.get("sample_id"),
                visible=True if i == 0 else "legendonly",
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "Porosité : %{x:.3f}<br>"
                    "Densité de connexions : %{y:.1f} contacts/mm³"
                    "<extra></extra>"
                ),
            ))
        fig_dp.update_layout(
            **PLOT_LAYOUT,
            xaxis_title="Porosité",
            yaxis_title="Densité de connexions (contacts/mm³)",
            legend=_legend_h(),
        )
        apply_grid(fig_dp)
    else:
        fig_dp = _empty_fig("Colonnes 'porosity', 'contact_density' ou 'material' non disponibles")

    # ── Résistivité vs Porosité ───────────────────────────────────────────
    fig_res = go.Figure()
    if not aco_f.empty and _has(aco_f, "porosity", "airflow_resistivity", "material"):
        for i, mat in enumerate(sorted(aco_f["material"].dropna().unique())):
            grp = aco_f[aco_f["material"] == mat].dropna(subset=["porosity", "airflow_resistivity"])
            if grp.empty:
                continue
            fig_res.add_trace(go.Scatter(
                x=grp["porosity"], y=grp["airflow_resistivity"],
                mode="markers", name=mat,
                marker=dict(color=mat_color(mat, i), size=12,
                            line=dict(width=1.5, color="white")),
                text=grp.get("sample_id"),
                visible=True if i == 0 else "legendonly",
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
            legend=_legend_h(),
        )
        apply_grid(fig_res)
    else:
        fig_res = _empty_fig("Colonnes 'airflow_resistivity' ou 'porosity' non disponibles")

    # ── Classement acoustique par matériau ────────────────────────────────
    fig_ranking = go.Figure()
    if not aco_f.empty and all(c in aco_f.columns for c in FREQ_COLS) and _has(aco_f, "material"):
        for i, mat in enumerate(sorted(aco_f["material"].dropna().unique())):
            grp = aco_f[aco_f["material"] == mat][FREQ_COLS].dropna()
            if grp.empty:
                continue
            means = [grp[c].mean() for c in FREQ_COLS]
            fig_ranking.add_trace(go.Scatter(
                x=FREQ_VALS, y=means,
                mode="lines+markers",
                name=mat,
                line=dict(color=mat_color(mat, i), width=2.5),
                marker=dict(size=8, symbol="circle",
                            line=dict(width=1.5, color="white")),
                hovertemplate=f"<b>{mat}</b><br>%{{x}} Hz → α moyen = %{{y:.3f}}<extra></extra>",
            ))
        fig_ranking.update_layout(
            **PLOT_LAYOUT,
            xaxis=dict(
                title="Fréquence (Hz)",
                tickvals=FREQ_VALS,
                ticktext=["250 Hz", "500 Hz", "1 kHz", "2 kHz", "4 kHz"],
                **{k: v for k, v in AXIS_STYLE.items() if k != "title_font"},
                title_font=AXIS_STYLE["title_font"],
            ),
            yaxis=dict(
                title="Coefficient d'absorption α moyen",
                range=[0, 1.05],
                **{k: v for k, v in AXIS_STYLE.items() if k != "title_font"},
                title_font=AXIS_STYLE["title_font"],
            ),
            legend=_legend_v(),
        )
    else:
        fig_ranking = _empty_fig("Données d'absorption insuffisantes pour comparer les matériaux")

    # ── Store acoustique pour le panneau de sélection ─────────────────────
    acou_store = []
    if not aco_f.empty and all(c in aco_f.columns for c in FREQ_COLS) and _has(aco_f, "sample_id", "material"):
        cols = ["sample_id", "material"] + FREQ_COLS
        acou_store = aco_f[cols].dropna(subset=FREQ_COLS).to_dict("records")

    return (kpis, fig_diam, fig_len, fig_ori, fig_curv,
            fig_ca, fig_dp, fig_res, fig_ranking, acou_store)


# ─── Callback : options et sélection du panneau échantillons ────────────────
@app.callback(
    Output("acou-checklist", "options"),
    Output("acou-checklist", "value"),
    Input("acou-data-store",    "data"),
    Input("acou-search",        "value"),
    Input("acou-select-all",    "n_clicks"),
    Input("acou-deselect-all",  "n_clicks"),
    State("acou-checklist",     "value"),
)
def update_acoustic_options(store_data, search, _n_all, _n_none, current_val):
    records = store_data or []

    # Index matériaux pour les couleurs
    mats_seen = {}
    mat_idx = 0
    for rec in records:
        m = rec.get("material", "?")
        if m not in mats_seen:
            mats_seen[m] = mat_idx
            mat_idx += 1

    # Construire toutes les options (label HTML = carré coloré + texte)
    all_options = []
    for rec in records:
        sid = str(rec["sample_id"])
        mat = rec.get("material", "?")
        color = mat_color(mat, mats_seen.get(mat, 0))
        label = html.Span([
            html.Span("■ ", style={"color": color, "fontWeight": "bold", "fontSize": "14px"}),
            html.Span(sid,  style={"fontWeight": 600, "fontSize": "12px", "color": "#1E293B"}),
            html.Span(f" ({mat})", style={"fontSize": "11px", "color": "#64748B"}),
        ])
        all_options.append({"label": label, "value": sid})

    # Filtrer par recherche
    if search:
        s = search.lower()
        filtered_options = [
            o for o, rec in zip(all_options, records)
            if s in str(rec["sample_id"]).lower() or s in rec.get("material", "").lower()
        ]
    else:
        filtered_options = all_options

    all_ids = [o["value"] for o in all_options]
    filtered_ids = [o["value"] for o in filtered_options]

    # Déterminer la nouvelle sélection
    triggered_id = ctx.triggered_id if ctx.triggered_id else ""

    if triggered_id == "acou-select-all":
        new_val = filtered_ids
    elif triggered_id == "acou-deselect-all":
        new_val = []
    elif triggered_id == "acou-data-store":
        # Nouvelles données : afficher seulement le premier échantillon
        new_val = [filtered_ids[0]] if filtered_ids else []
    else:
        # Recherche : garder la sélection courante valide
        new_val = [v for v in (current_val or []) if v in all_ids]

    return filtered_options, new_val


# ─── Callback : graphique d'absorption ───────────────────────────────────────
@app.callback(
    Output("graph-absorption", "figure"),
    Input("acou-checklist",  "value"),
    State("acou-data-store", "data"),
)
def update_absorption_graph(selected_ids, store_data):
    records = store_data or []
    selected_ids = selected_ids or []

    if not records:
        return _empty_fig("Données d'absorption acoustique non disponibles")
    if not selected_ids:
        return _empty_fig("Sélectionnez au moins un échantillon dans le panneau de droite")

    # Index matériaux
    mats_seen = {}
    mat_idx = 0
    for rec in records:
        m = rec.get("material", "?")
        if m not in mats_seen:
            mats_seen[m] = mat_idx
            mat_idx += 1

    fig = go.Figure()
    for rec in records:
        sid = str(rec["sample_id"])
        if sid not in selected_ids:
            continue
        mat  = rec.get("material", "?")
        vals = [rec.get(c) for c in FREQ_COLS]
        if any(v is None or (isinstance(v, float) and np.isnan(v)) for v in vals):
            continue
        color = mat_color(mat, mats_seen.get(mat, 0))
        fig.add_trace(go.Scatter(
            x=FREQ_VALS, y=vals,
            mode="lines+markers",
            name=f"{sid} ({mat})",
            line=dict(color=color, width=2.5),
            marker=dict(size=6, line=dict(width=1, color="white")),
            hovertemplate=f"<b>{sid} ({mat})</b><br>%{{x}} Hz → α = %{{y:.3f}}<extra></extra>",
        ))

    if len(selected_ids) > 1:
        # Médiane sur les échantillons sélectionnés
        sel_records = [r for r in records if str(r["sample_id"]) in selected_ids]
        medians = [
            float(np.median([r.get(c, np.nan) for r in sel_records if r.get(c) is not None]))
            for c in FREQ_COLS
        ]
        if not any(np.isnan(m) for m in medians):
            fig.add_trace(go.Scatter(
                x=FREQ_VALS, y=medians, mode="lines",
                name="Médiane sélection",
                line=dict(color="#0F172A", width=3, dash="dot"),
                hovertemplate="Médiane<br>%{x} Hz → α = %{y:.3f}<extra></extra>",
            ))

    fig.update_layout(
        **PLOT_LAYOUT,
        xaxis=dict(
            title="Fréquence (Hz)",
            tickvals=FREQ_VALS,
            ticktext=["250 Hz", "500 Hz", "1 kHz", "2 kHz", "4 kHz"],
            **{k: v for k, v in AXIS_STYLE.items() if k != "title_font"},
            title_font=AXIS_STYLE["title_font"],
        ),
        yaxis=dict(
            title="Coefficient d'absorption α",
            range=[0, 1.05],
            **{k: v for k, v in AXIS_STYLE.items() if k != "title_font"},
            title_font=AXIS_STYLE["title_font"],
        ),
        legend=dict(orientation="v", x=1.01, y=1, font_size=10,
                    bgcolor="rgba(248,250,252,0.9)", bordercolor="#CBD5E1", borderwidth=1),
    )
    apply_grid(fig)
    return fig


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
