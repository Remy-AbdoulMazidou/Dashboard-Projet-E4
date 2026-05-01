# FiberScope — Dashboard Microstructure Fibreuse

## Contexte du projet
Projet E4 ESIEE Paris en partenariat avec le laboratoire MSME (UMR 8208 CNRS).
Objectif : analyser la microstructure de matériaux fibreux à partir d'images de
microtomographie X, et comparer deux chaînes d'analyse : une pipeline MATLAB
développée au labo et le logiciel commercial Dragonfly.

## Mon rôle
Création du **dashboard analytique comparatif MATLAB vs Dragonfly** (`dashboard-reel/`) :
l'interface qui permet de visualiser et comparer côte à côte les résultats des deux méthodes
sur les mêmes échantillons (orientation des fibres, distribution de diamètre, porosité, etc.).

## Stack technique
- **Dashboard principal** : Python + Dash · `dashboard-reel/app.py` · port **8052**
- **Dashboard démo** : `fiber-dashboard/app.py` · port 8050 · données simulées
- **Environnement** : `venv/` + `requirements.txt`
- **Lancement (Windows, Git Bash)** :
  ```bash
  source venv/Scripts/activate && python dashboard-reel/app.py
  ```
  → http://127.0.0.1:8052
- **Dépendances clés** : dash, plotly, pandas, numpy, scipy, openpyxl
- **Python 3.14.4** : pandas/numpy installés sans version épinglée (`pip install --prefer-binary pandas numpy`), pas de wheel pour les versions 2.2.2/1.26.4
- **Activation venv Windows** : `venv/Scripts/activate` (PAS `venv/bin/activate`)

## Structure du repo
```
fiber-dashboard/     dashboard démo multi-matériaux (données simulées, 4 onglets)
dashboard-reel/      dashboard principal soutenance — vraies données, port 8052
  app.py             code unique (~1130 lignes, 5 onglets)
  assets/style.css   design system CSS (Inter, zinc palette, badges, tabnum)
vrai-data/
  antoine-aymen/
    donnees_F1_recycle.csv    données Dragonfly scan réel (FICHIER PRINCIPAL)
    donnees_F1_genere.csv     structure générée numériquement F1 (2 µm/vox)
    donnees_F2_genere.csv     structure générée F2
    donnees_F3_genere.csv     structure générée F3
    donnees_F4_genere.csv     structure générée F4
    diametre.csv              épaisseurs ray-tracing (16,5M lignes, Thickness en mm)
    .thick_cache.npy          cache numpy 1/100 de diametre.csv (généré automatiquement)
    analyse_diametre.txt      stats pré-calculées sur l'épaisseur
    analyse_grandeurs_dossier.csv  paramètres JCAL (F1_originel + F1-F4_genere)
  nolhan/
    Resultats_Fibres.xlsx  résultats MATLAB (405 composantes)
articlesprof/        articles scientifiques fournis par l'encadrant
docs/                docs de présentation et fiches projet
docsmiparcours/      livrables mi-parcours
```

## Méthodes comparées

### Dragonfly ORS — Antoine & Aymen
Workflow : segmentation volumique → squelettisation → épaisseur locale par ray-tracing → export.
**Volume traité : volume TOTAL de l'échantillon.**

#### Fichier scan réel : `donnees_F1_recycle.csv` (ex-donnees2.csv)
- Séparateur `;`, encodage `utf-8-sig`
- Colonnes : `Time Step`, `Label Index`, `Name` (NA), `MIL`, `SVD`, `Voxel count`, `Volume (mm³)`, `Phi (°)`, `Theta (°)`
- PAS de colonne Surface Area
- 537 lignes brutes → **95 fibres** après filtre 101–100 000 voxels
- `Phi (°)` = inclinaison depuis la verticale → `angle_h = 90 - Phi`
- `Theta (°)` = azimut dans le plan horizontal
- Résolution : **5.50 µm/voxel** (calculé depuis volume minimum / voxels)

#### Fichiers générés numériquement : `donnees_F1-F4_genere.csv`
- Séparateur `;`, encodage `utf-8-sig`
- Colonnes : idem + `Surface Area (mm²)` (présente dans les générés, absente dans F1_recycle)
- Résolution : **2.00 µm/voxel** (résolution plus fine que le scan réel)
- F2 et F4 ont des stats presque identiques (129 fibres, 8.9°, 31 µm d.éq.) — observation, pas un bug connu
- Utilisation : comparaison acoustique JCAL (onglet 5), PAS comparaison MATLAB vs Dragonfly

