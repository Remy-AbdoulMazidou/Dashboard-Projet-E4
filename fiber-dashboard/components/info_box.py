"""Reusable explanation callout components."""
from dash import html


def info_box(text: str, icon: str = "ℹ️") -> html.Div:
    """Blue informational callout."""
    return html.Div([
        html.Span(icon, className="callout-icon"),
        html.Span(text, className="callout-text"),
    ], className="callout callout--info")


def guide_box(title: str, points: list) -> html.Div:
    """Green interpretation guide."""
    items = [html.Li(p, className="callout-list-item") for p in points]
    return html.Div([
        html.Div([
            html.Span("📖", className="callout-icon"),
            html.Span(title, className="callout-title"),
        ], className="callout-header"),
        html.Ul(items, className="callout-list"),
    ], className="callout callout--guide")


def warn_box(text: str) -> html.Div:
    """Amber warning callout."""
    return html.Div([
        html.Span("⚠️", className="callout-icon"),
        html.Span(text, className="callout-text"),
    ], className="callout callout--warn")


def conclusion_box(title: str, text: str) -> html.Div:
    """Purple conclusion callout at the end of a section."""
    return html.Div([
        html.Div([
            html.Span("💡", className="callout-icon"),
            html.Span(title, className="callout-title"),
        ], className="callout-header"),
        html.P(text, className="callout-text", style={"margin": 0}),
    ], className="callout callout--conclusion")


def chart_header(title: str, description: str) -> html.Div:
    """Title + description above a graph."""
    return html.Div([
        html.H4(title, className="chart-title"),
        html.P(description, className="chart-desc"),
    ], className="chart-header")
