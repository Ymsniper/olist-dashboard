-- ══════════════════════════════════════════════════════
-- Projet Entrepôt de données · GLSI 2026
-- SQL KPI Queries — Olist Brazilian E-Commerce
-- ══════════════════════════════════════════════════════


-- ──────────────────────────────────────────────────────
-- KPI 1 : Chiffre d'affaires mensuel par région
-- ──────────────────────────────────────────────────────
SELECT
    t.annee,
    t.mois,
    t.nom_mois,
    c.region,
    ROUND(SUM(f.prix_unitaire + f.frais_livraison), 2)  AS ca_total,
    COUNT(DISTINCT f.commande_id)                        AS nb_commandes,
    ROUND(AVG(f.prix_unitaire), 2)                       AS panier_moyen
FROM FAIT_VENTES f
JOIN DIM_TEMPS   t ON f.temps_id  = t.temps_id
JOIN DIM_CLIENT  c ON f.client_id = c.client_id
GROUP BY t.annee, t.mois, t.nom_mois, c.region
ORDER BY t.annee, t.mois, ca_total DESC;


-- ──────────────────────────────────────────────────────
-- KPI 2 : CA mensuel par catégorie de produit
-- ──────────────────────────────────────────────────────
SELECT
    t.annee,
    t.mois,
    p.categorie,
    ROUND(SUM(f.prix_unitaire), 2)   AS ca_categorie,
    COUNT(*)                          AS nb_articles_vendus
FROM FAIT_VENTES f
JOIN DIM_TEMPS   t ON f.temps_id   = t.temps_id
JOIN DIM_PRODUIT p ON f.produit_id = p.produit_id
GROUP BY t.annee, t.mois, p.categorie
ORDER BY t.annee, t.mois, ca_categorie DESC;


-- ──────────────────────────────────────────────────────
-- KPI 3 : Score de satisfaction moyen par vendeur
-- ──────────────────────────────────────────────────────
SELECT
    v.vendeur_id,
    v.etat,
    ROUND(AVG(f.score_satisfaction), 2) AS score_moyen,
    COUNT(DISTINCT f.commande_id)        AS nb_commandes,
    ROUND(SUM(f.prix_unitaire), 2)       AS ca_total
FROM FAIT_VENTES f
JOIN DIM_VENDEUR v ON f.vendeur_id = v.vendeur_id
WHERE f.score_satisfaction IS NOT NULL
GROUP BY v.vendeur_id, v.etat
ORDER BY score_moyen DESC
LIMIT 20;


-- ──────────────────────────────────────────────────────
-- KPI 4 : Délai moyen de livraison par état
-- ──────────────────────────────────────────────────────
SELECT
    c.etat,
    c.region,
    ROUND(AVG(f.delai_livraison_jours), 1) AS delai_moyen_jours,
    ROUND(MIN(f.delai_livraison_jours), 1) AS delai_min,
    ROUND(MAX(f.delai_livraison_jours), 1) AS delai_max,
    COUNT(DISTINCT f.commande_id)           AS nb_commandes
FROM FAIT_VENTES f
JOIN DIM_CLIENT c ON f.client_id = c.client_id
WHERE f.delai_livraison_jours > 0
GROUP BY c.etat, c.region
ORDER BY delai_moyen_jours DESC;


-- ──────────────────────────────────────────────────────
-- KPI 5 : Top 10 catégories par satisfaction
-- ──────────────────────────────────────────────────────
SELECT
    p.categorie,
    ROUND(AVG(f.score_satisfaction), 2) AS score_moyen,
    COUNT(*)                             AS nb_evaluations
FROM FAIT_VENTES f
JOIN DIM_PRODUIT p ON f.produit_id = p.produit_id
WHERE f.score_satisfaction IS NOT NULL
GROUP BY p.categorie
HAVING nb_evaluations > 50
ORDER BY score_moyen DESC
LIMIT 10;


-- ──────────────────────────────────────────────────────
-- KPI 6 : Évolution trimestrielle du CA (pour prévision)
-- ──────────────────────────────────────────────────────
SELECT
    t.annee,
    t.trimestre,
    t.annee || '-T' || t.trimestre AS periode,
    ROUND(SUM(f.prix_unitaire + f.frais_livraison), 2) AS ca_total,
    COUNT(DISTINCT f.commande_id)                       AS nb_commandes
FROM FAIT_VENTES f
JOIN DIM_TEMPS t ON f.temps_id = t.temps_id
GROUP BY t.annee, t.trimestre
ORDER BY t.annee, t.trimestre;
