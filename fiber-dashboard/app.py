import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import dash
from dash import html, dcc, Input, Output

from components.sidebar import sidebar
from config import PORT, DEBUG

from pages import home, microstructure, algorithme
from pages import acoustic_thermal, correlations

app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    title="FiberScope — MSME",
    update_title=None,
)

# Two-shell layout: home (full-screen) vs dashboard (with sidebar)
app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    html.Div(id="_nav_active", style={"display": "none"}),

    # Full-screen home (shown only on /)
    html.Div(id="home-shell"),

    # Sidebar + content (shown on all other routes)
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
    "/microstructure": microstructure.layout,
    "/acoustique":     acoustic_thermal.layout,
    "/correlations":   correlations.layout,
    "/algorithme":     algorithme.layout,
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
    page_fn = ROUTES.get(pathname, microstructure.layout)
    return page_fn()


app.clientside_callback(
    """
    function(pathname) {
        document.querySelectorAll('.nav-link').forEach(function(el) {
            el.classList.remove('active');
        });
        if (pathname && pathname !== '/') {
            document.querySelectorAll('.nav-link').forEach(function(el) {
                if (el.getAttribute('href') === pathname) {
                    el.classList.add('active');
                }
            });
        }
        return '';
    }
    """,
    Output("_nav_active", "children"),
    Input("url", "pathname"),
)

server = app.server

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=DEBUG)
