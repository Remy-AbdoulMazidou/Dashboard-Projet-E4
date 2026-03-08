# Dashboard Analytique — Microstructure Fibreuse

Projet de recherche en partenariat avec le laboratoire **MSME (UMR 8208 CNRS)** — Université Gustave Eiffel.
ESIEE Paris · Filière E4 DSIA.

---

## Lancement rapide

```bash
docker-compose up --build
```

Ouvrir [http://localhost:8050](http://localhost:8050).

Les données mock sont générées automatiquement au build si les CSV n'existent pas.

---

## Développement local

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Générer les données mock (une seule fois)
python scripts/generate_mock_data.py

# Lancer le serveur de développement
python app.py
```

---

## Structure

```
fiber-dashboard/
├── app.py                   # Point d'entrée, routing
├── config.py                # Constantes, couleurs, chemins
├── data/                    # CSV (générés par scripts/)
├── pages/                   # 8 pages du dashboard
├── components/              # Composants réutilisables (sidebar, KPI, filtres)
├── utils/                   # Chargement données, statistiques, figures
├── assets/style.css         # Dark theme custom
└── scripts/generate_mock_data.py
```

## Pages

| # | URL | Contenu |
|---|-----|---------|
| 1 | `/` | Vue d'ensemble — KPIs, tableau, timeline |
| 2 | `/samples` | Fiche par échantillon, histogrammes |
| 3 | `/microstructure` | Diamètres, longueurs, orientations, contacts |
| 4 | `/parameters` | Sensibilité aux paramètres algorithmiques |
| 5 | `/robustness` | Sous-échantillonnage et bruit |
| 6 | `/correlations` | Matrice de corrélation, scatter interactif |
| 7 | `/acoustic-thermal` | Absorption acoustique, perméabilité thermique |
| 8 | `/quality` | Contrôle qualité, issues par type et sévérité |

---

## Intégration d'images réelles

Dans `pages/samples.py`, remplacer les blocs `.image-placeholder` par des composants `html.Img` pointant vers les images réelles dans `assets/images/`.

---

## Référence algorithmique

Depriester et al. (2022) — *Individual fiber separation in 3D fibrous material images using misorientation angle as a criterion*, Journal of Materials Science.
