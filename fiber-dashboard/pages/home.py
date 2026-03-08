from dash import html
import dash_bootstrap_components as dbc

NAV_CARDS = [
    {
        "href": "/overview",
        "icon": "📊",
        "color": "#2E86AB",
        "title": "Vue d'ensemble",
        "desc": "Statistiques globales, répartition par matériau, statuts de traitement et tableau récapitulatif des échantillons.",
        "badge": "Démarrer ici",
    },
    {
        "href": "/microstructure",
        "icon": "🔬",
        "color": "#2A9D8F",
        "title": "Microstructure",
        "desc": "Distributions morphologiques des fibres (diamètre, longueur, courbure), orientations 3D et figures de pôle.",
        "badge": "Exploration",
    },
    {
        "href": "/properties",
        "icon": "🔊",
        "color": "#E76F51",
        "title": "Propriétés",
        "desc": "Propriétés acoustiques et thermiques mesurées, courbes d'absorption, corrélations et régression microstructure–propriétés.",
        "badge": "Résultats",
    },
    {
        "href": "/algorithm",
        "icon": "⚙️",
        "color": "#6A4C93",
        "title": "Algorithme",
        "desc": "Sensibilité aux paramètres de segmentation (seuil de misorientation, directions), robustesse au bruit et sous-échantillonnage.",
        "badge": "Validation",
    },
]


def _nav_card(card: dict) -> html.A:
    return html.A(
        href=card["href"],
        className="home-nav-card",
        style={"--card-accent": card["color"]},
        children=html.Div([
            html.Div([
                html.Span(card["icon"], className="home-card-icon"),
                html.Span(card["badge"], className="home-card-badge",
                          style={"background": card["color"]}),
            ], className="home-card-header"),
            html.H3(card["title"], className="home-card-title"),
            html.P(card["desc"], className="home-card-desc"),
            html.Div([
                html.Span("Accéder", className="home-card-cta"),
                html.Span("→", className="home-card-arrow"),
            ], className="home-card-footer"),
        ], className="home-card-inner"),
    )


def layout() -> html.Div:
    return html.Div([

        # ── Hero ─────────────────────────────────────────────────────────────
        html.Div([
            html.Div([
                html.Div([
                    html.Span("◈", className="hero-logo-icon"),
                    html.Span("FiberScope", className="hero-logo-text"),
                ], className="hero-logo"),
                html.H1(
                    "Analyse de microstructure fibreuse",
                    className="hero-title",
                ),
                html.P(
                    "Plateforme de visualisation et d'interprétation des données "
                    "issues de la tomographie µ-CT de matériaux fibreux recyclés. "
                    "Développée dans le cadre du projet de recherche MSME — UMR 8208 CNRS.",
                    className="hero-subtitle",
                ),
                html.Div([
                    html.Div([
                        html.Span("🎓", style={"marginRight": "6px"}),
                        "ESIEE Paris · E4 DSIA",
                    ], className="hero-tag"),
                    html.Div([
                        html.Span("🏛️", style={"marginRight": "6px"}),
                        "Université Gustave Eiffel",
                    ], className="hero-tag"),
                    html.Div([
                        html.Span("🔬", style={"marginRight": "6px"}),
                        "Optimisation acoustique & thermique",
                    ], className="hero-tag"),
                ], className="hero-tags"),
            ], className="hero-content"),
        ], className="hero-section"),

        # ── Context box ──────────────────────────────────────────────────────
        html.Div([
            html.Div([
                html.H2("Objectif du projet", className="home-section-title"),
                html.P(
                    "Ce dashboard permet d'explorer les liens entre la microstructure "
                    "3D de matériaux fibreux recyclés (Nylon, Carbone, Verre, PET, Chanvre…) "
                    "et leurs propriétés acoustiques et thermiques mesurées. "
                    "L'algorithme de segmentation µ-CT extrait automatiquement les descripteurs "
                    "morphologiques (diamètre, longueur, orientation, courbure) qui alimentent "
                    "les modèles de régression Johnson-Champoux-Allard.",
                    className="home-context-text",
                ),
                html.Div([
                    html.Div([
                        html.Div("6", className="home-stat-value", style={"color": "#2E86AB"}),
                        html.Div("Matériaux", className="home-stat-label"),
                    ], className="home-stat"),
                    html.Div([
                        html.Div("15+", className="home-stat-value", style={"color": "#2A9D8F"}),
                        html.Div("Descripteurs", className="home-stat-label"),
                    ], className="home-stat"),
                    html.Div([
                        html.Div("4", className="home-stat-value", style={"color": "#E76F51"}),
                        html.Div("Propriétés cibles", className="home-stat-label"),
                    ], className="home-stat"),
                    html.Div([
                        html.Div("µ-CT", className="home-stat-value", style={"color": "#6A4C93"}),
                        html.Div("Tomographie X", className="home-stat-label"),
                    ], className="home-stat"),
                ], className="home-stats-row"),
            ], className="home-context-card"),
        ], className="home-section"),

        # ── Navigation cards ─────────────────────────────────────────────────
        html.Div([
            html.H2("Choisissez un module", className="home-section-title"),
            html.P(
                "Quatre modules indépendants couvrent l'ensemble du pipeline d'analyse.",
                className="home-section-sub",
            ),
            html.Div(
                [_nav_card(c) for c in NAV_CARDS],
                className="home-cards-grid",
            ),
        ], className="home-section"),

        # ── Footer ───────────────────────────────────────────────────────────
        html.Footer([
            html.Span("FiberScope v2.0 · MSME UMR 8208 CNRS · Université Gustave Eiffel · ESIEE Paris",
                      style={"fontSize": "11px", "color": "#8B9BB4"}),
        ], className="home-footer"),

    ], className="home-page")
