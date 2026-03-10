# FiberScope — Dashboard analytique · Microstructure fibreuse

Projet E4 DSIA · ESIEE Paris
Partenariat laboratoire **MSME UMR 8208 CNRS** — Université Gustave Eiffel

---

## Objectif

Ce dashboard relie quantitativement la **microstructure des fibres** (diamètre, longueur, orientation, porosité) aux **propriétés acoustiques et thermiques** des matériaux étudiés. Les données proviennent d'une segmentation 3D par tomographie à rayons X (µ-CT) sur 6 matériaux distincts.

Il permet d'explorer, comparer et valider les résultats produits par le pipeline de traitement de l'image.

---

## Contexte scientifique

La tomographie µ-CT produit un volume 3D d'intensités. L'algorithme de segmentation (Depriester et al., 2022) extrait individuellement chaque fibre et calcule :

- sa **géométrie** : diamètre (µm), longueur (µm), rapport d'élancement
- son **orientation** : angle zénithal θ ∈ [0°, 90°] et angle azimutal ψ ∈ [0°, 360°]
- ses **contacts** avec les fibres voisines

Ces descripteurs alimentent le modèle **Johnson-Champoux-Allard (JCA)** qui prédit les propriétés acoustiques et thermiques à partir de la microstructure.

---

## Stack technique

| Composant | Version |
|-----------|---------|
| Python | 3.11+ |
| Dash | 2.17.1 |
| Plotly | 5.22.0 |
| Pandas | 2.2.2 |
| NumPy | 1.26.4 |
| Gunicorn | 22.0.0 (prod) |
| Docker | optionnel |

---

## Structure du repo

```
fiber-dashboard/
├── app.py                        # Point d'entrée : routing + layout global
├── config.py                     # Couleurs, chemins, constantes globales
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
│
├── pages/                        # Une page par module
│   ├── home.py                   # Accueil (/)
│   ├── overview.py               # Vue d'ensemble (/overview)
│   ├── microstructure.py         # Morphologie fibres (/microstructure)
│   ├── properties.py             # Propriétés acoustiques + corrélations (/proprietes)
│   ├── acoustic_thermal.py       # Sous-page : courbes absorption, modèle JCA
│   ├── correlations.py           # Sous-page : scatter interactif, régression
│   ├── algorithm.py              # Algorithme + robustesse (/algorithme)
│   ├── parameters.py             # Sous-page : sensibilité paramètres
│   ├── robustness.py             # Sous-page : tests de robustesse
│   ├── quality.py                # Contrôle qualité image (/qualite)
│   └── samples.py                # Fiche échantillon (/echantillons)
│
├── components/                   # Composants réutilisables
│   ├── sidebar.py                # Barre de navigation latérale
│   ├── kpi_card.py               # Cartes KPI
│   ├── filters.py                # Dropdowns de filtre (matériau, lot, statut)
│   └── info_box.py               # Encadrés explicatifs (info, guide, warning)
│
├── utils/
│   ├── data_loader.py            # Chargement des CSV (avec cache LRU)
│   ├── figures.py                # Fonctions Plotly réutilisables
│   └── stats.py                  # Corrélations, régression, statistiques
│
├── data/                         # CSV (générés par scripts/ ou données réelles)
│   ├── samples.csv
│   ├── fibers.csv
│   ├── contacts.csv
│   ├── parameter_sweep.csv
│   ├── robustness.csv
│   ├── acoustic_thermal.csv
│   └── quality_log.csv
│
├── assets/
│   └── style.css                 # Thème visuel global
│
└── scripts/
    └── generate_mock_data.py     # Génération des données simulées
```

---

## Installation locale

```bash
git clone https://github.com/<votre-org>/Dashboard-Projet-E4.git
cd Dashboard-Projet-E4/fiber-dashboard

python -m venv venv
source venv/bin/activate       # Linux / Mac
# ou : venv\Scripts\activate   # Windows

pip install -r requirements.txt

# Générer les données simulées (une seule fois)
python scripts/generate_mock_data.py

# Lancer le serveur de développement
python app.py
```

Ouvrir **http://localhost:8050**

---

## Lancement Docker

```bash
cd fiber-dashboard

# Build + démarrage (les données mock sont générées automatiquement)
docker compose up --build

# Arrêt
docker compose down
```

Ouvrir **http://localhost:8050**

---

## Pages du dashboard

| URL | Page | Contenu |
|-----|------|---------|
| `/` | Accueil | Pipeline d'analyse, matériaux, statistiques globales |
| `/overview` | Vue d'ensemble | KPIs, graphiques par matériau, tableau des échantillons |
| `/microstructure` | Microstructure | Boxplots, KDE, figure de pôle stéréographique |
| `/proprietes` | Propriétés | Courbes d'absorption, paramètres JCA, corrélations |
| `/algorithme` | Algorithme | Sensibilité paramètres, robustesse bruit/résolution |
| `/qualite` | Qualité image | Journal des issues µ-CT, types et sévérités |
| `/echantillons` | Fiche échantillon | Détail par échantillon, histogrammes, table fibres |

