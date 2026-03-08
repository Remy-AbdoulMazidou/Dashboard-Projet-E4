from dash import html
from config import COLORS, APP_TITLE, APP_SUBTITLE


def header() -> html.Div:
    return html.Div(
        [
            html.Div(
                [
                    html.Span("◈", style={"color": COLORS["primary"], "fontSize": "20px", "marginRight": "10px"}),
                    html.Span(APP_TITLE, style={"fontWeight": "700", "fontSize": "16px",
                                                "color": COLORS["text_primary"]}),
                ],
                style={"display": "flex", "alignItems": "center"},
            ),
            html.Div(
                APP_SUBTITLE,
                style={"fontSize": "11px", "color": COLORS["text_secondary"],
                       "marginTop": "2px", "letterSpacing": "0.03em"},
            ),
        ],
        className="app-header",
    )
