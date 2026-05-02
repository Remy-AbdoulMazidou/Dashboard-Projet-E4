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
- **Lancement (Windows PowerShell)** :
  ```powershell
  . venv\Scripts\Activate.ps1; python dashboard-reel\app.py
  ```
  → http://127.0.0.1:8052
- **Dépendances clés** : dash, plotly, pandas, numpy, scipy, openpyxl
- **Python 3.14.4** : pandas/numpy installés sans version épinglée (`pip install --prefer-binary pandas numpy`), pas de wheel pour les versions 2.2.2/1.26.4
- **Activation venv Windows** : `venv/Scripts/activate` (PAS `venv/bin/activate`)
- **Git config local** : `user.email = remy.abdoul@gmail.com` · `user.name = Remy-AbdoulMazidou`
- **GitHub remote** : https://github.com/Remy-AbdoulMazidou/Dashboard-Projet-E4

## Structure du repo
```
fiber-dashboard/     dashboard démo multi-matériaux (données simulées, 4 onglets)
  app.py + components.py + config.py + data.py + tab_*.py
  assets/style.css · data/*.csv
dashboard-reel/      dashboard principal soutenance — vraies données, port 8052
  app.py             code unique (~1500 lignes, 5 onglets)
  assets/style.css   design system CSS (Inter, zinc palette, shadcn/ui style)
vrai-data/
  antoine-aymen/
    donnees_F1_recycle.csv    données Dragonfly scan réel F1 (FICHIER PRINCIPAL)
    donnees_F1_genere.csv     structure générée numériquement F1 (2 µm/vox)
    donnees_F2_genere.csv     structure générée F2
    donnees_F3_genere.csv     structure générée F3
    donnees_F4_genere.csv     structure générée F4
    diametre.csv              épaisseurs ray-tracing (16,5M lignes, Thickness en mm)
    .thick_cache.npy          cache numpy 1/100 de diametre.csv (généré automatiquement)
    analyse_diametre.txt      stats pré-calculées sur l'épaisseur
    analyse_grandeurs_dossier.csv  paramètres JCAL (F1_originel + F1-F4_genere)
  nolhan/
    Resultats_Fibres.xlsx       résultats MATLAB (405 composantes)
    correspondance-variable.pdf documentation des variables MATLAB (commité depuis 202d878)
documentationprojet/            dossier unique de documentation (renommé depuis docs/)
  Article_1_IJSS_preprint.pdf                           article IJSS (ex-articlesprof/)
  Depriester_rolland_orgeas_geindreau_levrard_bremond 2022 (J. Microscopy).pdf  (ex-articlesprof/)
  projetE4_rapport_Intermediaire_ECL.pdf                rapport intermédiaire mis à jour
```

**Supprimés lors du nettoyage (2026-05-02) :**
- `articlesprof/` → contenu déplacé dans `documentationprojet/` (renommés sans "(1)")
- `docs/` (discours_oral_remy.docx, documentation_projet.pdf, rapport_dashboard_remy.docx, slides_presentation.pptx) → documents personnels, supprimés
- `docsmiparcours/` (rapport_Intermediaire.pdf remplacé par ECL version, séance 5 docx supprimé)
- `generate_doc.py`, `generate_rapport.py`, `generate_slides.py` → scripts utilitaires supprimés

---

## Méthodes comparées

### Dragonfly ORS — Antoine & Aymen
Workflow : segmentation volumique → squelettisation → épaisseur locale par ray-tracing → export.

