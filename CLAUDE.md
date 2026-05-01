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
  app.py             code unique (pas de modules séparés)
  assets/style.css   design system CSS (Inter, zinc palette, badges, tabnum)
vrai-data/
  antoine-aymen/
    donnees2.csv     données Dragonfly (ACTIF — remplace l'ancien donnee.csv supprimé)
    diametre.csv     épaisseurs ray-tracing (16,5M lignes, Thickness en mm)
    .thick_cache.npy cache numpy 1/100 de diametre.csv (généré automatiquement)
    analyse_diametre.txt  stats pré-calculées sur l'épaisseur
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

Fichier actif : `vrai-data/antoine-aymen/donnees2.csv`
- Séparateur `;`, encodage `utf-8-sig`
- Colonnes : `Time Step`, `Label Index`, `Name` (NA), `MIL`, `SVD`, `Voxel count`, `Volume (mm³)`, `Phi (°)`, `Theta (°)`
- 537 lignes brutes → **95 fibres** après filtre 101–100 000 voxels
- `Phi (°)` = inclinaison depuis la verticale → `angle_h = 90 - Phi` = inclinaison depuis l'horizontale
- `Theta (°)` = azimut dans le plan horizontal

Épaisseur : `vrai-data/antoine-aymen/diametre.csv`
- Séparateur `;`, colonne unique `Thickness (mm)` — 16 477 636 lignes
- Cache numpy `.thick_cache.npy` créé automatiquement (échantillon 1/100, filtre 5–350 µm)
- Stats : moyenne 122 µm, **médiane 113 µm**, écart-type 48 µm

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
VOX_UM      = 5.50   # µm/voxel Dragonfly (calculé depuis Volume[0]^(1/3))
THICK_MED   = 113    # µm — médiane épaisseur ray-tracing Dragonfly
NOL_D_MED   = 59     # µm — médiane PAL3 × 10 MATLAB
AA_ANG_MED  = 6.3    # ° — médiane inclinaison depuis l'horizontale Dragonfly
NOL_ANG_MED = 11.0   # ° — médiane inclinaison MATLAB (Orientation_2)
AA_EQ_MED   = 51     # µm — médiane diamètre équivalent sphère Dragonfly (∛(6V/π))
NOL_EQ_MED  = 83     # µm — médiane diamètre équivalent sphère MATLAB
ECART_PCT   = 38     # % d'écart entre AA_EQ_MED et NOL_EQ_MED
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
- `kpi(label, v_aa, v_nol, badge_text, badge_cls)` : KPI double avec diviseur vertical
- `chart_head(title, subtitle)` : en-tête de section graphique
- `grid(*children, cols, gap)` : CSS grid helper
- `G(fig)` : dcc.Graph sans modebar

## Structure des onglets — dashboard-reel/app.py
1. **Vue d'ensemble** : 4 KPI cards (fibres, inclinaison médiane, diamètre direct, diamètre équivalent) + cards méthodes + bar chart classification Dragonfly
2. **Orientation** : histogrammes azimut et inclinaison avec toggle Dragonfly / MATLAB / Superposé
3. **Comparaison** : tableau récapitulatif côte à côte avec badges convergence/écart
4. **Morphologie** : distributions des diamètres (épaisseur Dragonfly vs PAL3 MATLAB)

## État d'avancement
### Fait
- `dashboard-reel/app.py` : refonte complète design (blanc, indigo/emerald, zinc, tabnum)
- Chargement des vraies données : `donnees2.csv` + `Resultats_Fibres.xlsx` + cache épaisseur
- Calcul automatique de toutes les métriques de comparaison au démarrage
- Onglets Vue d'ensemble et Orientation opérationnels
- `assets/style.css` : design system complet
- `requirements.txt` : scipy ajouté, openpyxl ajouté

### À faire (priorité soutenance)
- Obtenir les **dimensions du sous-volume Nolhan** pour filtrer spatialement Dragonfly
- Onglet **Morphologie** : overlay distribution diamètres Dragonfly vs MATLAB
- Onglet **Comparaison** : tableau récapitulatif complet avec toutes les métriques
- Vérifier que `fiber-dashboard/app.py` (port 8050) tourne encore sans erreur

## Conventions
- Langue : commentaires et noms de variables en français
- Code Python : PEP 8, fonctions en `snake_case`
- Avant de commit : lancer `python dashboard-reel/app.py` et vérifier les 4 onglets

## Points d'attention
- Garder la séparation claire MATLAB vs Dragonfly dans l'UI — jamais fusionnés
- Toujours utiliser INDIGO pour Dragonfly et EMERALD pour MATLAB, partout
- Ne PAS comparer les comptages absolus (volumes différents) — uniquement les distributions %
- Le fichier `donnee.csv` a été supprimé — utiliser uniquement `donnees2.csv`
- Port actif : **8052** (changé depuis 8051 pour forcer le rechargement navigateur)
- Valeurs de référence thermique : PET ≈ 1,61 / Coton ≈ 1,31 / Verre ≈ 1,11 m²·K/W

## Ressources
@./README.md
@./docs/
@./articlesprof/
@./docsmiparcours/
