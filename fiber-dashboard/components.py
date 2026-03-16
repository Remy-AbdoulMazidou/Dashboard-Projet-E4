from dash import dcc, html
import dash_bootstrap_components as dbc
from config import TABS, PLOT_CONFIG, mat_color
from data import MATERIALS


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
            dcc.Store(id={"type": "mat-store", "graph": graph_id}, data=list(MATERIALS)),
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
    accent = TABS["acoustics"]["bg"]
    return dbc.Col(dbc.Card(style={
        "borderRadius": "12px",
        "border":       "1px solid #E2E8F0",
        "boxShadow":    "0 2px 10px rgba(15,23,42,0.06)",
    }, children=[
        dbc.CardBody(style={"padding": "20px 20px 16px 20px"}, children=[
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
            html.Div(style={"display": "flex", "gap": "14px", "alignItems": "stretch"}, children=[

                html.Div(style={"flex": 1, "minWidth": 0}, children=[
                    dcc.Graph(id="graph-absorption", config=PLOT_CONFIG,
                              style={"height": "320px"}),
                ]),

                html.Div(style={
                    "width": "1px", "backgroundColor": "#E2E8F0",
                    "flexShrink": 0, "borderRadius": "1px",
                }),

                html.Div(style={
                    "width": "175px", "flexShrink": 0,
                    "display": "flex", "flexDirection": "column", "gap": "8px",
                }, children=[
                    html.P("Échantillons à afficher :", style={
                        "fontSize": "11px", "fontWeight": 700,
                        "color": "#334155", "margin": 0,
                    }),
                    dcc.Input(
                        id="acou-search",
                        type="text",
                        placeholder="Rechercher...",
                        debounce=True,
                        style={
                            "width": "100%", "padding": "5px 8px",
                            "border": "1px solid #E2E8F0", "borderRadius": "6px",
                            "fontSize": "11px", "color": "#334155",
                            "boxSizing": "border-box", "outline": "none",
                        },
                    ),
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
