# 🛒 Olist E-Commerce Dashboard
**Projet Entrepôt de données · GLSI 2026 · Houcine ESSID**

[![CI — Lint & Deploy](https://github.com/Ymsniper/olist-dashboard/actions/workflows/deploy.yml/badge.svg?branch=main)](https://github.com/Ymsniper/olist-dashboard/actions)
[![Live Demo](https://img.shields.io/badge/Live%20Demo-Render-46E3B7?logo=render)](https://olist-dashboard.onrender.com)

---

## Présentation

Dashboard interactif KPIs sur le dataset Olist (e-commerce brésilien), couvrant :
- Pipeline ETL (Python/pandas)
- Modèle dimensionnel en étoile (Star Schema)
- Requêtes KPI (SQL)
- Dashboard interactif (Plotly Dash)
- Fouille de données : segmentation K-Means, classification Decision Tree, prévision régression linéaire

## Structure des fichiers

```
olist-dashboard/
├── .github/workflows/
│   └── deploy.yml              ← CI/CD : lint + deploy automatique sur Render
├── olist_data/                 ← Données brutes CSV (non versionnées)
├── dashboard.py                ← Dashboard Plotly Dash
├── etl_pipeline.py             ← ETL pipeline
├── data_mining.py              ← K-Means, Decision Tree, Régression
├── star_schema_sql.sql         ← DDL schéma en étoile
├── kpi_queries.sql             ← Requêtes KPI
├── requirements.txt            ← Dépendances Python
├── Procfile                    ← Commande démarrage Render/Heroku
├── render.yaml                 ← Config Render
└── README.md
```

---

## 🚀 Déploiement — Guide complet

### Étape 1 — Pousser sur GitHub

```bash
# 1. Créer un dépôt sur https://github.com/new  (nom : olist-dashboard)

# 2. Dans le dossier du projet :
git init
git add .
git commit -m "Initial commit — Olist dashboard"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/olist-dashboard.git
git push -u origin main
```

> Le dossier `olist_data/` est dans `.gitignore` (CSV trop volumineux).
> Le fichier `olist_dw.db` (28 MB) **est versionné** — base pré-construite requise par le dashboard.

---

### Étape 2 — Héberger sur Render (lien public gratuit)

1. Aller sur **https://render.com** → créer un compte (gratuit).
2. **New → Web Service** → connecter GitHub → sélectionner `olist-dashboard`.
3. Remplir les champs :

   | Champ | Valeur |
   |---|---|
   | **Runtime** | `Python 3` |
   | **Build Command** | `pip install -r requirements.txt` |
   | **Start Command** | `gunicorn dashboard:server` |
   | **Instance Type** | `Free` |

4. **Create Web Service** → Render construit et déploie.
5. Lien public : `https://olist-dashboard.onrender.com` ✅

---

### Étape 3 — Déploiement automatique via GitHub Actions

Le workflow `.github/workflows/deploy.yml` redéploie sur Render à chaque `git push main`.

**Pour l'activer :**

1. Render → votre service → **Settings → Deploy Hook** → copier l'URL.
2. GitHub → votre dépôt → **Settings → Secrets and variables → Actions → New secret** :
   - **Name** : `RENDER_DEPLOY_HOOK_URL`
   - **Value** : l'URL Render copiée.

Désormais, chaque push sur `main` exécute automatiquement :
- ✅ Lint Python (flake8)
- ✅ Vérification des dépendances
- ✅ Redéploiement Render

---

## 💻 Exécution locale

```bash
pip install -r requirements.txt

# Générer la base (si olist_dw.db absent)
# Télécharger olist_data/ depuis Kaggle d'abord :
# https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
python etl_pipeline.py

# Lancer le dashboard
python dashboard.py        # → http://127.0.0.1:8050

# Fouille de données (optionnel)
python data_mining.py
```

---

## Schéma en étoile

```
           DIM_TEMPS
               |
DIM_VENDEUR ——FAIT_VENTES—— DIM_CLIENT
               |
           DIM_PRODUIT
```

## KPIs principaux

| KPI | Description |
|-----|-------------|
| CA mensuel | Chiffre d'affaires par région et mois |
| CA par catégorie | Revenus par catégorie de produit |
| Score satisfaction | Moyenne et distribution des avis (1-5) |
| Délai de livraison | Délai moyen par état brésilien |
| Évolution trimestrielle | Tendance du CA pour prévisions |

## Fouille de données

| Méthode | Objectif |
|---------|----------|
| K-Means (K=4) | Segmentation clients |
| Decision Tree (depth=5) | Prédiction score commande ≥ 4 |
| Régression linéaire | Prévision CA T1/T2 2019 |

---

Source : [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) — Kaggle
