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
from dash import dcc, html, Input, Output, State, ctx, ALL
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
    margin=dict(l=70, r=24, t=54, b=60),
    hoverlabel=dict(bgcolor="#1E293B", bordercolor="#0F172A", font_size=12, font_color="white"),
)

AXIS_STYLE = dict(
    showgrid=True,  gridcolor="#94A3B8",  gridwidth=1,
    zeroline=True,  zerolinecolor="#64748B", zerolinewidth=1.5,
    showline=True,  linecolor="#64748B",  linewidth=1,
    title_font=dict(size=13, color="#1E293B", family="Inter, system-ui, sans-serif"),
    tickfont=dict(size=11, color="#334155"),
)

LEGEND_STYLE = dict(
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

def _legend_h():
    return dict(**LEGEND_STYLE, orientation="h", y=1.22, x=0)

def _legend_v():
    return dict(**LEGEND_STYLE, orientation="v", x=1.02, y=1)

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

# ─── Composants réutilisables ─────────────────────────────────────────────────

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


def _read_guide_block(text, accent):
    """Bloc 'Comment lire ce graphique' standardisé."""
    return html.Div([
        html.Span("Comment lire : ", style={
            "fontWeight": 700, "fontSize": "11px", "color": "#334155",
        }),
        html.Span(text, style={"fontSize": "11px", "color": "#64748B"}),
    ], style={
        "backgroundColor": "#F1F5F9",
        "borderLeft":      f"3px solid {accent}",
        "padding":         "7px 11px",
        "borderRadius":    "0 6px 6px 0",
        "marginBottom":    "14px",
        "lineHeight":      "1.55",
    })


def graph_card(graph_id, title, description, read_guide, height="310px", col_width=6, accent="#2563EB"):
    # Légende matériaux custom (cases à cocher) sous le graphique
    legend_row = None
    if MATERIALS:
        items = []
        for i, mat in enumerate(MATERIALS):
            items.append(html.Div(
                id={"type": "mat-g-cb", "graph": graph_id, "mat": mat},
                n_clicks=0,
                className="mat-cb-item mat-cb-item--on",
                children=[
                    html.Div(className="mat-cb-box", children=[
                        html.Span("✕", className="mat-cb-x",
                                  style={"color": mat_color(mat, i)}),
                    ]),
                    html.Span(mat, className="mat-cb-name"),
                ],
            ))
        items.append(html.Div(className="mat-cb-separator"))
        items.append(html.Div(
            id={"type": "mat-g-all", "graph": graph_id},
            n_clicks=0,
            className="mat-cb-item mat-cb-item--on",
            children=[
                html.Div(className="mat-cb-box", children=[
                    html.Span("✕", className="mat-cb-x",
                              style={"color": "#0F172A"}),
                ]),
                html.Span("Tous les matériaux", className="mat-cb-name"),
            ],
        ))
        legend_row = html.Div(items, className="mat-cb-row", style={
            "marginTop": "10px",
            "paddingTop": "10px",
            "borderTop": "1px solid #E2E8F0",
        })

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
                    "fontWeight": 800, "color": "#0F172A",
                    "fontSize": "15px", "marginBottom": "0",
                    "letterSpacing": "-0.02em",
                }),
            ]),
            html.P(description, style={
                "fontSize": "13px", "color": "#334155",
                "fontWeight": "500",
                "lineHeight": "1.65", "marginBottom": "10px",
                "textAlign": "center",
            }),
            _read_guide_block(read_guide, accent),
            dcc.Graph(id=graph_id, config=PLOT_CONFIG, style={"height": height}),
            legend_row,
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


