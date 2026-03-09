from dash import html

MATERIALS = [
    ("Nylon",       "#2E86AB", "Ø 15 µm"),
    ("Carbone",     "#2A9D8F", "Ø 7 µm"),
    ("Verre",       "#5B9BD5", "Ø 10 µm"),
    ("Cuivre",      "#E76F51", "Ø 20 µm"),
    ("PET recyclé", "#E9C46A", "Ø 25 µm"),
    ("Chanvre",     "#57CC99", "Ø 30 µm"),
]

PIPELINE = [
    ("01", "Acquisition µ-CT",  "1–20 µm/voxel · volume 3D"),
    ("02", "Segmentation 3D",   "Depriester et al. (2022)"),
    ("03", "Morphologie",       "Diamètre · longueur · orient."),
    ("04", "Propriétés JCA",    "Résistivité · absorption"),
    ("05", "Corrélations",      "Régression · validation"),
]

NAV_CARDS = [
    {
        "href": "/overview",
        "icon": "📊",
        "color": "#2E86AB",
        "title": "Vue d'ensemble",
        "desc": "Statistiques globales, répartition matériaux, suivi des traitements.",
    },
    {
        "href": "/microstructure",
        "icon": "🔬",
        "color": "#2A9D8F",
        "title": "Microstructure",
        "desc": "Diamètre, longueur, courbure, orientation 3D et figures de pôle.",
    },
    {
        "href": "/properties",
        "icon": "🔊",
        "color": "#E76F51",
        "title": "Propriétés",
        "desc": "Absorption acoustique, perméabilité thermique, modèle JCA.",
    },
    {
        "href": "/algorithm",
        "icon": "⚙️",
        "color": "#6A4C93",
        "title": "Algorithme",
        "desc": "Paramètres de segmentation, robustesse au bruit et résolution.",
    },
    {
        "href": "/quality",
        "icon": "🔍",
        "color": "#E9C46A",
        "title": "Contrôle qualité",
        "desc": "Anomalies de scan, taux de résolution, détection automatique.",
    },
]


def _pipeline_step(num, title, desc):
    return html.Div([
        html.Div(num, className="step-num"),
        html.Div(title, className="step-title"),
        html.Div(desc, className="step-desc"),
    ], className="pipeline-step")


def _nav_card(card):
    return html.A(
        href=card["href"],
        className="home-nav-card",
        style={"--card-accent": card["color"]},
        children=[
            html.Span(card["icon"], className="home-card-icon"),
            html.H3(card["title"], className="home-card-title"),
            html.P(card["desc"], className="home-card-desc"),
            html.Span("Accéder →", className="home-card-arrow"),
        ],
    )


def layout() -> html.Div:
    return html.Div([

        # ── Hero ─────────────────────────────────────────────────────────
        html.Div([
            html.Div([
                # Logo
                html.Div([
                    html.Span("◈", className="hero-logo-icon"),
                    html.Span("FiberScope", className="hero-logo-text"),
                    html.Span("v2.0", className="hero-logo-version"),
                ], className="hero-logo"),

                # Titre principal
                html.H1([
                    "Analyse microstructure–propriétés",
                    html.Br(),
                    html.Span(
                        "des matériaux fibreux recyclés",
                        className="hero-title-accent",
                    ),
                ], className="hero-title"),

                # Description scientifique
                html.P(
                    "Tomographie µ-CT · Segmentation 3D · Modèle JCA. "
                    "Ce projet relie quantitativement la microstructure des fibres — "
                    "diamètre, orientation, porosité — aux propriétés acoustiques "
                    "et thermiques du matériau final.",
                    className="hero-subtitle",
                ),

                # Tags institutionnels
                html.Div([
                    html.Span("ESIEE Paris · E4 DSIA", className="hero-tag"),
                    html.Span("MSME · UMR 8208 CNRS", className="hero-tag"),
                    html.Span("Univ. Gustave Eiffel", className="hero-tag"),
                ], className="hero-tags"),

            ], className="hero-left"),

            # Panneau de données (côté droit)
            html.Div([
                html.Div("Jeu de données", className="data-panel-header"),
                html.Div([
                    html.Div([
                        html.Span(
                            className="mat-dot",
                            style={"background": color},
                        ),
                        html.Span(name, className="mat-name"),
                        html.Span(diam, className="mat-diam"),
                    ], className="mat-row")
                    for name, color, diam in MATERIALS
                ], className="mat-list"),
                html.Div([
                    html.Div([
                        html.Span("26", className="data-stat-num",
                                  style={"color": "#2E86AB"}),
                        html.Span("échantillons", className="data-stat-label"),
                    ], className="data-stat-row"),
                    html.Div([
                        html.Span("4 952", className="data-stat-num",
                                  style={"color": "#2A9D8F"}),
                        html.Span("fibres segmentées", className="data-stat-label"),
                    ], className="data-stat-row"),
                    html.Div([
                        html.Span("2 983", className="data-stat-num",
                                  style={"color": "#E76F51"}),
                        html.Span("contacts fibre-fibre", className="data-stat-label"),
                    ], className="data-stat-row"),
                ], className="data-panel-footer"),
            ], className="hero-data-panel"),

        ], className="hero-inner"),

        # ── Pipeline ─────────────────────────────────────────────────────
        html.Div([
            html.Div("Pipeline d'analyse", className="section-eyebrow"),
            html.Div(
                [_pipeline_step(*s) for s in PIPELINE],
                className="pipeline-strip",
            ),
        ], className="pipeline-section"),

        # ── Modules ──────────────────────────────────────────────────────
        html.Div([
            html.Div("Modules d'exploration", className="section-eyebrow"),
            html.Div(
                [_nav_card(c) for c in NAV_CARDS],
                className="home-cards-grid",
            ),
        ], className="home-cards-section"),

        # ── Footer ───────────────────────────────────────────────────────
        html.Footer([
            html.Span(
                "FiberScope v2.0 · MSME UMR 8208 CNRS · Université Gustave Eiffel · ESIEE Paris",
                className="footer-text",
            ),
        ], className="home-footer"),

    ], className="home-page")
