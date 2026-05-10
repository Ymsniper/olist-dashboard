"""
ETL Pipeline — Olist E-Commerce → Star Schema
Projet Entrepôt de données · GLSI 2026
"""

import pandas as pd
import sqlite3
import os

DATA_DIR = "olist_data"   # folder where you put the Kaggle CSVs
DB_PATH  = "olist_dw.db"  # output SQLite database

# ─────────────────────────────────────────────
# 1. EXTRACT — load raw CSVs
# ─────────────────────────────────────────────
print("📥 Loading raw data …")

orders    = pd.read_csv(f"{DATA_DIR}/olist_orders_dataset.csv")
items     = pd.read_csv(f"{DATA_DIR}/olist_order_items_dataset.csv")
customers = pd.read_csv(f"{DATA_DIR}/olist_customers_dataset.csv")
products  = pd.read_csv(f"{DATA_DIR}/olist_products_dataset.csv")
sellers   = pd.read_csv(f"{DATA_DIR}/olist_sellers_dataset.csv")
reviews   = pd.read_csv(f"{DATA_DIR}/olist_order_reviews_dataset.csv")
cat_trans = pd.read_csv(f"{DATA_DIR}/product_category_name_translation.csv")
payments  = pd.read_csv(f"{DATA_DIR}/olist_order_payments_dataset.csv")

print(f"  Orders: {len(orders):,} rows")
print(f"  Items:  {len(items):,} rows")

# ─────────────────────────────────────────────
# 2. TRANSFORM — clean & reshape
# ─────────────────────────────────────────────
print("\n🔧 Transforming …")

# --- Parse dates ---
date_cols = ["order_purchase_timestamp", "order_delivered_customer_date",
             "order_estimated_delivery_date"]
for col in date_cols:
    orders[col] = pd.to_datetime(orders[col], errors="coerce")

# Keep only delivered orders
orders = orders[orders["order_status"] == "delivered"].copy()
orders.dropna(subset=["order_purchase_timestamp"], inplace=True)

# --- Translate product categories ---
products = products.merge(cat_trans, on="product_category_name", how="left")
products["product_category_name_english"] = (
    products["product_category_name_english"]
    .fillna(products["product_category_name"])
    .fillna("unknown")
)

# --- DIM_TEMPS ---
print("  Building DIM_TEMPS …")
all_dates = orders["order_purchase_timestamp"].dt.date.unique()
dim_temps = pd.DataFrame({"date_achat": pd.to_datetime(all_dates)})
dim_temps["temps_id"]   = range(1, len(dim_temps) + 1)
dim_temps["jour"]       = dim_temps["date_achat"].dt.day
dim_temps["mois"]       = dim_temps["date_achat"].dt.month
dim_temps["trimestre"]  = dim_temps["date_achat"].dt.quarter
dim_temps["annee"]      = dim_temps["date_achat"].dt.year
dim_temps["nom_mois"]   = dim_temps["date_achat"].dt.strftime("%B")
dim_temps["date_str"]   = dim_temps["date_achat"].dt.strftime("%Y-%m-%d")

# --- DIM_CLIENT ---
print("  Building DIM_CLIENT …")
dim_client = customers[["customer_id", "customer_city",
                         "customer_state"]].copy()
dim_client.columns = ["client_id", "ville", "etat"]
# Map state to region (Brazil)
region_map = {
    "SP":"Sudeste","RJ":"Sudeste","MG":"Sudeste","ES":"Sudeste",
    "RS":"Sul","SC":"Sul","PR":"Sul",
    "BA":"Nordeste","PE":"Nordeste","CE":"Nordeste","MA":"Nordeste",
    "PB":"Nordeste","RN":"Nordeste","AL":"Nordeste","SE":"Nordeste","PI":"Nordeste",
    "GO":"Centro-Oeste","MT":"Centro-Oeste","MS":"Centro-Oeste","DF":"Centro-Oeste",
    "AM":"Norte","PA":"Norte","RO":"Norte","AC":"Norte","AP":"Norte","RR":"Norte","TO":"Norte"
}
dim_client["region"] = dim_client["etat"].map(region_map).fillna("Outro")
dim_client.drop_duplicates(subset="client_id", inplace=True)

# --- DIM_PRODUIT ---
print("  Building DIM_PRODUIT …")
dim_produit = products[["product_id", "product_category_name_english",
                         "product_weight_g"]].copy()
dim_produit.columns = ["produit_id", "categorie", "poids_g"]
dim_produit.drop_duplicates(subset="produit_id", inplace=True)

# --- DIM_VENDEUR ---
print("  Building DIM_VENDEUR …")
dim_vendeur = sellers[["seller_id", "seller_city", "seller_state"]].copy()
dim_vendeur.columns = ["vendeur_id", "ville", "etat"]
dim_vendeur.drop_duplicates(subset="vendeur_id", inplace=True)

# ─────────────────────────────────────────────
# FACT TABLE — FAIT_VENTES
# ─────────────────────────────────────────────
print("  Building FAIT_VENTES …")

# Join items → orders → reviews → payments
avg_review = (reviews.groupby("order_id")["review_score"]
              .mean().reset_index()
              .rename(columns={"review_score": "score_moyen"}))

total_payment = (payments.groupby("order_id")["payment_value"]
                 .sum().reset_index()
                 .rename(columns={"payment_value": "montant_total"}))

fact = (items
        .merge(orders[["order_id","customer_id",
                        "order_purchase_timestamp",
                        "order_delivered_customer_date",
                        "order_estimated_delivery_date"]], on="order_id")
        .merge(avg_review, on="order_id", how="left")
        .merge(total_payment, on="order_id", how="left"))

# Delivery delay (days)
fact["delai_livraison"] = (
    (fact["order_delivered_customer_date"] -
     fact["order_purchase_timestamp"]).dt.total_seconds() / 86400
).round(1)

# Map to dim keys
date_map = dim_temps.set_index("date_str")["temps_id"].to_dict()
fact["date_str"] = fact["order_purchase_timestamp"].dt.strftime("%Y-%m-%d")
fact["temps_id"] = fact["date_str"].map(date_map)

fact_final = fact[[
    "order_id", "order_item_id", "customer_id", "product_id",
    "seller_id", "temps_id", "price", "freight_value",
    "montant_total", "score_moyen", "delai_livraison"
]].copy()
fact_final.columns = [
    "commande_id", "item_id", "client_id", "produit_id",
    "vendeur_id", "temps_id", "prix_unitaire", "frais_livraison",
    "montant_total", "score_satisfaction", "delai_livraison_jours"
]

print(f"  Fact rows: {len(fact_final):,}")

# ─────────────────────────────────────────────
# 3. LOAD — write to SQLite
# ─────────────────────────────────────────────
print(f"\n💾 Loading into {DB_PATH} …")

if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)

dim_temps.to_sql("DIM_TEMPS",    conn, index=False, if_exists="replace")
dim_client.to_sql("DIM_CLIENT",  conn, index=False, if_exists="replace")
dim_produit.to_sql("DIM_PRODUIT",conn, index=False, if_exists="replace")
dim_vendeur.to_sql("DIM_VENDEUR",conn, index=False, if_exists="replace")
fact_final.to_sql("FAIT_VENTES", conn, index=False, if_exists="replace")

conn.close()

print("✅ ETL complete!")
print(f"   Database: {DB_PATH}")
print(f"   Tables: DIM_TEMPS, DIM_CLIENT, DIM_PRODUIT, DIM_VENDEUR, FAIT_VENTES")