def _absorption_card():
    """Carte absorption : graphique + sélecteur intégrés côte à côte."""
    accent = TABS["acoustics"]["bg"]
    return dbc.Col(dbc.Card(style={
        "borderRadius": "12px",
        "border":       "1px solid #E2E8F0",
        "boxShadow":    "0 2px 10px rgba(15,23,42,0.06)",
    }, children=[
        dbc.CardBody(style={"padding": "20px 20px 16px 20px"}, children=[
            # Titre
            html.Div(style={"textAlign": "center", "marginBottom": "10px"}, children=[
                html.Div(style={
                    "width": "28px", "height": "3px",
                    "backgroundColor": accent, "borderRadius": "2px",
                    "margin": "0 auto 8px auto",
                }),
                html.H6("Coefficient d'absorption acoustique par fréquence", style={
                    "fontWeight": 800, "color": "#0F172A",
                    "fontSize": "15px", "marginBottom": "0",
                    "letterSpacing": "-0.02em",
                }),
            ]),
            html.P(
                "Chaque courbe montre comment un échantillon absorbe le son selon la fréquence. "
                "Plus la courbe est haute, meilleure est l'absorption.",
                style={"fontSize": "13px", "color": "#334155",
                       "fontWeight": "500",
                       "lineHeight": "1.65", "marginBottom": "10px", "textAlign": "center"},
            ),
            _read_guide_block(
                "Choisissez un ou plusieurs échantillons dans la liste à droite. "
                "Un α proche de 1 = excellent absorbant. Proche de 0 = le son rebondit. "
                "La fréquence 1 kHz correspond à la voix humaine.",
                accent,
            ),
            # Zone graphique + sélecteur côte à côte
            html.Div(style={"display": "flex", "gap": "14px", "alignItems": "stretch"}, children=[

                # Graphique
                html.Div(style={"flex": 1, "minWidth": 0}, children=[
                    dcc.Graph(id="graph-absorption", config=PLOT_CONFIG,
                              style={"height": "320px"}),
                ]),

                # Séparateur vertical
                html.Div(style={
                    "width": "1px", "backgroundColor": "#E2E8F0",
                    "flexShrink": 0, "borderRadius": "1px",
                }),

                # Panneau de sélection compact
                html.Div(style={
                    "width": "175px", "flexShrink": 0,
                    "display": "flex", "flexDirection": "column", "gap": "8px",
                }, children=[
                    html.P("Échantillons à afficher :", style={
                        "fontSize": "11px", "fontWeight": 700,
                        "color": "#334155", "margin": 0,
                    }),
                    # Recherche
                    dcc.Input(
                        id="acou-search",
                        type="text",
                        placeholder="🔍 Rechercher...",
                        debounce=True,
                        style={
                            "width": "100%", "padding": "5px 8px",
                            "border": "1px solid #E2E8F0", "borderRadius": "6px",
                            "fontSize": "11px", "color": "#334155",
                            "boxSizing": "border-box", "outline": "none",
                        },
                    ),
                    # Boutons
                    html.Div(style={"display": "flex", "gap": "5px"}, children=[
                        dbc.Button("Tous", id="acou-select-all", size="sm", style={
                            "flex": 1, "fontSize": "10px", "padding": "3px 0",
                            "backgroundColor": accent, "color": "white",
                            "border": "none", "borderRadius": "5px", "fontWeight": 600,
                        }),
                        dbc.Button("Aucun", id="acou-deselect-all", size="sm", style={
                            "flex": 1, "fontSize": "10px", "padding": "3px 0",
                            "backgroundColor": "white", "color": "#64748B",
                            "border": "1px solid #CBD5E1", "borderRadius": "5px",
                        }),
                    ]),
                    # Liste
                    html.Div(style={
                        "flex": 1,
                        "overflowY": "auto",
                        "maxHeight": "250px",
                        "border": "1px solid #F1F5F9",
                        "borderRadius": "6px",
                        "padding": "4px 6px",
                        "backgroundColor": "#FAFAFA",
                    }, children=[
                        dcc.Checklist(
                            id="acou-checklist",
                            options=[],
                            value=[],
                            labelStyle={
                                "display": "flex", "alignItems": "center",
                                "marginBottom": "5px", "cursor": "pointer",
                                "lineHeight": "1.3",
                            },
                            inputStyle={
                                "marginRight": "7px", "cursor": "pointer",
                                "accentColor": accent,
                                "width": "13px", "height": "13px",
                            },
                        ),
                    ]),
                ]),
            ]),
        ]),
    ]), xs=12, md=12, className="mb-4")