#### Fichier scan réel : `donnees_F1_recycle.csv`
- Anciennement `donnees2.csv` (fichier supprimé, données identiques)
- Séparateur `;`, encodage `utf-8-sig`
- Colonnes : `Time Step`, `Label Index`, `Name (NA)`, `MIL`, `SVD`, `Voxel count`, `Volume (mm³)`, `Phi (°)`, `Theta (°)`
- **PAS de colonne Surface Area** (contrairement aux fichiers _genere)
- 537 lignes brutes (Label Index 1 → 537)
- `Phi (°)` = inclinaison depuis la **verticale** → `angle_h = 90 - Phi` = inclinaison depuis l'horizontale
- `Theta (°)` = azimut dans le plan horizontal
- Résolution : **5.50 µm/voxel** (calculé : volume d'un voxel unique = 1.664×10⁻⁷ mm³ → ∛ = 5.50 µm)

#### Structure interne de donnees_F1_recycle.csv — détail important
L'analyse du fichier révèle une structure à deux niveaux :

| Catégorie | Condition (voxels) | Nb objets | Rôle |
|---|---|---|---|
| Bruit | 1–5 | ~440 | Artefacts 1–5 voxels, Phi=90° |
| Fragment | 6–100 | quelques | Petits fragments |
| **Fibre** | **101–100 000** | **95** | **Fibres utilisées dans le dashboard** |
| Gros objet | 100 001–1 000 000 | quelques | Agrégats |
| **Matrice** | **> 1 000 000** | **1** | **Label 537 = réseau fibreux global** |

**L'objet "Matrice" (Label 537)** est fondamental à comprendre :
- 31 029 776 voxels → **5.16 mm³** → représente ~97% de toute la matière labellisée
- Phi ≈ 90° (structure quasi-verticale / isotrope en volume)
- C'est le composant connexe principal du réseau fibreux (toutes les fibres connectées entre elles)
- Total matière labellisée tous objets confondus : **5.31 mm³** (= 5.16 + 0.15 autres)

#### ✓ CONFIRMÉ PAR ANTOINE — Volume global
**Le volume de 122.96 mm³ est bien le volume total du scan complet** (confirmé par Antoine).
Dragonfly a donc analysé l'intégralité de l'échantillon physique scanné, pas une ROI.

- Volume total scan : **122.96 mm³**
- Matière labellisée : **5.31 mm³** (= 31 891 188 voxels × (5.5 µm)³)
- Porosité : 1 − 5.31/122.96 ≈ **95.7%** (cohérent avec la mesure Dragonfly ~94.5%)

Le fichier CSV ne contient pas les dimensions du volume en voxels, mais le volume total est confirmé via Antoine.

#### Fichiers générés numériquement : `donnees_F1-F4_genere.csv`
- Séparateur `;`, encodage `utf-8-sig`
- Colonnes : idem + `Surface Area (mm²)` (présente dans les générés, absente dans F1_recycle)
- Résolution : **2.00 µm/voxel** (résolution plus fine que le scan réel)
- F2 et F4 ont des stats quasi-identiques (129 fibres, ~8.9°, ~31 µm d.éq.) — observation notée, cause inconnue
- **Usage exclusif : onglet 5 acoustique**. Ces fichiers ne servent PAS à la comparaison MATLAB/Dragonfly.

#### Épaisseur ray-tracing : `diametre.csv`
- Séparateur `;`, colonne unique `Thickness (mm)` — 16 477 636 lignes
- Cache numpy `.thick_cache.npy` créé automatiquement au premier lancement (échantillon 1/100, filtre 5–350 µm)
- Stats : moyenne 122 µm, **médiane 113 µm**, écart-type 48 µm

#### Propriétés acoustiques : `analyse_grandeurs_dossier.csv`
- Colonnes brutes : `Dossier;Porosité(phi);Tortuosité;Surf.Spec.λ(mm-1);Long.visc.Λ(mm);Long.therm.Λ'(mm);Résistivité flux σ(N.s.m-4)`
- Renommées dans app.py : `nom`, `porosite`, `tortuosite`, `sv`, `lambda_v`, `lambda_t`, `sigma`
- `lambda_v` et `lambda_t` en mm dans le fichier → convertis en µm (`×1000`) pour l'affichage
- Données :
  | nom         | porosité | tortuosité | Sv (mm⁻¹) | Λ (µm) | Λ' (µm) | σ (N·s·m⁻⁴) |
  |-------------|----------|------------|-----------|--------|---------|-------------|
  | F1_originel | 93.42%   | 1.0329     | 4.069     | 114.8  | 229.6   | 12 148      |
  | F1_genere   | 95%      | 1.025      | 15.97     | 29.8   | 61.2    | 176 493     |
  | F2_genere   | 91.21%   | 1.0439     | 28.29     | 16.1   | 42.7    | 637 549     |
  | F3_genere   | 90.10%   | 1.0495     | 32.66     | 13.8   | 38.3    | 886 390     |
  | F4_genere   | 87.67%   | 1.0617     | 38.74     | 11.3   | 33.3    | 1 369 675   |

---

### MATLAB regionprops3 — Nolhan
Fonction native `regionprops3` (Image Processing Toolbox).
**Volume traité : SOUS-VOLUME délimité par Nolhan.**

Fichier : `vrai-data/nolhan/Resultats_Fibres.xlsx`
- 405 composantes connexes, **aucun filtre appliqué** (fragments et bruit inclus)
- Résolution : ~10 µm/voxel
- Volume analysé : 200 × 200 × 100 voxels × (10 µm)³ = **4.00 mm³**
- Colonnes clés :
  - `PrincipalAxisLength_1` → longueur proxy (voxels × 10 µm)
  - `PrincipalAxisLength_3` → diamètre proxy (PAL3 × 10 µm)
  - `Orientation_1` → azimut (utilisé ×2 pour l'histogramme azimut)
  - `Orientation_2` → inclinaison horizontale (utilisé directement comme `angle_h`)
  - `Volume` (en voxels × (10 µm)³ → mm³ × 1000 pour µm³)
  - `EquivDiameter`, `SurfaceArea`
  - `Centroid_1/2/3` → position spatiale (voxels × 10 µm)

---

### ⚠ Problème de comparaison volumes — ANALYSE COMPLÈTE

**Ce qu'on sait avec certitude :**
| | Dragonfly (Antoine) | MATLAB (Nolhan) |
|---|---|---|
| Matière labellisée | **5.31 mm³** (lu dans le CSV) | non mesuré directement |
| Volume analysé | **122.96 mm³ — volume total du scan** (confirmé par Antoine) | **4.00 mm³ — sous-volume** (200×200×100 vox × (10 µm)³) |
| Résolution | 5.5 µm/vox | ~10 µm/vox |
| Filtre appliqué | oui : 101–100 000 voxels → 95 fibres | non : 405 composantes |

**Situation claire :**
- Dragonfly = analyse du **scan complet** (122.96 mm³)
- MATLAB = analyse d'un **sous-volume délimité** (4.00 mm³ = 3.25% du total)

**Porosité :**
- Estimée depuis les voxels : 1 − 5.31/122.96 ≈ **95.7%** (si 122.96 mm³ est le volume total analysé)
- Mesurée par Antoine via Dragonfly : **~94.5%**, fourchette 0.88–0.95 (source WhatsApp équipe)
- Les deux valeurs sont cohérentes entre elles → vraisemblable

**Densités de fibres (non comparables) :**
- Dragonfly : 95 fibres / 122.96 mm³ = **0.77 fibres/mm³**
- MATLAB : 405 composantes / 4.00 mm³ = **101 composantes/mm³**
- Facteur ×130 → incomparable : volumes ≠ ET filtres ≠

**Hypothèse homogénéité (supposition de l'équipe) :**
- Nolhan suppose que les distributions moyennes du sous-volume (4 mm³) sont représentatives
  du volume total — physiquement raisonnable pour un matériau fibreux, non vérifiée formellement.
- **Toujours présenter comme hypothèse dans le dashboard, jamais comme fait établi.**

**Règles d'or pour le dashboard :**
→ **Jamais comparer les comptages absolus** (95 vs 405).
→ Les **distributions normalisées (%)** d'orientation et de diamètre sont comparables sous l'hypothèse d'homogénéité.
→ La porosité (~94–95%) est la seule valeur affichable comme caractéristique commune.
→ Afficher 3.25% = 4/122.96 comme contexte volumique (à nuancer selon réponse d'Antoine).
→ Tout chiffre issu de généralisation du sous-volume MATLAB → étiquette "hypothèse".

---

## Métriques calculées dans app.py (constantes au chargement)
```python
VOX_UM      = 5.50   # µm/voxel Dragonfly scan réel (F1_recycle) — calculé : ∛(1.664e-7 mm³) × 1000
THICK_MED   = 113    # µm — médiane épaisseur ray-tracing Dragonfly (cache .npy)
NOL_D_MED   = 59     # µm — médiane PAL3 × 10 MATLAB
AA_ANG_MED  = 6.3    # ° — médiane inclinaison depuis l'horizontale Dragonfly (= 90 - Phi)
NOL_ANG_MED = 11.0   # ° — médiane inclinaison MATLAB (Orientation_2 en valeur absolue)
AA_EQ_MED   = 51     # µm — médiane diamètre équivalent Dragonfly [∛(6V/π), V en mm³ × 1e9]
NOL_EQ_MED  = 83     # µm — médiane diamètre équivalent MATLAB [∛(6V/π), V en mm³ × 1000]
ECART_PCT   = 38     # % d'écart entre AA_EQ_MED et NOL_EQ_MED
NOL_LEN_MED = ?      # µm — médiane longueur MATLAB (calculé au runtime)
NOL_AR_MED  = ?      # — médiane rapport d'aspect MATLAB (calculé au runtime)
VOL_TOTAL   = 122.96 # mm³ — volume analysé Dragonfly (déclaré par Antoine — voir ⚠ ci-dessus)
VOL_NOL_MM3 = 4.00   # mm³ — sous-volume MATLAB
VOL_RATIO_PC = 3.25  # % — VOL_NOL_MM3 / VOL_TOTAL
POROSITY    = 94.5   # % — porosité mesurée Dragonfly (source Antoine, plage 88–95%)
```

**Formule diamètre équivalent — identique pour les deux méthodes :**
```python
aa_eq  = (6 * FIB['vol'] * 1e9 / np.pi) ** (1/3)   # vol en mm³ → µm³ × 1e9
nol_eq = (6 * DF_NOL['Volume'] * 1000 / np.pi) ** (1/3)  # Volume MATLAB × 1000 → µm³
```

**Filtre fibres Dragonfly :**
```python
bins   = [0, 5, 100, 100_000, 1_000_000, float('inf')]
labels = ['Bruit', 'Fragment', 'Fibre', 'Gros objet', 'Matrice']
FIB    = DF_AA[DF_AA['cat'] == 'Fibre']   # 95 fibres
```

---

## Design system — dashboard-reel
Esthétique Vercel/Linear — **Inter font, palette zinc, JAMAIS de gradient AI-looking**.

```python
INDIGO  = '#6366F1'   # Dragonfly (toutes les traces, KPIs, dots)
EMERALD = '#10B981'   # MATLAB (toutes les traces, KPIs, dots)
BG      = '#FAFAFA'   # fond général
CARD    = '#FFFFFF'   # fond des cartes
ZN100   = '#F4F4F5'   # grille plotly
ZN200   = '#E4E4E7'   # bordures, séparateurs
ZN400   = '#A1A1AA'   # labels uppercase, éléments discrets
ZN500   = '#71717A'   # texte secondaire
ZN700   = '#3F3F46'   # texte corps
ZN800   = '#27272A'   # titres section
ZN900   = '#18181B'   # body + tooltip background
AMBER   = '#D97706'   # avertissements (warn=True dans item())
GREEN   = '#059669'   # succès / accord (badge-ok, insight par défaut)
RED     = '#E11D48'   # écart / désaccord

# Palette échantillons générés F1→F4 (onglet acoustique uniquement)
GEN_COLORS = ['#60A5FA', '#6366F1', '#7C3AED', '#A855F7']
GEN_LABELS = ['F1 — Généré', 'F2 — Généré', 'F3 — Généré', 'F4 — Généré']
GEN_KEYS   = ['F1_genere', 'F2_genere', 'F3_genere', 'F4_genere']
```

**Classes CSS clés (assets/style.css)** :
- `.tabnum` : `font-variant-numeric: tabular-nums` — tous les chiffres
- `.badge`, `.badge-ok`, `.badge-warn`, `.badge-diff`, `.badge-info` — pastilles colorées
- `.cmp-table` — tableau de comparaison sobre
- `.method-toggle` — radio bouton custom (segmented control)

**En-tête** : fond blanc `CARD`, pas de gradient, texte zinc-900, bordure bottom ZN200.

**Fonctions helper importantes** :
- `lay(**kw)` : layout Plotly unifié (zinc bg, tooltip sombre ZN900, no modebar)
- `card(*children, p, mb)` : carte blanche, borderRadius 12px, box-shadow subtil
- `kpi_dual(label, v_aa, v_nol, badge_text, badge_cls)` : KPI double INDIGO|EMERALD avec diviseur
- `kpi_single(label, value, sub, color)` : KPI simple (porosité, etc.)
- `chart_head(title, subtitle)` : en-tête de section graphique
- `grid(*children, cols, gap, mb)` : CSS grid helper
- `G(fig)` : dcc.Graph sans modebar
- `item(text, warn)` : bullet point · avec option couleur AMBER si warn=True
- `insight(text, color, bg, border)` : bandeau de conclusion coloré (vert par défaut)

---

## Structure des onglets — dashboard-reel/app.py (5 onglets — TOUS OPÉRATIONNELS)

### Onglet 1 — Vue d'ensemble (`overview`)
- 3 KPI cards en grid 3 colonnes :
  - Porosité 94.5% (kpi_single)
  - Inclinaison médiane : 6.3° Dragonfly / 11.0° MATLAB (kpi_dual, badge-ok)
  - Diamètre équivalent : 51 µm Dragonfly / 83 µm MATLAB (kpi_dual, badge-warn 38% écart)
- Contexte volumique : barre INDIGO 100% + barre EMERALD 3.25% + note hypothèse homogénéité
- Cards objets : 95 fibres (filtre 101-100k vox) vs 405 composantes (sans filtre) + ⚠ avertissement
- Cards méthodes : description Dragonfly et MATLAB côte à côte
- Bar chart classification Dragonfly : Bruit / Fragment / Fibre (INDIGO) / Gros objet / Matrice

### Onglet 2 — Orientation (`orient`)
- Bandeau insight vert : convergence quasi-horizontale + isotropie azimutale
- Grid 2 colonnes :
  - Rose polaire `go.Barpolar` 18 bins · INDIGO Dragonfly + EMERALD MATLAB · direction clockwise
  - Histogramme inclinaison avec `dcc.RadioItems` id=`method-toggle` (Les deux / Dragonfly / MATLAB)
    → callback `update_elevation` sur Input `method-toggle`
- Histogramme azimut superposé (INDIGO + EMERALD) confirmation isotropie

### Onglet 3 — Morphologie (`morphologie`) — 10 graphiques
1. Diamètre direct : THICK (ray-tracing, méd. 113 µm) vs Diam_um (PAL₃×10, méd. 59 µm) — ⚠ métriques ≠
2. Diamètre équivalent ∛(6V/π) : aa_eq vs nol_eq — comparaison la plus équitable, écart 38%
3. CDF diamètre équivalent : courbes cumulées + lignes pointillées aux médianes
4. Volume log₁₀ : même unité µm³ pour les deux
5. Box plot inclinaison : `go.Box` INDIGO vs EMERALD
6. Box plot diamètre équivalent
7. Scatter volume (log) vs inclinaison : chaque point = une fibre
8. Longueur MATLAB (PAL₁ × 10 µm, EMERALD) — Dragonfly n'a pas de longueur exportée
9. Rapport d'aspect MATLAB (PAL₁/PAL₃, clipé à 12)
10. Carte spatiale MATLAB (Centroid_1/2 × 10 µm · couleur = inclinaison vert→rouge · taille = longueur)

### Onglet 4 — Comparaison (`compare`)
- Bandeau insight rouge-texte : résultat clé convergence orientation + explication écart diamètre
- Tableau 10 lignes (`cmp-table`, alternance bg ZN100/CARD) :
  - Volume analysé (badge-warn) · Résolution (badge-info) · Porosité (badge-info)
  - Orientation générale (badge-ok) · Inclinaison médiane (badge-ok)
  - Isotropie azimutale (badge-ok) · Diamètre mesure directe (badge-diff)
  - Diamètre équivalent (badge-warn) · Longueur (badge-info) · Rapport d'aspect (badge-info)
- Grid 2 colonnes : "Ce que les données confirment" (GREEN) vs "Limites et précautions" (AMBER)

### Onglet 5 — Propriétés acoustiques (`acoustique`)
- Bandeau intro gris (insight ZN800/ZN100/ZN200)
- Tableau JCAL : F1_originel (fond ZN100, gras) + F1–F4 générés (fond blanc)
- Grid 2 colonnes × 2 lignes → 4 scatter plots :
  - Sv vs porosité · Tortuosité vs porosité
  - Λ visqueuse (µm) vs porosité · Λ' thermique (µm) vs porosité
- Scatter σ seul (pleine largeur) avec `y_log=True` (varie sur 2 ordres de grandeur)
- Chaque scatter : cercles GEN_COLORS pour F1–F4, ★ ZN400 pour F1_originel, ligne de tendance pointillée ZN400
- Card "Modèle JCAL — Paramètres clés" : explication Sv, Λ, σ en prose

---

## État d'avancement — DASHBOARD COMPLET ✓

### Tout est opérationnel
- `dashboard-reel/app.py` : 5 onglets, ~1500 lignes, démarrage propre
- Sortie au démarrage : `OK · 95 fibres Dragonfly · 405 composantes MATLAB · 4 échantillons générés`
- `assets/style.css` : design system complet (style shadcn/ui, hover-card, badges)
- `requirements.txt` : scipy + openpyxl présents
- Dernier commit design : `7ddf51b` — refonte visuelle shadcn/ui

### Questions en attente de réponse (avant soutenance)
1. ~~122.96 mm³ = scan total ou ROI Dragonfly ?~~ → **✓ CONFIRMÉ : volume total du scan**
2. Clarifier pourquoi F2_genere et F4_genere ont des stats quasi-identiques (à vérifier avec Antoine)

### Pistes d'amélioration optionnelles (post-soutenance)
- Filtrage spatial Dragonfly au sous-volume Nolhan (nécessite les dimensions exactes de la ROI MATLAB)
- Vérifier que `fiber-dashboard/app.py` (port 8050) tourne encore sans erreur

---

## Conventions
- Langue : commentaires et noms de variables en français
- Code Python : PEP 8, fonctions en `snake_case`
- Avant de commit : lancer `python dashboard-reel/app.py`, vérifier les 5 onglets manuellement

## Points d'attention — règles absolues
- **INDIGO = Dragonfly, EMERALD = MATLAB** — partout, sans exception
- **Jamais fusionner** les deux méthodes dans le même graphique sans légende claire
- **Jamais comparer les comptages absolus** (95 vs 405) — uniquement les distributions (%)
- `donnees2.csv` supprimé → uniquement `donnees_F1_recycle.csv`
- Les fichiers `donnees_F1-F4_genere.csv` → **onglet acoustique uniquement**
- Port actif : **8052** (changé depuis 8051 pour forcer rechargement navigateur, ne pas rechanger)
- Valeurs de référence thermique (pour contexte) : PET ≈ 1.61 / Coton ≈ 1.31 / Verre ≈ 1.11 m²·K/W

## Ressources
@./README.md
@./documentationprojet/