#### Épaisseur ray-tracing : `diametre.csv`
- Séparateur `;`, colonne unique `Thickness (mm)` — 16 477 636 lignes
- Cache numpy `.thick_cache.npy` créé automatiquement (échantillon 1/100, filtre 5–350 µm)
- Stats : moyenne 122 µm, **médiane 113 µm**, écart-type 48 µm

#### Propriétés acoustiques : `analyse_grandeurs_dossier.csv`
- Colonnes (après rename) : `nom`, `porosite`, `tortuosite`, `sv`, `lambda_v`, `lambda_t`, `sigma`
- `lambda_v` et `lambda_t` en mm → convertis en µm pour l'affichage
- Données :
  | nom         | porosité | tortuosité | Sv (mm⁻¹) | Λ (µm) | Λ' (µm) | σ (N·s·m⁻⁴) |
  |-------------|----------|------------|-----------|--------|---------|-------------|
  | F1_originel | 93.42%   | 1.0329     | 4.069     | 114.8  | 229.6   | 12 148      |
  | F1_genere   | 95%      | 1.025      | 15.97     | 29.8   | 61.2    | 176 493     |
  | F2_genere   | 91.21%   | 1.0439     | 28.29     | 16.1   | 42.7    | 637 549     |
  | F3_genere   | 90.10%   | 1.0495     | 32.66     | 13.8   | 38.3    | 886 390     |
  | F4_genere   | 87.67%   | 1.0617     | 38.74     | 11.3   | 33.3    | 1 369 675   |

### MATLAB regionprops3 — Nolhan
Fonction native `regionprops3` (Image Processing Toolbox).
**Volume traité : SOUS-VOLUME de la même ROI (~10 µm/voxel).**

Fichier : `vrai-data/nolhan/Resultats_Fibres.xlsx`
- 405 composantes connexes, aucun filtre appliqué
- Colonnes clés :
  - `PrincipalAxisLength_1` → longueur proxy (voxels × 10 µm)
  - `PrincipalAxisLength_3` → diamètre proxy (PAL3 × 10 µm)
  - `Orientation_1/2` → angles d'Euler (Orientation_2 ≈ inclinaison horizontale)
  - `Volume`, `EquivDiameter`, `SurfaceArea`
  - `Centroid_1/2/3` → position spatiale (voxels × 10 µm)

### ⚠ Problème de comparaison volumes — ANALYSE COMPLÈTE

**Volumes connus :**
| | Dragonfly (Antoine) | MATLAB (Nolhan) |
|---|---|---|
| Volume traité | 122.96 mm³ (volume total) | 4.00 mm³ (sous-volume) |
| Dimensions | non connues en voxels | 200 × 200 × 100 voxels × (10 µm)³ |
| Voxels labellisés | 31 891 188 → 5.31 mm³ (4.3%) | — |
| Rapport | 100% | **3.25% du volume total** |
| Facteur d'échelle | — | ×30.7 pour extrapoler au total |

**Porosité estimée Dragonfly** : 1 − 5.31/122.96 ≈ **95.7%** (cohérent pour un matériau fibreux lâche)

**Densités de fibres calculées :**
- Dragonfly : 95 fibres / 122.96 mm³ = **0.77 fibres/mm³** (après filtre 101–100 000 voxels)
- MATLAB : 405 composantes / 4.00 mm³ = **101 composantes/mm³** (sans filtre)
- Facteur ×130 entre les deux → **NON comparable** : Dragonfly filtre les fragments et le bruit, MATLAB garde tout.

