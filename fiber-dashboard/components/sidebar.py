from dash import html, dcc
from config import COLORS

NAV_ITEMS = [
    ("/microstructure", "🔬", "Microstructure"),
    ("/acoustique",     "🔊", "Acoustique & Thermique"),
    ("/correlations",   "📈", "Corrélations"),
    ("/algorithme",     "⚙️",  "Algorithme"),
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

    return html.Div([
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

        # Nav section
        html.Nav([
            html.Div("Analyse", className="sidebar-section-label"),
            *nav_links,
        ], className="sidebar-nav"),

        # Footer
        html.Div(
            html.Div("v2.0 · ESIEE Paris E4 DSIA", className="sidebar-footer-text"),
            className="sidebar-footer",
        ),
    ], className="sidebar")