> **Navigation** : la page **Propriétés** regroupe en onglets l'acoustique/thermique et les corrélations.
> La page **Algorithme** regroupe en onglets la sensibilité paramètres et la robustesse.

---

## Dictionnaire des colonnes CSV

### `samples.csv` — un enregistrement par échantillon

| Colonne | Type | Description |
|---------|------|-------------|
| `sample_id` | str | Identifiant unique (ex : S001) |
| `material` | str | Matériau : Nylon, Carbone, Verre, Cuivre, PET recyclé, Chanvre |
| `batch` | str | Lot de fabrication : LOT-A, LOT-B, LOT-C |
| `resolution_um` | float | Résolution de scan (µm/voxel) |
| `voxel_size` | float | Taille effective d'un voxel (µm) |
| `volume_mm3` | float | Volume analysé (mm³) |
| `porosity` | float | Fraction volumique de vide (0–1) |
| `fiber_count` | int | Nombre de fibres segmentées |
| `contact_count` | int | Nombre de contacts fibre-fibre |
| `contact_density` | float | Contacts par mm³ |
| `mean_diameter_um` | float | Diamètre moyen des fibres (µm) |
| `mean_length_um` | float | Longueur moyenne des fibres (µm) |
| `mean_curvature` | float | Courbure moyenne (µm⁻¹) |
| `orientation_dispersion` | float | Dispersion angulaire (°) |
| `misorientation_threshold` | float | Seuil de misorientation utilisé (°) |
| `n_directions` | int | Nombre de directions d'analyse |
| `dilation_type` | str | Type de dilatation : longitudinal ou isotropic |
| `slenderness_ratio` | float | Rapport longueur/diamètre |
| `quality_score` | int | Score qualité image (1–5) |
| `status` | str | completed / in_progress / failed |

### `fibers.csv` — un enregistrement par fibre

| Colonne | Description |
|---------|-------------|
| `fiber_id` | Identifiant unique |
| `sample_id` | Échantillon parent |
| `diameter_um` | Diamètre (µm) |
| `length_um` | Longueur (µm) |
| `orientation_theta` | Angle zénithal θ ∈ [0°, 90°] (θ = 0° : fibre perpendiculaire au plan d'imagerie) |
| `orientation_psi` | Angle azimutal ψ ∈ [0°, 360°] |
| `curvature` | Courbure locale (µm⁻¹) |
| `n_contacts` | Nombre de contacts avec d'autres fibres |

### `acoustic_thermal.csv` — propriétés par échantillon

| Colonne | Description |
|---------|-------------|
| `airflow_resistivity` | Résistivité à l'écoulement σ (Pa·s/m²) |
| `thermal_permeability` | Perméabilité thermique k₀' (m²) — ordre 10⁻¹³ à 10⁻¹⁰ m² |
| `viscous_length_um` | Longueur caractéristique visqueuse Λ (µm) |
| `thermal_length_um` | Longueur caractéristique thermique Λ' (µm) |
| `absorption_Xhz` | Coefficient α à X Hz, X ∈ {250, 500, 1000, 2000, 4000} |
| `predicted_*` | Valeurs prédites par le modèle JCA |

> `thermal_permeability` est de l'ordre de 10⁻¹² m² — ne pas arrondir à moins de 6 chiffres significatifs.

---

## Intégrer les vraies données du groupe

1. Remplacer les CSV dans `data/` en respectant les colonnes requises listées ci-dessus.
2. Les colonnes absentes sont tolérées : le dashboard affiche un message plutôt qu'une erreur.
3. Pour les images µ-CT, dans `pages/samples.py`, remplacer les blocs `.image-placeholder` par :

```python
html.Img(src=f"/assets/images/{sample_id}_raw.png", style={"width": "100%"})
```

Placer les images dans `assets/images/`.

---

## Limites du jeu de données mock

- Les données sont **entièrement simulées** à partir de distributions statistiques réalistes.
- La graine aléatoire est fixée (`SEED=42`) pour garantir la reproductibilité.
- Les corrélations sont simulées avec du bruit intentionnel pour rester crédibles, mais ne reflètent pas de vraies mesures expérimentales.
- Seuls les échantillons au statut `completed` ont des données acoustiques/thermiques (comportement intentionnel).

---

## Référence algorithmique

> Depriester et al. (2022) — *Individual fiber separation in 3D fibrous material images using misorientation angle as a criterion*, **Journal of Materials Science**.

---

## Maintenance

- Régénérer les données mock : `python scripts/generate_mock_data.py`
- Ajouter une page : créer `pages/ma_page.py` avec `def layout()`, l'importer dans `app.py`, ajouter la route dans `ROUTES`.
- Modifier les couleurs ou chemins : tout est centralisé dans `config.py`.