**Généralisation Nolhan (hypothèse homogénéité — supposition de l'équipe) :**
- Nolhan considère que toutes les variables moyennes (rayon, orientation, porosité) sont
  représentatives du volume total car le matériau est supposé homogène.
- Cette hypothèse est physiquement raisonnable pour un matériau fibreux, mais non vérifiée formellement.
- **À présenter comme hypothèse dans le dashboard, pas comme fait établi.**

**Porosité :**
- Mesurée par Antoine sur les fichiers Dragonfly : moyenne **~94.5%**, fourchette 0.88–0.95
- Estimée depuis les voxels labellisés : 1 − 5.31/122.96 = **95.7%** (cohérent, légèrement au-dessus)

**Conclusion pour le dashboard :**
→ **Ne jamais comparer les comptages absolus** (95 vs 405 — volumes différents ET filtres différents).
→ Les **distributions d'orientation et de diamètre (%)** sont comparables et valides (hypothèse homogénéité).
→ La porosité (~94–95%) est une valeur à afficher comme caractéristique commune.
→ Afficher le ratio de volumes (3.25%) comme contexte pour l'auditoire.
→ Toute généralisation doit être étiquetée "hypothèse" dans l'UI.

## Métriques calculées dans app.py (constantes au chargement)
```python
VOX_UM      = 5.50   # µm/voxel Dragonfly scan réel (F1_recycle)
THICK_MED   = 113    # µm — médiane épaisseur ray-tracing Dragonfly
NOL_D_MED   = 59     # µm — médiane PAL3 × 10 MATLAB
AA_ANG_MED  = 6.3    # ° — médiane inclinaison depuis l'horizontale Dragonfly
NOL_ANG_MED = 11.0   # ° — médiane inclinaison MATLAB (Orientation_2)
AA_EQ_MED   = 51     # µm — médiane diamètre équivalent sphère Dragonfly (∛(6V/π))
NOL_EQ_MED  = 83     # µm — médiane diamètre équivalent sphère MATLAB
ECART_PCT   = 38     # % d'écart entre AA_EQ_MED et NOL_EQ_MED
VOL_TOTAL   = 122.96 # mm³ — volume total Dragonfly
VOL_NOL_MM3 = 4.00   # mm³ — sous-volume MATLAB
VOL_RATIO_PC = 3.25  # % — VOL_NOL_MM3 / VOL_TOTAL
POROSITY    = 94.5   # % — porosité mesurée Dragonfly (plage 88–95%)
```

## Design system — dashboard-reel
Esthétique Vercel/Linear — **Inter font, palette zinc, JAMAIS de gradient AI-looking**.

```python
INDIGO  = '#6366F1'   # Dragonfly (toutes les traces, KPIs, dots)
EMERALD = '#10B981'   # MATLAB (toutes les traces, KPIs, dots)
BG      = '#FAFAFA'   # fond général
CARD    = '#FFFFFF'   # fond des cartes
ZN100   = '#F4F4F5'   # grille plotly
ZN200   = '#E4E4E7'   # bordures, séparateurs
ZN400   = '#A1A1AA'   # labels uppercase
ZN500   = '#71717A'   # texte secondaire
ZN700   = '#3F3F46'   # texte corps
ZN800   = '#27272A'   # titres section
ZN900   = '#18181B'   # body + tooltip background
AMBER   = '#D97706'   # avertissements
GREEN   = '#059669'   # succès / accord
RED     = '#E11D48'   # écart / désaccord

# Palette échantillons générés F1→F4 (onglet acoustique)
GEN_COLORS = ['#60A5FA', '#6366F1', '#7C3AED', '#A855F7']
GEN_LABELS = ['F1 — Généré', 'F2 — Généré', 'F3 — Généré', 'F4 — Généré']
GEN_KEYS   = ['F1_genere', 'F2_genere', 'F3_genere', 'F4_genere']
```

**Classes CSS clés (assets/style.css)** :
- `.tabnum` : `font-variant-numeric: tabular-nums` — tous les chiffres l'utilisent
- `.badge`, `.badge-ok`, `.badge-warn`, `.badge-diff`, `.badge-info` — pastilles colorées
- `.cmp-table` — tableau de comparaison sobre
- `.method-toggle` — radio bouton custom (segmented control)

**En-tête** : fond blanc `CARD`, pas de gradient, texte zinc-900, bordure bottom ZN200.

**Fonctions helper** :
- `lay(**kw)` : layout Plotly unifié (zinc bg, tooltip sombre, no modebar)
- `card(*children)` : carte blanche, borderRadius 12px, box-shadow subtil
- `kpi_dual(label, v_aa, v_nol, badge_text, badge_cls)` : KPI double avec diviseur vertical
- `kpi_single(label, value, sub, color)` : KPI simple (porosité, etc.)
- `chart_head(title, subtitle)` : en-tête de section graphique
- `grid(*children, cols, gap)` : CSS grid helper
- `G(fig)` : dcc.Graph sans modebar
- `item(text, warn)` : bullet point avec option couleur amber
- `insight(text, color, bg, border)` : bandeau de conclusion coloré

## Structure des onglets — dashboard-reel/app.py (5 onglets — TOUS OPÉRATIONNELS)

### Onglet 1 — Vue d'ensemble (`overview`)
- 3 KPI cards : Porosité · Inclinaison médiane (double) · Diamètre équivalent (double)
- Contexte volumique : barres proportionnelles Dragonfly (100%) vs MATLAB (3.25%)
- Cards objets : 95 fibres Dragonfly / 405 composantes MATLAB + avertissement volumes ≠
- Cards méthodes : description pipeline Dragonfly et MATLAB côte à côte
- Bar chart classification Dragonfly (Bruit / Fragment / Fibre / Gros objet / Matrice)

### Onglet 2 — Orientation (`orient`)
- Bandeau insight convergence orientation
- Diagramme rose polaire (`go.Barpolar`) : azimut Dragonfly (INDIGO) vs MATLAB (EMERALD), 18 bins
- Histogramme inclinaison avec toggle segmented control (Les deux / Dragonfly / MATLAB)
- Histogramme azimut superposé confirmation isotropie

### Onglet 3 — Morphologie (`morphologie`) — 10 graphiques
1. Diamètre direct (ray-tracing vs PAL₃) — barmode overlay, note métriques ≠
2. Diamètre équivalent ∛(6V/π) — même formule pour les deux
3. CDF diamètre équivalent — courbes + pointillés médianes
4. Distribution volumes en log₁₀ — même unité µm³
5. Box plot inclinaison — médiane + quartiles + outliers
6. Box plot diamètre équivalent
7. Scatter volume vs inclinaison (axe x log)
8. Histogramme longueur MATLAB (PAL₁ × 10 µm)
9. Rapport d'aspect MATLAB (PAL₁/PAL₃)
10. Carte spatiale fibres MATLAB (couleur = inclinaison, taille = longueur)

### Onglet 4 — Comparaison (`compare`)
- Bandeau insight résultat clé
- Tableau 10 lignes (métrique / Dragonfly / MATLAB / badge accord)
  - Volume analysé · Résolution · Porosité · Orientation générale · Inclinaison médiane
  - Isotropie azimutale · Diamètre mesure directe · Diamètre équivalent · Longueur · Rapport d'aspect
- 2 cards : "Ce que les données confirment" vs "Limites et précautions"

### Onglet 5 — Propriétés acoustiques (`acoustique`) — NOUVEAU
- Bandeau intro modèle JCAL
- Tableau récapitulatif JCAL (F1_originel + F1–F4 générés)
- 5 scatter plots (x = porosité %, y = paramètre JCAL) avec ligne de tendance :
  - Sv (mm⁻¹)
  - Tortuosité
  - Λ visqueuse (µm)
  - Λ' thermique (µm)
  - σ résistivité au flux (échelle log — varie sur 2 ordres de grandeur)
- Chaque scatter : F1–F4 génér. comme cercles colorés (GEN_COLORS) + F1_originel comme ★ grise
- Explication JCAL (Sv, Λ, σ) en prose

## État d'avancement — DASHBOARD COMPLET ✓
### Tout est fait
- `dashboard-reel/app.py` : 5 onglets opérationnels, ~1130 lignes
- Chargement : `donnees_F1_recycle.csv` + `Resultats_Fibres.xlsx` + cache épaisseur + `analyse_grandeurs_dossier.csv`
- Chargement générique `_load_dragonfly(filename)` — détecte automatiquement colonnes Volume/Phi/Theta/SurfaceArea
- Calcul automatique de toutes les métriques au démarrage
- `assets/style.css` : design system complet
- `requirements.txt` : scipy, openpyxl ajoutés

### Pistes d'amélioration optionnelles (post-soutenance)
- Filtrage spatial Dragonfly au sous-volume Nolhan (dimensions exactes inconnues)
- Vérifier que `fiber-dashboard/app.py` (port 8050) tourne encore sans erreur
- Clarifier pourquoi F2_genere et F4_genere ont des stats quasi-identiques (à vérifier avec Antoine)

## Conventions
- Langue : commentaires et noms de variables en français
- Code Python : PEP 8, fonctions en `snake_case`
- Avant de commit : lancer `python dashboard-reel/app.py` et vérifier les 5 onglets

## Points d'attention
- Garder la séparation claire MATLAB vs Dragonfly dans l'UI — jamais fusionnés
- Toujours utiliser INDIGO pour Dragonfly et EMERALD pour MATLAB, partout
- Ne PAS comparer les comptages absolus (volumes différents) — uniquement les distributions %
- Le fichier `donnee.csv` et `donnees2.csv` ont été supprimés — utiliser `donnees_F1_recycle.csv`
- Port actif : **8052**
- Les fichiers F1-F4_genere servent UNIQUEMENT à l'onglet acoustique, PAS à la comparaison MATLAB/Dragonfly
- Valeurs de référence thermique : PET ≈ 1,61 / Coton ≈ 1,31 / Verre ≈ 1,11 m²·K/W

## Ressources
@./README.md
@./docs/
@./articlesprof/
@./docsmiparcours/
