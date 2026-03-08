import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import dash
from dash import html, dcc, Input, Output

from components.sidebar import sidebar
from config import PORT, DEBUG

from pages import (
    home,
    overview,
    samples,
    microstructure,
    parameters,
    robustness,
    correlations,
    acoustic_thermal,
    quality,
    algorithm,
    properties,
)

app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    title="FiberScope — MSME",
    update_title=None,
)

# Two-shell layout: home (full-screen) vs dashboard (with sidebar)
app.layout = html.Div([
    dcc.Location(id="url", refresh=False),

    # Full-screen home shell (shown only on /)
    html.Div(id="home-shell"),

    # Sidebar + content shell (shown on all other routes)
    html.Div(
        [
            sidebar(),
            html.Div(
                html.Div(id="page-content", className="page-wrapper"),
                className="main-container",
            ),
        ],
        className="app-shell",
        id="app-shell",
        style={"display": "none"},
    ),
])


ROUTES = {
    "/overview":      overview.layout,
    "/microstructure": microstructure.layout,
    "/properties":    properties.layout,
    "/algorithm":     algorithm.layout,
    # keep legacy routes working
    "/samples":       samples.layout,
    "/parameters":    parameters.layout,
    "/robustness":    robustness.layout,
    "/correlations":  correlations.layout,
    "/acoustic-thermal": acoustic_thermal.layout,
    "/quality":       quality.layout,
}


@app.callback(
    Output("home-shell", "children"),
    Output("home-shell", "style"),
    Output("app-shell", "style"),
    Input("url", "pathname"),
)
def toggle_shells(pathname):
    if pathname is None or pathname == "/":
        return home.layout(), {"display": "block"}, {"display": "none"}
    return [], {"display": "none"}, {"display": "flex"}


@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname"),
)
def render_page(pathname):
    page_fn = ROUTES.get(pathname, overview.layout)
    return page_fn()


server = app.server

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=DEBUG)
