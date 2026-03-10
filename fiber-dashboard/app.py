"""
FiberScope — Point d'entrée principal
Projet E4 DSIA · ESIEE Paris

Architecture :
  app.py         → routing + layout global (sidebar + contenu)
  pages/         → une page par module (overview, microstructure, ...)
  components/    → composants réutilisables (sidebar, KPI, filtres, ...)
  utils/         → chargement données, statistiques, figures
  config.py      → constantes, couleurs, chemins

Intégration de vraies données :
  Remplacer les CSV dans data/ en respectant les colonnes requises.
  Voir README.md pour le dictionnaire des colonnes.
"""

import os
import dash
from dash import dcc, html, Input, Output

from components.sidebar import sidebar
from config import PORT, DEBUG

# Import des pages : déclenche l'enregistrement de tous leurs callbacks
import pages.home as home
import pages.overview as overview
import pages.microstructure as microstructure
import pages.properties as properties_page
import pages.algorithm as algorithm
import pages.quality as quality
import pages.samples as samples_page

app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    title="FiberScope",
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)

server = app.server  # pour gunicorn

app.layout = html.Div([
    dcc.Location(id="url"),
    html.Div([
        sidebar(),
        html.Div(id="page-content", className="main-content"),
    ], className="app-shell"),
])

# Table de routage URL → fonction layout de la page
ROUTES = {
    "/":               home.layout,
    "/overview":       overview.layout,
    "/microstructure": microstructure.layout,
    "/proprietes":     properties_page.layout,
    "/algorithme":     algorithm.layout,
    "/qualite":        quality.layout,
    "/echantillons":   samples_page.layout,
}


@app.callback(Output("page-content", "children"), Input("url", "pathname"))
def route(pathname):
    page_fn = ROUTES.get(pathname, home.layout)
    return page_fn()


if __name__ == "__main__":
    app.run(debug=DEBUG, port=PORT)
