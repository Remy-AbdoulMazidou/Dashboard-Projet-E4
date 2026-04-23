"""
Génère le PDF de documentation du projet.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs", "documentation_projet.pdf")

BLUE   = colors.HexColor('#3B82F6')
ORANGE = colors.HexColor('#F97316')
DARK   = colors.HexColor('#111827')
MUTED  = colors.HexColor('#6B7280')
LIGHT  = colors.HexColor('#F3F4F6')
GREEN  = colors.HexColor('#16A34A')
BORDER = colors.HexColor('#E5E7EB')

doc = SimpleDocTemplate(
    OUT, pagesize=A4,
    leftMargin=2.2*cm, rightMargin=2.2*cm,
    topMargin=2*cm, bottomMargin=2*cm,
)

S = getSampleStyleSheet()

def style(name='Normal', **kw):
    return ParagraphStyle(name, parent=S[name], **kw)

TITLE1 = style('Heading1', fontSize=18, textColor=DARK, spaceAfter=6,
               spaceBefore=18, fontName='Helvetica-Bold')
TITLE2 = style('Heading2', fontSize=13, textColor=BLUE, spaceAfter=4,
               spaceBefore=14, fontName='Helvetica-Bold')
TITLE3 = style('Heading3', fontSize=11, textColor=DARK, spaceAfter=4,
               spaceBefore=10, fontName='Helvetica-Bold')
BODY   = style('Normal', fontSize=10, textColor=DARK, spaceAfter=5,
               leading=15, alignment=TA_JUSTIFY)
BODY_L = style('Normal', fontSize=10, textColor=DARK, spaceAfter=4,
               leading=15, alignment=TA_LEFT)
SMALL  = style('Normal', fontSize=9, textColor=MUTED, spaceAfter=4, leading=13)
CODE   = style('Normal', fontSize=9, fontName='Courier', textColor=DARK,
               backColor=colors.HexColor('#F9FAFB'), spaceAfter=3, leading=13)
BULLET = style('Normal', fontSize=10, textColor=DARK, spaceAfter=3,
               leading=14, leftIndent=14, bulletIndent=0)

def H1(t): return Paragraph(t, TITLE1)
def H2(t): return Paragraph(t, TITLE2)
def H3(t): return Paragraph(t, TITLE3)
def P(t):  return Paragraph(t, BODY)
def Pl(t): return Paragraph(t, BODY_L)
def Sm(t): return Paragraph(t, SMALL)
def Co(t): return Paragraph(t, CODE)
def Bu(t): return Paragraph(f'• &nbsp; {t}', BULLET)
def sp(n=1): return Spacer(1, n * 0.35 * cm)
def hr(): return HRFlowable(width='100%', thickness=0.5, color=BORDER, spaceAfter=6, spaceBefore=6)

def info_box(label, content, color=BLUE):
    data = [[
        Paragraph(f'<b>{label}</b>', ParagraphStyle('', fontSize=9, textColor=color, fontName='Helvetica-Bold')),
        Paragraph(content, ParagraphStyle('', fontSize=9.5, textColor=DARK, leading=14)),
    ]]
    t = Table(data, colWidths=[3.5*cm, 12*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,0), colors.HexColor(color.hexval()+'18' if hasattr(color,'hexval') else '#EFF6FF')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ('LINEBELOW', (0,0), (-1,0), 0.5, BORDER),
        ('ROUNDEDCORNERS', [4]),
    ]))
    return t

def table_cols(headers, rows, col_widths=None):
    head_row = [Paragraph(f'<b>{h}</b>', ParagraphStyle('', fontSize=9, textColor=MUTED,
                fontName='Helvetica-Bold')) for h in headers]
    data_rows = []
    for row in rows:
        data_rows.append([
            Paragraph(str(c), ParagraphStyle('', fontSize=9, textColor=DARK,
                      fontName='Courier' if i == 0 else 'Helvetica', leading=12))
            for i, c in enumerate(row)
        ])
    t = Table([head_row] + data_rows, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), LIGHT),
        ('LINEBELOW', (0,0), (-1,0), 1, BORDER),
        ('LINEBELOW', (0,1), (-1,-1), 0.3, BORDER),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 7),
        ('RIGHTPADDING', (0,0), (-1,-1), 7),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, LIGHT]),
    ]))
    return t


# ─── CONTENU ───────────────────────────────────────────────────────────────
story = []

# Couverture
story += [
    sp(2),
    Paragraph('<b>Documentation du projet</b>', ParagraphStyle('', fontSize=26,
        textColor=DARK, fontName='Helvetica-Bold', alignment=TA_CENTER)),
    sp(0.5),
    Paragraph('Analyse de microstructure fibreuse par microtomographie X', ParagraphStyle('',
        fontSize=14, textColor=MUTED, alignment=TA_CENTER, leading=20)),
    sp(0.5),
    Paragraph('Comparaison Méthode Dragonfly vs Méthode MATLAB', ParagraphStyle('',
        fontSize=12, textColor=BLUE, alignment=TA_CENTER, fontName='Helvetica-Bold')),
    sp(1),
    hr(),
    sp(0.5),
    Paragraph('Projet E4 DSIA — ESIEE Paris · Partenariat laboratoire MSME (UMR 8208 CNRS)',
        ParagraphStyle('', fontSize=10, textColor=MUTED, alignment=TA_CENTER)),
    Paragraph('Rémy ABDOUL MAZIDOU — Dashboard et analyse comparative',
        ParagraphStyle('', fontSize=10, textColor=MUTED, alignment=TA_CENTER)),
    sp(3),
]

# ── 1. CONTEXTE ──────────────────────────────────────────────────────────────
story += [H1('1. Contexte du projet'), hr()]

story += [
    P("Ce projet s'inscrit dans le cadre d'un partenariat entre l'ESIEE Paris et le laboratoire "
      "MSME (Mécanique et Sciences des Matériaux et des Structures, UMR 8208 CNRS). "
      "L'objectif est d'analyser la microstructure d'un matériau fibreux à partir d'images obtenues par "
      "microtomographie X (µCT)."),
    sp(),
    P("La microtomographie X est une technique d'imagerie 3D non destructive. Elle fonctionne comme un "
      "scanner médical mais à très haute résolution — ici <b>10 µm par voxel</b>. Le scan produit un volume "
      "3D de l'échantillon dans lequel on peut distinguer les fibres individuelles, leur forme et leur "
      "organisation dans l'espace."),
    sp(),
    P("Deux membres du groupe ont analysé ces images avec des outils différents de façon indépendante. "
      "Le but de ce travail est de comparer leurs résultats pour valider les conclusions sur le matériau."),
]

story += [sp(), H2('Membres du groupe impliqués')]
story += [
    Bu('<b>Antoine & Aymen</b> — Méthode Dragonfly ORS : segmentation 3D, extraction du squelette, '
       'mesure d\'épaisseur locale par ray-tracing, orientation via angles sphériques.'),
    Bu('<b>Nolhan</b> — Méthode MATLAB : analyse morphologique par regionprops3, '
       'axes principaux (PAL1/2/3), angles d\'Euler pour l\'orientation.'),
    Bu('<b>Rémy</b> — Création du dashboard de comparaison et analyse des données.'),
    sp(),
]

# ── 2. DONNÉES ──────────────────────────────────────────────────────────────
story += [H1('2. Les données'), hr()]

story += [
    P("Trois fichiers de données sont utilisés dans le projet. Ils se trouvent dans le dossier "
      "<font face='Courier'>vrai-data/</font>."),
    sp(),
]

story += [H2('2.1 Méthode Dragonfly — donnee.csv')]
story += [
    Pl('<font face="Courier">vrai-data/antoine-aymen/donnee.csv</font> · 537 lignes · séparateur point-virgule'),
    sp(0.5),
    table_cols(
        ['Colonne', 'Unité', 'Description'],
        [
            ('Label Index',  '—',    'Identifiant de l\'objet segmenté'),
            ('Voxel count',  'vox',  'Volume de l\'objet en voxels'),
            ('Volume (mm³)', 'mm³',  'Volume converti (résolution 10 µm/vox)'),
            ('Phi (°)',      '°',    'Angle polaire — 0° = vertical, 90° = horizontal'),
            ('Theta (°)',    '°',    'Angle azimutal dans le plan horizontal'),
            ('MIL',          '—',    'Mean Intercept Length — non exploité'),
            ('SVD',          '—',    'Non renseigné dans ce dataset'),
        ],
        col_widths=[3.5*cm, 2*cm, 10*cm]
    ),
    sp(),
    Sm('Note : pour obtenir l\'inclinaison depuis l\'horizontale, on calcule angle_h = 90 − Phi.'),
    sp(),
]

story += [H2('2.2 Méthode Dragonfly — diametre.csv')]
story += [
    Pl('<font face="Courier">vrai-data/antoine-aymen/diametre.csv</font> · ~16 millions de lignes · 785 Mo · séparateur point-virgule'),
    sp(0.5),
    table_cols(
        ['Colonne', 'Unité', 'Description'],
        [
            ('Thickness (mm)', 'mm', 'Épaisseur locale mesurée par ray-tracing en chaque point du squelette de fibre. Une ligne = un point de mesure.'),
        ],
        col_widths=[3.5*cm, 2*cm, 10*cm]
    ),
    sp(0.5),
    Sm('Ce fichier est très volumineux car il contient un point de mesure par voxel du squelette. '
       'Dans le dashboard, on charge 1 point sur 100 (sous-échantillonnage) et on met en cache le résultat '
       'dans .thick_cache.npy pour ne pas recharger à chaque démarrage.'),
    sp(),
]

story += [H2('2.3 Méthode MATLAB — Resultats_Fibres.xlsx')]
story += [
    Pl('<font face="Courier">vrai-data/nolhan/Resultats_Fibres.xlsx</font> · 405 lignes'),
    sp(0.5),
    table_cols(
        ['Colonne', 'Unité', 'Description'],
        [
            ('Volume',                'vox',  'Volume de l\'objet en voxels'),
            ('Centroid_1/2/3',        'vox',  'Coordonnées du centre de masse (x, y, z)'),
            ('EquivDiameter',         'vox',  'Diamètre de la sphère de même volume'),
            ('PrincipalAxisLength_1', 'vox',  'PAL₁ — axe le plus long (≈ longueur de la fibre)'),
            ('PrincipalAxisLength_2', 'vox',  'PAL₂ — axe intermédiaire'),
            ('PrincipalAxisLength_3', 'vox',  'PAL₃ — axe le plus court (≈ diamètre de la fibre)'),
            ('Orientation_1/2/3',     '°',    'Angles d\'Euler — orientation dans l\'espace 3D'),
            ('Solidity',              '—',    'Volume / volume convexe (1 = objet parfaitement convexe)'),
            ('SurfaceArea',           'vox²', 'Aire de surface de l\'objet'),
            ('ConvexVolume',          'vox',  'Volume de l\'enveloppe convexe'),
        ],
        col_widths=[3.5*cm, 2*cm, 10*cm]
    ),
    sp(0.5),
    Sm('Résolution 10 µm/voxel — pour convertir en µm, multiplier PAL et EquivDiameter par 10. '
       'Pour l\'orientation, on utilise Orientation_2 en valeur absolue comme angle depuis l\'horizontale.'),
    sp(),
]

# ── 3. CLASSIFICATION DRAGONFLY ──────────────────────────────────────────────
story += [H1('3. Classification des objets (Dragonfly)'), hr()]

story += [
    P("Dragonfly détecte tous les objets segmentés dans le scan — pas uniquement les fibres. "
      "On les classe par taille de voxels pour ne garder que ce qui nous intéresse :"),
    sp(0.5),
    table_cols(
        ['Catégorie', 'Seuil (voxels)', 'Description'],
        [
            ('Bruit',       '0 – 5',            'Artefacts, bruit numérique'),
            ('Fragment',    '6 – 100',           'Petits morceaux, non exploitables'),
            ('Fibre',       '101 – 100 000',     '→ Objets retenus pour l\'analyse'),
            ('Gros objet',  '100 001 – 1 000 000', 'Agrégats, fibres fusionnées'),
            ('Matrice',     '> 1 000 000',       'Structure principale du matériau'),
        ],
        col_widths=[3.5*cm, 4*cm, 8*cm]
    ),
    sp(0.5),
    P("Sur 537 objets détectés, <b>95 sont classifiés comme fibres</b> et retenus pour l\'analyse. "
      "MATLAB ne fait pas ce filtrage — il garde les 405 objets segmentés tels quels."),
    sp(),
]

# ── 4. COMPARABILITÉ ─────────────────────────────────────────────────────────
story += [H1('4. Comparabilité des deux méthodes'), hr()]

story += [
    P("Les deux méthodes n\'ont pas été conçues pour produire les mêmes mesures. "
      "Voici ce qu\'on peut comparer directement et ce qui nécessite des précautions :"),
    sp(0.5),
    table_cols(
        ['Grandeur', 'Comparable ?', 'Explication'],
        [
            ('Orientation',        'Oui',                  'Les deux mesurent l\'angle dans l\'espace. Résultats cohérents.'),
            ('Taille (directe)',   'Non directement',      'Dragonfly = épaisseur skeleton, MATLAB = PAL₃. Métriques différentes → écart ×2 normal.'),
            ('Taille (via volume)','Oui (~10% d\'écart)',  'Diamètre équivalent d = (6V/π)^(1/3) — mesure commune aux deux méthodes.'),
            ('Nombre de fibres',   'Non',                  'Dragonfly filtre 101–100k vox, MATLAB garde tout. L\'écart reflète des choix méthodologiques.'),
        ],
        col_widths=[4*cm, 3.5*cm, 8*cm]
    ),
    sp(),
]

# ── 5. RÉSULTATS CLÉS ────────────────────────────────────────────────────────
story += [H1('5. Résultats principaux'), hr()]

story += [
    H2('5.1 Orientation'),
    Bu('<b>Les fibres sont quasi-horizontales</b> dans les deux méthodes.'),
    Bu('Dragonfly : angle médian = 6.3° depuis l\'horizontale.'),
    Bu('MATLAB : angle médian = 1.3° depuis l\'horizontale.'),
    Bu('Écart de ~5° expliqué par les conventions d\'angle différentes et les objets segmentés distincts.'),
    Bu('Distribution azimutale uniforme → pas de direction préférentielle dans le plan (isotropie).'),
    sp(),
    H2('5.2 Taille des fibres'),
    Bu('Dragonfly — épaisseur skeleton médiane : ~120 µm.'),
    Bu('MATLAB — PAL₃ médiane : ~59 µm. Écart ×2 attendu (métriques différentes).'),
    Bu('Via le volume : Dragonfly ~93 µm vs MATLAB ~84 µm → ~10% d\'écart seulement.'),
    sp(),
    H2('5.3 Morphologie (MATLAB uniquement)'),
    Bu('Longueur médiane des fibres (PAL₁) : ~160 µm, max ~2 588 µm.'),
    Bu('Rapport d\'aspect médian (PAL₁/PAL₃) : ~2.6 — fibres allongées.'),
    Bu('Solidité médiane : 0.68 — corrélation négative avec le diamètre (r ≈ −0.43).'),
    Bu('Répartition spatiale homogène sur ~2 mm × 2 mm × 1 mm.'),
    sp(),
]

# ── 6. DASHBOARD ─────────────────────────────────────────────────────────────
story += [H1('6. Le dashboard'), hr()]

story += [
    P("Le dashboard est une application web interactive développée avec <b>Plotly Dash</b> (Python). "
      "Il tourne en local sur le port 8051."),
    sp(),
]

story += [H2('6.1 Structure des fichiers')]
story += [
    table_cols(
        ['Fichier / Dossier', 'Rôle'],
        [
            ('dashboard-reel/app.py',         'Code principal — données, graphiques, callbacks, layout'),
            ('dashboard-reel/assets/style.css','CSS personnalisé (polices, scrollbar, tabs)'),
            ('vrai-data/antoine-aymen/',       'Données Dragonfly (donnee.csv, diametre.csv)'),
            ('vrai-data/nolhan/',              'Données MATLAB (Resultats_Fibres.xlsx)'),
            ('requirements.txt',               'Dépendances Python'),
        ],
        col_widths=[6*cm, 9.5*cm]
    ),
    sp(),
]

story += [H2('6.2 Les onglets')]
story += [
    table_cols(
        ['Onglet', 'Contenu'],
        [
            ('Contexte & méthodes', 'Présentation du projet, des deux méthodes, classification Dragonfly'),
            ('Orientation',         'Histogrammes d\'inclinaison (toggle interactif), distribution azimutale'),
            ('Comparaison',         'Tableau point par point, distributions de taille, comparaison via volume, conclusion'),
            ('Morphologie',         'Volume, longueur, rapport d\'aspect, solidity vs diamètre, carte spatiale'),
            ('Données',             'Dictionnaire complet des colonnes et fichiers avec unités'),
        ],
        col_widths=[4*cm, 11.5*cm]
    ),
    sp(),
]

story += [H2('6.3 Lancer le dashboard')]
story += [
    Co('# Depuis le dossier TestDashboardProjet/'),
    Co('source venv/bin/activate'),
    Co('python dashboard-reel/app.py'),
    Co('# → Ouvrir http://localhost:8051 dans un navigateur'),
    sp(0.5),
    Sm('Le premier démarrage charge diametre.csv (~15 secondes) et crée un cache .thick_cache.npy. '
       'Les démarrages suivants sont instantanés.'),
    sp(),
]

story += [H2('6.4 Dépendances principales')]
story += [
    table_cols(
        ['Package', 'Version', 'Usage'],
        [
            ('dash',        '2.17+', 'Framework web interactif'),
            ('plotly',      '5.x',   'Graphiques'),
            ('pandas',      '2.x',   'Chargement et manipulation des données'),
            ('numpy',       '1.x',   'Calculs numériques'),
            ('openpyxl',    '3.x',   'Lecture du fichier .xlsx MATLAB'),
        ],
        col_widths=[3.5*cm, 2.5*cm, 9.5*cm]
    ),
    sp(),
]

# ── 7. POINTS TECHNIQUES ─────────────────────────────────────────────────────
story += [H1('7. Points techniques importants'), hr()]

story += [
    H2('Chargement de diametre.csv (785 Mo)'),
    P("Le fichier est trop grand pour être chargé en mémoire d\'un coup. "
      "On le lit par chunks de 1 million de lignes et on garde 1 ligne sur 100 par chunk, "
      "ce qui donne ~164 000 points de mesure. Le résultat est sauvegardé en .npy pour les "
      "rechargements suivants."),
    sp(),
    H2('Convention d\'angles'),
    Bu('Dragonfly — Phi : 0° = vertical, 90° = horizontal → angle_h = 90 − Phi'),
    Bu('MATLAB — Orientation_2 : directement depuis l\'horizontale → angle_h = |Orientation_2|'),
    Bu('Les deux sont ramenés à la même convention pour comparaison.'),
    sp(),
    H2('Comparaison de taille via le volume'),
    P("Pour comparer les tailles de fibres de façon équitable, on calcule le <b>diamètre équivalent "
      "d'une sphère de même volume</b> : d = (6V/π)^(1/3). "
      "Pour Dragonfly : V en mm³ → µm³ (×10⁹). Pour MATLAB : V en voxels → µm³ (×1 000)."),
    sp(),
]

# ── 8. QUESTIONS FRÉQUENTES ──────────────────────────────────────────────────
story += [H1('8. Questions fréquentes'), hr()]

story += [
    H3('Pourquoi 95 fibres Dragonfly vs 405 MATLAB ?'),
    P("Dragonfly applique un filtre de taille (101–100 000 voxels) pour éliminer le bruit et "
      "les agrégats. MATLAB ne filtre pas. Si on applique le même filtre aux données MATLAB, "
      "on passe à ~374 objets. Le reste de l\'écart vient des algorithmes de segmentation différents."),
    sp(),
    H3('L\'écart de taille ×2 est-il une erreur ?'),
    P("Non. Dragonfly mesure l\'épaisseur locale en chaque point du squelette (mesure ponctuelle). "
      "MATLAB mesure PAL₃ = l\'axe le plus court de l\'ellipsoïde ajusté sur la fibre entière "
      "(mesure globale). Ce ne sont pas la même chose. Via le volume, l\'écart tombe à ~10%."),
    sp(),
    H3('Pourquoi l\'angle médian diffère de ~5° entre les deux méthodes ?'),
    P("Les conventions d\'angle sont différentes (angle polaire vs angle d\'Euler) et les objets "
      "segmentés ne sont pas exactement les mêmes. La conclusion reste identique : les fibres "
      "sont quasi-horizontales dans les deux cas."),
    sp(),
    H3('Le matériau est-il isotrope ?'),
    P("Dans le plan horizontal oui — la distribution azimutale est uniforme dans les deux méthodes. "
      "Hors plan, les fibres sont préférentiellement horizontales (faible inclinaison), "
      "ce qui signifie une anisotropie verticale/horizontale."),
    sp(),
]

doc.build(story)
print(f"PDF généré : {OUT}")