# ─── Layout ───────────────────────────────────────────────────────────────────
app.layout = dbc.Container(fluid=True, style={
    "backgroundColor": "#F1F5F9",
    "minHeight": "100vh",
    "fontFamily": "Inter, system-ui, sans-serif",
}, children=[

    dcc.Store(id="acou-data-store"),
    dcc.Store(id="mat-vis-store", data=list(MATERIALS)),

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
            "justifyContent": "center", "gap": "6px", "marginTop": "4px",
        }) if MATERIALS else html.Span(),
    ]),

    # ── FILTRES ──────────────────────────────────────────────────────────────
    dbc.Row(className="mt-4 mb-3 px-3", children=[
        dbc.Col(dbc.Card(style={
            "borderRadius": "12px", "border": "1px solid #E2E8F0",
            "boxShadow": "0 2px 6px rgba(0,0,0,0.04)", "backgroundColor": "white",
        }, children=[
            dbc.CardBody(style={"padding": "16px 20px"}, children=[
                html.P(
                    "Filtrez les données par matériau et par lot de fabrication. "
                    "Tous les graphiques se mettent à jour instantanément.",
                    style={"fontSize": "12px", "color": "#64748B", "marginBottom": "14px"},
                ),
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
                            multi=True, placeholder="Tous les matériaux",
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
                            multi=True, placeholder="Tous les lots",
                            style={"fontSize": "13px"},
                        ),
                    ]),
                    dbc.Button("Tout afficher", id="btn-reset", style={
                        "border": "1px solid #CBD5E1", "backgroundColor": "white",
                        "color": "#475569", "fontWeight": 700, "fontSize": "12px",
                        "whiteSpace": "nowrap", "borderRadius": "8px",
                        "padding": "9px 18px", "flexShrink": 0, "alignSelf": "flex-end",
                    }),
                ]),
            ]),
        ]))
    ]),

    # ── ONGLETS ──────────────────────────────────────────────────────────────
    html.Div(style={"padding": "0 16px"}, children=[
        dcc.Tabs(
            id="main-tabs", value="overview",
            style={"borderBottom": "2px solid #E2E8F0", "marginBottom": "0"},
            children=[

                # ── VUE D'ENSEMBLE ──────────────────────────────────────────
                dcc.Tab(label=TABS["overview"]["label"], value="overview",
                        style=BASE_TAB, selected_style=sel_tab("overview"),
                        children=[html.Div(style={"padding": "28px 0 12px 0"}, children=[
                            tab_banner(
                                "overview",
                                "Résumé des données analysées",
                                "Cette page donne un aperçu rapide de tout ce que le scanner 3D a mesuré "
                                "pour les matériaux sélectionnés. C'est le point de départ idéal avant "
                                "d'explorer les détails dans les autres onglets.",
                                [
                                    "Échantillons : morceaux de matériau numérisés en 3D par le scanner.",
                                    "Fibres : chaque fil individuel détecté à l'intérieur du matériau.",
                                    "Contacts : points où deux fibres se touchent et forment une liaison.",
                                    "Porosité : part de vide dans le matériau — plus c'est élevé, plus il y a d'air à l'intérieur.",
                                ],
                            ),
                            dbc.Row(id="row-kpis", className="px-1"),
                        ])]),

                # ── MORPHOLOGIE ─────────────────────────────────────────────
                dcc.Tab(label=TABS["morphology"]["label"], value="morphology",
                        style=BASE_TAB, selected_style=sel_tab("morphology"),
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
                                    "Compare l'épaisseur des fibres entre matériaux. "
                                    "Des fibres plus fines créent généralement un réseau plus dense et absorbant.",
                                    "La barre centrale = l'épaisseur la plus courante. "
                                    "La boîte = où se trouvent la majorité des fibres. "
                                    "Survolez pour voir les valeurs exactes.",
                                    accent=TABS["morphology"]["bg"],
                                ),
                                graph_card(
                                    "graph-length",
                                    "Longueur des fibres par matériau (µm)",
                                    "Compare la longueur des fibres entre matériaux. "
                                    "Des fibres plus longues peuvent former plus de liaisons dans le réseau.",
                                    "La barre centrale = la longueur la plus courante. "
                                    "Une boîte haute = tailles très variées au sein du matériau. "
                                    "Survolez pour voir les valeurs exactes.",
                                    accent=TABS["morphology"]["bg"],
                                ),
                            ]),
                            dbc.Row(className="px-1 g-3", children=[
                                graph_card(
                                    "graph-orientation",
                                    "Direction des fibres dans le matériau (angle θ)",
                                    "Montre dans quelle direction sont orientées les fibres. "
                                    "0° = fibres à plat, 90° = fibres verticales.",
                                    "Un pic = beaucoup de fibres dans la même direction. "
                                    "Courbe plate = fibres dans toutes les directions. "
                                    "Utilisez les cases ci-dessous pour afficher ou masquer un matériau.",
                                    accent=TABS["morphology"]["bg"],
                                ),
                                graph_card(
                                    "graph-curvature",
                                    "Courbure des fibres par matériau",
                                    "Mesure à quel point les fibres sont droites ou courbées. "
                                    "Des fibres très courbées (ondulées) améliorent l'absorption acoustique.",
                                    "Boîte basse = fibres presque droites. "
                                    "Boîte haute = fibres très ondulées. "
                                    "Survolez pour comparer les matériaux.",
                                    accent=TABS["morphology"]["bg"],
                                ),
                            ]),
                        ])]),

                # ── LIAISONS INTER-FIBRES ────────────────────────────────────
                dcc.Tab(label=TABS["contacts"]["label"], value="contacts",
                        style=BASE_TAB, selected_style=sel_tab("contacts"),
                        children=[html.Div(style={"padding": "28px 0 12px 0"}, children=[
                            tab_banner(
                                "contacts",
                                "Comment les fibres se connectent entre elles",
                                "Quand deux fibres se croisent, elles forment un point de contact. "
                                "Plus un matériau a de points de contact, plus il est solide mécaniquement "
                                "et plus il freine le passage de l'air — ce qui améliore l'absorption du son.",
                                [
                                    "Aire de contact : la surface de la zone où deux fibres se touchent (en µm²).",
                                    "Densité de contacts : combien de points de contact il y a par mm³ de matériau.",
                                    "Porosité : plus la porosité est faible, plus les fibres sont serrées et se touchent souvent.",
                                ],
                            ),
                            dbc.Row(className="px-1 g-3", children=[
                                graph_card(
                                    "graph-contact-area",
                                    "Taille des zones de contact entre fibres (µm²)",
                                    "Montre la répartition des tailles de zones de contact. "
                                    "La plupart sont petites, quelques-unes peuvent être très grandes.",
                                    "Les barres à gauche = contacts petits (les plus fréquents). "
                                    "Les barres à droite = contacts plus rares mais plus grands. "
                                    "Utilisez les cases ci-dessous pour afficher ou masquer un matériau.",
                                    accent=TABS["contacts"]["bg"],
                                ),
                                graph_card(
                                    "graph-density-porosity",
                                    "Nombre de contacts selon la densité du matériau",
                                    "Un matériau dense (peu de vide) contient plus de fibres et donc "
                                    "plus de points de contact. Ce graphique confirme cette relation.",
                                    "Chaque point = un échantillon. En bas à droite = peu dense, peu de contacts. "
                                    "En haut à gauche = très dense, beaucoup de contacts. "
                                    "Survolez un point pour voir de quel échantillon il s'agit.",
                                    accent=TABS["contacts"]["bg"],
                                ),
                            ]),
                        ])]),

                # ── PROPRIÉTÉS ACOUSTIQUES ───────────────────────────────────
                dcc.Tab(label=TABS["acoustics"]["label"], value="acoustics",
                        style=BASE_TAB, selected_style=sel_tab("acoustics"),
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

                            # Ligne 1 : absorption + sélecteur intégré
                            dbc.Row(className="px-1 g-3", children=[
                                _absorption_card(),
                            ]),

                            # Ligne 2 : résistivité + classement
                            dbc.Row(className="px-1 g-3", children=[
                                graph_card(
                                    "graph-resistivity",
                                    "Résistance à l'air vs quantité de vide (porosité)",
                                    "Plus un matériau est dense (peu poreux), plus il résiste au passage de l'air. "
                                    "Une résistance intermédiaire est idéale pour l'absorption acoustique.",
                                    "Chaque point = un échantillon. En bas = résistance faible (laisse passer l'air). "
                                    "En haut = résistance forte (bloque l'air). "
                                    "Utilisez les cases ci-dessous pour afficher ou masquer un matériau.",
                                    height="310px", col_width=6,
                                    accent=TABS["acoustics"]["bg"],
                                ),
                                graph_card(
                                    "graph-absorption-ranking",
                                    "Comparaison des matériaux — absorption moyenne",
                                    "Chaque courbe = la performance acoustique moyenne d'un matériau "
                                    "sur l'ensemble du spectre. Permet de voir en un coup d'œil "
                                    "quel matériau absorbe le mieux le son.",
                                    "La courbe la plus haute = le meilleur absorbant. "
                                    "Utilisez les cases ci-dessous pour afficher ou masquer un matériau.",
                                    height="310px", col_width=6,
                                    accent=TABS["acoustics"]["bg"],
                                ),
                            ]),
                        ])]),
            ],
        ),
    ]),

    # ── FOOTER ──────────────────────────────────────────────────────────────
    html.Div(style={
        "textAlign": "center", "padding": "24px 16px",
        "color": "#94A3B8", "fontSize": "12px",
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
    if mat_sel is not None:   # None = pas de filtre ; [] = afficher rien
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
            text=msg, x=0.5, y=0.5, xref="paper", yref="paper",
            showarrow=False, font=dict(size=13, color="#94A3B8"),
        )],
    )
    return apply_grid(fig)


