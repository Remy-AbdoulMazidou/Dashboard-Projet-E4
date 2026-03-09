from dash import html, dcc
from config import COLORS

NAV_ITEMS = [
    ("/overview",      "📊", "Vue d'ensemble"),
    ("/microstructure","🔬", "Microstructure"),
    ("/properties",    "🔊", "Propriétés"),
    ("/algorithm",     "⚙️",  "Algorithme"),
    ("/quality",       "🔍", "Contrôle qualité"),
]


def sidebar() -> html.Div:
    nav_links = [
        dcc.Link(
            href=href,
            children=html.Div(
                [
                    html.Span(icon, className="nav-icon"),
                    html.Span(label, className="nav-label"),
                ],
                className="nav-item",
            ),
            className="nav-link",
            id=f"nav-{href.strip('/')}",
        )
        for href, icon, label in NAV_ITEMS
    ]

    return html.Div(
        [
            # Logo / brand
            html.A(
                href="/",
                className="sidebar-brand",
                children=html.Div([
                    html.Span("◈", className="brand-icon"),
                    html.Div([
                        html.Div("FiberScope", className="brand-name"),
                        html.Div("MSME · UMR 8208", className="brand-sub"),
                    ]),
                ], className="brand-inner"),
            ),

            # Nav links
            html.Nav(nav_links, className="sidebar-nav"),

            # Footer
            html.Div(
                [
                    html.Div("v2.0 · ESIEE Paris E4 DSIA",
                             style={"fontSize": "10px", "color": COLORS["text_secondary"],
                                    "textAlign": "center"}),
                ],
                className="sidebar-footer",
            ),
        ],
        className="sidebar",
    )
