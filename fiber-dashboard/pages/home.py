from dash import html

MATERIALS = [
    ("Nylon",       "#2563EB", "Ø 15 µm"),
    ("Carbone",     "#EF4444", "Ø 7 µm"),
    ("Verre",       "#10B981", "Ø 10 µm"),
    ("Cuivre",      "#F59E0B", "Ø 20 µm"),
    ("PET recyclé", "#8B5CF6", "Ø 25 µm"),
    ("Chanvre",     "#059669", "Ø 30 µm"),
]

PIPELINE = [
    ("01", "Acquisition µ-CT",  "Résolution 1–20 µm/voxel, volume 3D"),
    ("02", "Segmentation 3D",   "Algorithme Depriester et al. (2022)"),
    ("03", "Morphologie",       "Diamètre, longueur, orientation"),
    ("04", "Propriétés JCA",    "Résistivité, absorption, thermique"),
    ("05", "Corrélations",      "Régression linéaire, validation"),
]

NAV_CARDS = [
    {
        "href":  "/microstructure",
        "icon":  "🔬",
        "color": "#2563EB",
        "title": "Microstructure",
        "desc":  "Distributions de diamètre et longueur, orientation 3D par figure de pôle stéréographique, et courbes KDE par matériau.",
    },
    {
        "href":  "/acoustique",
        "icon":  "🔊",
        "color": "#10B981",
        "title": "Acoustique & Thermique",
        "desc":  "Courbes d'absorption en fréquence, paramètres du modèle JCA vs porosité, et matrice de corrélation microstructure–propriétés.",
    },
    {
        "href":  "/correlations",
        "icon":  "📈",
        "color": "#8B5CF6",
        "title": "Corrélations",
        "desc":  "Scatter plot interactif sur 15 variables, droite de régression avec R², et validation prédits vs mesurés pour 4 propriétés.",
    },
    {
        "href":  "/algorithme",
        "icon":  "⚙️",
        "color": "#F59E0B",
        "title": "Algorithme",
        "desc":  "Sensibilité des paramètres de segmentation (seuil × directions) et robustesse au bruit et au sous-échantillonnage.",
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
            html.Span("Explorer →", className="home-card-arrow"),
        ],
    )


def layout() -> html.Div:
    return html.Div([

        # ── Top bar ───────────────────────────────────────────────────────
        html.Div([
            html.Div([
                html.Span("◈", className="home-topbar-icon"),
                html.Span("FiberScope", className="home-topbar-name"),
                html.Span("v2.0", className="home-topbar-version"),
            ], className="home-topbar-brand"),
            html.Div([
                html.Span("ESIEE Paris · E4 DSIA", className="home-topbar-tag"),
                html.Span("MSME · UMR 8208 CNRS", className="home-topbar-tag"),
                html.Span("Univ. Gustave Eiffel", className="home-topbar-tag"),
            ], className="home-topbar-tags"),
        ], className="home-topbar"),

        # ── Hero ─────────────────────────────────────────────────────────
        html.Div([
            html.Div([
                html.Div([
                    html.Span("🔬", style={"marginRight": "6px"}),
                    "Analyse microstructure–propriétés · Tomographie µ-CT",
                ], className="hero-eyebrow"),

                html.H1([
                    "Dashboard analytique",
                    html.Br(),
                    html.Span("des matériaux fibreux", className="hero-title-accent"),
                ], className="hero-title"),

                html.P(
                    "Ce dashboard relie quantitativement la microstructure des fibres — "
                    "diamètre, longueur, orientation, porosité — aux propriétés acoustiques "
                    "et thermiques du matériau. Les données proviennent d'une segmentation 3D "
                    "par tomographie µ-CT sur 6 matériaux et 26 échantillons.",
                    className="hero-subtitle",
                ),

                html.Div([
                    html.Div([
                        html.Div("26", className="hero-stat-num", style={"color": "#2563EB"}),
                        html.Div("échantillons analysés", className="hero-stat-label"),
                    ], className="hero-stat"),
                    html.Div([
                        html.Div("4 952", className="hero-stat-num", style={"color": "#10B981"}),
                        html.Div("fibres segmentées", className="hero-stat-label"),
                    ], className="hero-stat"),
                    html.Div([
                        html.Div("2 983", className="hero-stat-num", style={"color": "#8B5CF6"}),
                        html.Div("contacts fibre-fibre", className="hero-stat-label"),
                    ], className="hero-stat"),
                ], className="hero-stats"),

            ], className="hero-left"),

            # Panneau matériaux
            html.Div([
                html.Div("Matériaux du jeu de données", className="data-panel-header"),
                html.Div([
                    html.Div([
                        html.Span(className="mat-dot", style={"background": color}),
                        html.Span(name, className="mat-name"),
                        html.Span(diam, className="mat-diam"),
                    ], className="mat-row")
                    for name, color, diam in MATERIALS
                ], className="mat-list"),
                html.Div([
                    html.Div([
                        html.Span("6", className="data-stat-num", style={"color": "#2563EB"}),
                        html.Span("matériaux distincts", className="data-stat-label"),
                    ], className="data-stat-row"),
                    html.Div([
                        html.Span("3", className="data-stat-num", style={"color": "#F59E0B"}),
                        html.Span("lots de fabrication", className="data-stat-label"),
                    ], className="data-stat-row"),
                    html.Div([
                        html.Span("7", className="data-stat-num", style={"color": "#10B981"}),
                        html.Span("fichiers CSV de données", className="data-stat-label"),
                    ], className="data-stat-row"),
                ], className="data-panel-footer"),
            ], className="hero-data-panel"),

        ], className="hero-section"),

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
                "FiberScope v2.0 · MSME UMR 8208 CNRS · Université Gustave Eiffel · ESIEE Paris E4 DSIA",
                className="footer-text",
            ),
        ], className="home-footer"),

    ], className="home-page")