def _boxplot(df, y_col, y_title="", unit=""):
    """
    Boxplot par matériau.
    Le hover natif de go.Box est désactivé (hoverinfo='none') car Plotly génère
    des événements séparés pour chaque élément (médiane, moustaches, etc.) qui
    affichent des labels cryptiques comme 'carbone max', 'carbone median'...
    On le remplace par des points invisibles positionnés aux valeurs clés de la
    boîte, qui déclenchent un tooltip clair et unifié en français.
    """
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

        tooltip = (
            f"<b>{mat}</b><br>"
            f"Valeur typique : <b>{med_v:.2f}{u}</b><br>"
            f"La moitié des fibres : {q1_v:.2f} – {q3_v:.2f}{u}<br>"
            f"Plage habituelle : {low_v:.2f} – {high_v:.2f}{u}<br>"
            f"Fibres mesurées : {n_v:,}"
            "<extra></extra>"
        )

        # Boîte visible — hover natif supprimé
        fig.add_trace(go.Box(
            y=vals, name=mat,
            marker_color=mat_color(mat, i),
            boxpoints=False,
            line_width=1.8,
            hoverinfo="none",
        ))

        # Points invisibles aux niveaux clés → tooltip propre sur toute la hauteur
        for y_pos in [low_v, q1_v, med_v, q3_v, high_v]:
            fig.add_trace(go.Scatter(
                x=[mat], y=[y_pos],
                mode="markers",
                showlegend=False,
                marker=dict(size=14, opacity=0),
                hovertemplate=tooltip,
            ))

    fig.update_layout(**PLOT_LAYOUT, yaxis_title=y_title, showlegend=False)
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
    Output("graph-resistivity",      "figure"),
    Output("graph-absorption-ranking", "figure"),
    Output("acou-data-store",        "data"),
    Input("mat-vis-store", "data"),
    Input("filter-batch",  "value"),
)
def update_all(vis_mats, bat_sel):
    ids, samp_f = _filter(vis_mats, bat_sel)

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
    fig_diam = _boxplot(fib_f, "diameter_um", "Épaisseur (µm)", "µm")
    fig_len  = _boxplot(fib_f, "length_um",   "Longueur (µm)", "µm")

    # ── Orientations ─────────────────────────────────────────────────────
    fig_ori = go.Figure()
    if not fib_f.empty and _has(fib_f, "orientation_theta", "material"):
        for i, mat in enumerate(sorted(fib_f["material"].dropna().unique())):
            vals = fib_f[fib_f["material"] == mat]["orientation_theta"].dropna()
            if vals.empty:
                continue
            fig_ori.add_trace(go.Histogram(
                x=vals, name=mat,
                marker_color=mat_color(mat, i),
                marker_line=dict(color="white", width=0.8),
                opacity=0.55, nbinsx=20, histnorm="percent",
                hovertemplate=f"<b>{mat}</b><br>Angle = %{{x:.0f}}°<br>%{{y:.1f}} % des fibres<extra></extra>",
            ))
        fig_ori.update_layout(
            **PLOT_LAYOUT,
            barmode="overlay",
            xaxis_title="Angle θ (degrés)",
            yaxis_title="% des fibres",
            showlegend=False,
        )
        apply_grid(fig_ori)
    else:
        fig_ori = _empty_fig("Colonne 'orientation_theta' non disponible")

    # ── Courbure ─────────────────────────────────────────────────────────
    if not fib_f.empty and "curvature" in fib_f.columns:
        fc = fib_f.copy()
        fc["curvature_scaled"] = fc["curvature"] * 1000
        fig_curv = _boxplot(fc, "curvature_scaled", "Courbure (κ × 10³ mm⁻¹)", "×10³ mm⁻¹")
    else:
        fig_curv = _empty_fig("Colonne 'curvature' non disponible")

    # ── Aires de contact ──────────────────────────────────────────────────
    fig_ca = go.Figure()
    if not con_f.empty and _has(con_f, "contact_area_um2", "material"):
        for i, mat in enumerate(sorted(con_f["material"].dropna().unique())):
            vals = con_f[con_f["material"] == mat]["contact_area_um2"].dropna()
            if vals.empty:
                continue
            vals = vals[vals <= vals.quantile(0.99)]
            fig_ca.add_trace(go.Histogram(
                x=vals, name=mat,
                marker_color=mat_color(mat, i),
                marker_line=dict(color="white", width=0.8),
                opacity=0.55, nbinsx=30, histnorm="percent",
                hovertemplate=f"<b>{mat}</b><br>Aire = %{{x:.0f}} µm²<br>%{{y:.1f}} % des contacts<extra></extra>",
            ))
        fig_ca.update_layout(
            **PLOT_LAYOUT,
            barmode="overlay",
            xaxis_title="Aire de contact (µm²)",
            yaxis_title="% des contacts",
            showlegend=False,
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
                hovertemplate=(
                    "<b>Échantillon %{text}</b><br>"
                    "Porosité : %{x:.3f}<br>"
                    "Contacts : %{y:.1f} par mm³"
                    "<extra></extra>"
                ),
            ))
        fig_dp.update_layout(
            **PLOT_LAYOUT,
            xaxis_title="Porosité (proportion de vide)",
            yaxis_title="Contacts par mm³",
            showlegend=False,
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
                hovertemplate=(
                    "<b>Échantillon %{text}</b><br>"
                    "Porosité : %{x:.3f}<br>"
                    "Résistivité : %{y:,.0f} Pa·s/m²"
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
            xaxis_title="Porosité (proportion de vide)",
            yaxis_title="Résistivité σ (Pa·s/m²)",
            yaxis_type="log",
            showlegend=False,
        )
        apply_grid(fig_res)
    else:
        fig_res = _empty_fig("Colonnes 'airflow_resistivity' ou 'porosity' non disponibles")

    # ── Classement acoustique ─────────────────────────────────────────────
    fig_ranking = go.Figure()
    if not aco_f.empty and all(c in aco_f.columns for c in FREQ_COLS) and _has(aco_f, "material"):
        for i, mat in enumerate(sorted(aco_f["material"].dropna().unique())):
            grp = aco_f[aco_f["material"] == mat][FREQ_COLS].dropna()
            if grp.empty:
                continue
            means = [grp[c].mean() for c in FREQ_COLS]
            fig_ranking.add_trace(go.Scatter(
                x=FREQ_VALS, y=means,
                mode="lines+markers", name=mat,
                line=dict(color=mat_color(mat, i), width=2.5),
                marker=dict(size=8, line=dict(width=1.5, color="white")),
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
                title="Absorption moyenne α",
                range=[0, 1.05],
                **{k: v for k, v in AXIS_STYLE.items() if k != "title_font"},
                title_font=AXIS_STYLE["title_font"],
            ),
            showlegend=False,
        )
    else:
        fig_ranking = _empty_fig("Données d'absorption insuffisantes pour comparer les matériaux")

    # ── Store données acoustiques ─────────────────────────────────────────
    acou_store = []
    if not aco_f.empty and all(c in aco_f.columns for c in FREQ_COLS) and _has(aco_f, "sample_id", "material"):
        cols = ["sample_id", "material"] + FREQ_COLS
        acou_store = aco_f[cols].dropna(subset=FREQ_COLS).to_dict("records")

    return (kpis, fig_diam, fig_len, fig_ori, fig_curv,
            fig_ca, fig_dp, fig_res, fig_ranking, acou_store)


# ─── Callback : panneau de sélection des échantillons ────────────────────────
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
    mats_idx = {}
    for idx, rec in enumerate(records):
        m = rec.get("material", "?")
        if m not in mats_idx:
            mats_idx[m] = len(mats_idx)

    # Construire les options (carré coloré + nom)
    all_options = []
    for rec in records:
        sid   = str(rec["sample_id"])
        mat   = rec.get("material", "?")
        color = mat_color(mat, mats_idx.get(mat, 0))
        label = html.Span([
            html.Span("■ ", style={"color": color, "fontWeight": "bold", "fontSize": "14px"}),
            html.Span(sid, style={"fontWeight": 600, "fontSize": "11px", "color": "#1E293B"}),
            html.Span(f" {mat}", style={"fontSize": "10px", "color": "#94A3B8"}),
        ])
        all_options.append({"label": label, "value": sid})

    # Filtrer par recherche
    if search:
        s = search.lower()
        filtered = [
            (o, rec) for o, rec in zip(all_options, records)
            if s in str(rec["sample_id"]).lower() or s in rec.get("material", "").lower()
        ]
        filtered_options = [o for o, _ in filtered]
    else:
        filtered_options = all_options

    all_ids      = [o["value"] for o in all_options]
    filtered_ids = [o["value"] for o in filtered_options]

    triggered_id = ctx.triggered_id if ctx.triggered_id else ""

    if triggered_id == "acou-select-all":
        new_val = filtered_ids
    elif triggered_id == "acou-deselect-all":
        new_val = []
    elif triggered_id == "acou-data-store":
        new_val = [filtered_ids[0]] if filtered_ids else []
    else:
        new_val = [v for v in (current_val or []) if v in all_ids]

    return filtered_options, new_val


# ─── Callback : graphique d'absorption ───────────────────────────────────────
@app.callback(
    Output("graph-absorption", "figure"),
    Input("acou-checklist",  "value"),
    Input("acou-data-store", "data"),
)
def update_absorption_graph(selected_ids, store_data):
    records      = store_data or []
    selected_ids = selected_ids or []

    if not records:
        return _empty_fig("Données d'absorption acoustique non disponibles")

    if not selected_ids:
        return _empty_fig("Sélectionnez au moins un échantillon dans la liste à droite →")

    mats_idx = {}
    for rec in records:
        m = rec.get("material", "?")
        if m not in mats_idx:
            mats_idx[m] = len(mats_idx)

    fig = go.Figure()
    for rec in records:
        sid = str(rec["sample_id"])
        if sid not in selected_ids:
            continue
        mat  = rec.get("material", "?")
        vals = [rec.get(c) for c in FREQ_COLS]
        if any(v is None or (isinstance(v, float) and np.isnan(v)) for v in vals):
            continue
        color = mat_color(mat, mats_idx.get(mat, 0))
        fig.add_trace(go.Scatter(
            x=FREQ_VALS, y=vals,
            mode="lines+markers",
            name=f"{sid} ({mat})",
            line=dict(color=color, width=2.5),
            marker=dict(size=6, line=dict(width=1, color="white")),
            hovertemplate=f"<b>{sid} ({mat})</b><br>%{{x}} Hz → α = %{{y:.3f}}<extra></extra>",
        ))

    # Médiane si plusieurs sélectionnés
    if len(selected_ids) > 1:
        sel_recs = [r for r in records if str(r["sample_id"]) in selected_ids]
        medians  = [
            float(np.median([r[c] for r in sel_recs if r.get(c) is not None]))
            for c in FREQ_COLS
        ]
        if not any(np.isnan(m) for m in medians):
            fig.add_trace(go.Scatter(
                x=FREQ_VALS, y=medians, mode="lines",
                name="Médiane",
                line=dict(color="#0F172A", width=3, dash="dot"),
                hovertemplate="Médiane sélection<br>%{x} Hz → α = %{y:.3f}<extra></extra>",
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
        legend=dict(
            orientation="v", x=1.01, y=1,
            font_size=10, bgcolor="rgba(248,250,252,0.9)",
            bordercolor="#CBD5E1", borderwidth=1,
        ),
    )
    apply_grid(fig)
    return fig


# ─── Callback : dropdown matériau → mat-vis-store ────────────────────────────
@app.callback(
    Output("mat-vis-store", "data"),
    Input("filter-material", "value"),
    prevent_initial_call=True,
)
def material_dropdown_to_store(mat_sel):
    if not mat_sel:
        return list(MATERIALS)
    return list(mat_sel)


# ─── Callback : cases matériaux dans les graphiques ──────────────────────────
@app.callback(
    Output("mat-vis-store", "data", allow_duplicate=True),
    Input({"type": "mat-g-cb",  "graph": ALL, "mat": ALL}, "n_clicks"),
    Input({"type": "mat-g-all", "graph": ALL},              "n_clicks"),
    State("mat-vis-store", "data"),
    prevent_initial_call=True,
)
def toggle_material_vis_graph(mat_clicks, all_clicks, current):
    triggered = ctx.triggered_id
    vis = list(current or [])
    if isinstance(triggered, dict):
        if triggered.get("type") == "mat-g-cb":
            mat = triggered["mat"]
            if mat in vis:
                vis.remove(mat)
            else:
                vis.append(mat)
            return vis
        if triggered.get("type") == "mat-g-all":
            if set(vis) == set(MATERIALS):
                return []
            return list(MATERIALS)
    return vis


# ─── Callback : sync classes des cases dans les graphiques ───────────────────
@app.callback(
    Output({"type": "mat-g-cb",  "graph": ALL, "mat": ALL}, "className"),
    Output({"type": "mat-g-all", "graph": ALL},              "className"),
    Input("mat-vis-store", "data"),
)
def sync_graph_legend_classes(vis_data):
    vis = set(vis_data or [])
    mat_classes = [
        "mat-cb-item mat-cb-item--on" if spec["id"]["mat"] in vis
        else "mat-cb-item mat-cb-item--off"
        for spec in ctx.outputs_list[0]
    ]
    all_class = (
        "mat-cb-item mat-cb-item--on" if vis == set(MATERIALS)
        else "mat-cb-item mat-cb-item--off"
    )
    return mat_classes, [all_class] * len(ctx.outputs_list[1])


# ─── Reset filtres ────────────────────────────────────────────────────────────
@app.callback(
    Output("mat-vis-store",   "data",  allow_duplicate=True),
    Output("filter-batch",    "value"),
    Output("filter-material", "value"),
    Input("btn-reset", "n_clicks"),
    prevent_initial_call=True,
)
def reset_filters(_):
    return list(MATERIALS), None, None


if __name__ == "__main__":
    PORT  = int(os.environ.get("PORT", 8050))
    DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=PORT, debug=DEBUG)
