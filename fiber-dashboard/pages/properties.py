"""Combined page: Acoustique/Thermique + Corrélations — tabs layout."""
from dash import html, dcc

from pages import acoustic_thermal, correlations


def layout() -> html.Div:
    # Ensure callbacks are registered by importing the modules above
    return html.Div([
        html.H2("Propriétés — Acoustique, Thermique & Corrélations", className="page-title"),
        html.P(
            "Propriétés mesurées par matériau, courbes d'absorption en fréquence, "
            "paramètres de transport (JCA) et corrélations microstructure–propriétés.",
            className="page-subtitle",
        ),

        dcc.Tabs(
            id="props-tabs",
            value="acoustic",
            className="dash-tabs-dark",
            children=[
                dcc.Tab(
                    label="🔊 Acoustique & Thermique",
                    value="acoustic",
                    className="dash-tab",
                    selected_className="dash-tab--selected",
                    children=html.Div(
                        acoustic_thermal.layout().children[1:],  # skip H2 title
                        className="tab-content",
                    ),
                ),
                dcc.Tab(
                    label="📈 Corrélations & Régression",
                    value="corr",
                    className="dash-tab",
                    selected_className="dash-tab--selected",
                    children=html.Div(
                        correlations.layout().children[1:],  # skip H2 title
                        className="tab-content",
                    ),
                ),
            ],
        ),
    ], className="page-content")
