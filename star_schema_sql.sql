-- ══════════════════════════════════════════════════════════════
-- Projet Entrepôt de données · GLSI 2026
-- Schéma en étoile (Star Schema) — Olist Brazilian E-Commerce
-- DDL : CREATE TABLE avec clés primaires et étrangères
-- ══════════════════════════════════════════════════════════════

-- ──────────────────────────────────────────────────────────────
-- DIMENSION : DIM_TEMPS
-- ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS DIM_TEMPS (
    temps_id    INTEGER  PRIMARY KEY,
    date_achat  DATE     NOT NULL,
    date_str    TEXT     NOT NULL,
    jour        INTEGER  NOT NULL CHECK (jour BETWEEN 1 AND 31),
    mois        INTEGER  NOT NULL CHECK (mois BETWEEN 1 AND 12),
    nom_mois    TEXT     NOT NULL,
    trimestre   INTEGER  NOT NULL CHECK (trimestre BETWEEN 1 AND 4),
    annee       INTEGER  NOT NULL
);

-- ──────────────────────────────────────────────────────────────
-- DIMENSION : DIM_CLIENT
-- ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS DIM_CLIENT (
    client_id   TEXT  PRIMARY KEY,
    ville       TEXT,
    etat        TEXT  NOT NULL,
    region      TEXT  NOT NULL
);

-- ──────────────────────────────────────────────────────────────
-- DIMENSION : DIM_PRODUIT
-- ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS DIM_PRODUIT (
    produit_id  TEXT  PRIMARY KEY,
    categorie   TEXT  NOT NULL DEFAULT 'unknown',
    poids_g     REAL
);

-- ──────────────────────────────────────────────────────────────
-- DIMENSION : DIM_VENDEUR
-- ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS DIM_VENDEUR (
    vendeur_id  TEXT  PRIMARY KEY,
    ville       TEXT,
    etat        TEXT
);

-- ──────────────────────────────────────────────────────────────
-- TABLE DE FAITS : FAIT_VENTES
-- ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS FAIT_VENTES (
    commande_id          TEXT    NOT NULL,
    item_id              INTEGER NOT NULL,
    client_id            TEXT    NOT NULL,
    produit_id           TEXT    NOT NULL,
    vendeur_id           TEXT    NOT NULL,
    temps_id             INTEGER NOT NULL,

    -- Mesures
    prix_unitaire        REAL    NOT NULL DEFAULT 0.0,
    frais_livraison      REAL    NOT NULL DEFAULT 0.0,
    montant_total        REAL,
    score_satisfaction   REAL    CHECK (score_satisfaction BETWEEN 1 AND 5),
    delai_livraison_jours REAL,

    -- Clé primaire composite
    PRIMARY KEY (commande_id, item_id),

    -- Clés étrangères vers les dimensions
    FOREIGN KEY (client_id)  REFERENCES DIM_CLIENT  (client_id),
    FOREIGN KEY (produit_id) REFERENCES DIM_PRODUIT (produit_id),
    FOREIGN KEY (vendeur_id) REFERENCES DIM_VENDEUR (vendeur_id),
    FOREIGN KEY (temps_id)   REFERENCES DIM_TEMPS   (temps_id)
);

-- ──────────────────────────────────────────────────────────────
-- INDEX pour accélérer les jointures et les agrégations
-- ──────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_fait_client    ON FAIT_VENTES (client_id);
CREATE INDEX IF NOT EXISTS idx_fait_produit   ON FAIT_VENTES (produit_id);
CREATE INDEX IF NOT EXISTS idx_fait_vendeur   ON FAIT_VENTES (vendeur_id);
CREATE INDEX IF NOT EXISTS idx_fait_temps     ON FAIT_VENTES (temps_id);
CREATE INDEX IF NOT EXISTS idx_temps_annee    ON DIM_TEMPS   (annee, mois);
CREATE INDEX IF NOT EXISTS idx_client_region  ON DIM_CLIENT  (region);
CREATE INDEX IF NOT EXISTS idx_produit_cat    ON DIM_PRODUIT (categorie);

-- ══════════════════════════════════════════════════════════════
-- VÉRIFICATION : compter les enregistrements dans chaque table
-- ══════════════════════════════════════════════════════════════
-- SELECT 'DIM_TEMPS'    AS table_name, COUNT(*) AS nb FROM DIM_TEMPS
-- UNION ALL
-- SELECT 'DIM_CLIENT',   COUNT(*) FROM DIM_CLIENT
-- UNION ALL
-- SELECT 'DIM_PRODUIT',  COUNT(*) FROM DIM_PRODUIT
-- UNION ALL
-- SELECT 'DIM_VENDEUR',  COUNT(*) FROM DIM_VENDEUR
-- UNION ALL
-- SELECT 'FAIT_VENTES',  COUNT(*) FROM FAIT_VENTES;
