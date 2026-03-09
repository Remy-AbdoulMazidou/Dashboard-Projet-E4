from dash import html
from config import COLORS


def kpi_card(icon: str, value: str, label: str, delta: str = None,
             delta_positive: bool = True, color: str = None) -> html.Div:
    accent = color or COLORS["primary"]
    delta_color = COLORS["success"] if delta_positive else COLORS["danger"]
    delta_arrow = "▲" if delta_positive else "▼"

    children = [
        html.Div(icon, className="kpi-icon", style={"color": accent}),
        html.Div(value, className="kpi-value"),
        html.Div(label, className="kpi-label"),
    ]
    if delta:
        children.append(
            html.Div(
                [html.Span(delta_arrow, style={"marginRight": "4px"}), html.Span(delta)],
                className="kpi-delta",
                style={"color": delta_color},
            )
        )

    return html.Div(children, className="kpi-card", style={"--kpi-color": accent})
