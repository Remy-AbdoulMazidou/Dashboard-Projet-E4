"""Combined page: Paramètres de l'algorithme + Robustesse — tabs layout."""
from dash import html, dcc

from pages import parameters, robustness


def layout() -> html.Div:
    # Ensure callbacks are registered by importing the modules above
    return html.Div([
        html.H2("Algorithme — Paramètres & Robustesse", className="page-title"),
        html.P(
            "Sensibilité de la segmentation aux paramètres de l'algorithme "
            "et analyse de robustesse au bruit et au sous-échantillonnage.",
            className="page-subtitle",
        ),

        dcc.Tabs(
            id="algo-tabs",
            value="params",
            className="dash-tabs-dark",
            children=[
                dcc.Tab(
                    label="⚙ Paramètres de segmentation",
                    value="params",
                    className="dash-tab",
                    selected_className="dash-tab--selected",
                    children=html.Div(
                        parameters.layout().children[1:],  # skip the H2 title
                        className="tab-content",
                    ),
                ),
                dcc.Tab(
                    label="🛡 Robustesse & limitations",
                    value="robust",
                    className="dash-tab",
                    selected_className="dash-tab--selected",
                    children=html.Div(
                        robustness.layout().children[1:],  # skip the H2 title
                        className="tab-content",
                    ),
                ),
            ],
        ),
    ], className="page-content")
