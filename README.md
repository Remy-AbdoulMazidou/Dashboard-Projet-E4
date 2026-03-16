# FiberScope — Dashboard Microstructure Fibreuse

Projet E4 ESIEE Paris — Partenariat MSME UMR 8208 CNRS  
Analyse de matériaux fibreux par microtomographie X.

## Lancer le dashboard

```bash
source venv/bin/activate
python fiber-dashboard/app.py
```

Ouvrir http://127.0.0.1:8050

## Installer les dépendances

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Structure du projet

```
fiber-dashboard/   code du dashboard (Python/Dash)
articles/          articles scientifiques de référence
docs/              fiches et documents de présentation
```

## Données

Les fichiers CSV dans `fiber-dashboard/data/` sont des données simulées.  
Remplacer par les vrais CSV fournis par le groupe pour afficher les vraies mesures.
