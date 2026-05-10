"""
Fouille de données — Olist E-Commerce
Projet Entrepôt de données · GLSI 2026

- K-Means : segmentation clients (fréquence achat & montant moyen)
- Decision Tree : classification commandes bien notées (score ≥ 4)
- Prévision : Linear Regression sur CA trimestriel

Install: pip install scikit-learn pandas matplotlib seaborn sqlite3
"""

import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier, plot_tree
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay
from sklearn.linear_model import LinearRegression

DB = "olist_dw.db"

def query(sql):
    conn = sqlite3.connect(DB)
    df = pd.read_sql_query(sql, conn)
    conn.close()
    return df

print("=" * 60)
print("   FOUILLE DE DONNÉES — Olist DW · GLSI 2026")
print("=" * 60)

# ══════════════════════════════════════════════════════════════
# PARTIE 1 — K-MEANS : Segmentation clients
# ══════════════════════════════════════════════════════════════
print("\n🔵 PARTIE 1 : K-Means — Segmentation clients")

df_clients = query("""
    SELECT
        f.client_id,
        COUNT(DISTINCT f.commande_id)               AS freq_achat,
        ROUND(AVG(f.prix_unitaire), 2)              AS montant_moyen,
        ROUND(SUM(f.prix_unitaire + f.frais_livraison), 2) AS ca_total,
        ROUND(AVG(f.score_satisfaction), 2)         AS score_moyen,
        ROUND(AVG(f.delai_livraison_jours), 1)      AS delai_moyen
    FROM FAIT_VENTES f
    GROUP BY f.client_id
    HAVING freq_achat >= 1
""")

print(f"   Clients chargés : {len(df_clients):,}")

features = ["freq_achat", "montant_moyen", "ca_total"]
X = df_clients[features].fillna(0)

# Standardize
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Elbow method
inertias = []
K_range = range(2, 9)
for k in K_range:
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    km.fit(X_scaled)
    inertias.append(km.inertia_)

# Fit with K=4
K = 4
km = KMeans(n_clusters=K, random_state=42, n_init=10)
df_clients["segment"] = km.fit_predict(X_scaled)

# Label segments
seg_summary = df_clients.groupby("segment")[features].mean()
seg_summary["ca_total_rank"] = seg_summary["ca_total"].rank()
labels = {
    seg_summary["ca_total_rank"].idxmin():      "Segment 1 — Petits acheteurs",
    seg_summary["ca_total_rank"].sort_values().index[1]: "Segment 2 — Occasionnels",
    seg_summary["ca_total_rank"].sort_values().index[2]: "Segment 3 — Réguliers",
    seg_summary["ca_total_rank"].idxmax():      "Segment 4 — Grands comptes",
}
df_clients["segment_label"] = df_clients["segment"].map(labels)

print("\n   Résumé des segments :")
print(df_clients.groupby("segment_label")[features].mean().round(2).to_string())

# ══════════════════════════════════════════════════════════════
# PARTIE 2 — DECISION TREE : Classification commandes
# ══════════════════════════════════════════════════════════════
print("\n🟡 PARTIE 2 : Decision Tree — Commandes bien notées (score ≥ 4)")

df_orders = query("""
    SELECT
        f.score_satisfaction,
        f.prix_unitaire,
        f.frais_livraison,
        f.delai_livraison_jours,
        p.categorie,
        c.region
    FROM FAIT_VENTES f
    JOIN DIM_PRODUIT p ON f.produit_id = p.produit_id
    JOIN DIM_CLIENT  c ON f.client_id  = c.client_id
    WHERE f.score_satisfaction IS NOT NULL
      AND f.delai_livraison_jours > 0
""")

df_orders["bonne_note"] = (df_orders["score_satisfaction"] >= 4).astype(int)

# Encode categoricals
df_model = pd.get_dummies(df_orders[["prix_unitaire", "frais_livraison",
                                     "delai_livraison_jours", "categorie", "region"]],
                          drop_first=True)
y = df_orders["bonne_note"]

X_train, X_test, y_train, y_test = train_test_split(
    df_model, y, test_size=0.25, random_state=42, stratify=y)

dt = DecisionTreeClassifier(max_depth=5, random_state=42, class_weight="balanced")
dt.fit(X_train, y_train)
y_pred = dt.predict(X_test)

print(f"\n   Précision globale : {(y_pred == y_test).mean():.1%}")
print("\n   Rapport de classification :")
print(classification_report(y_test, y_pred,
                             target_names=["Mauvaise note (< 4)", "Bonne note (≥ 4)"]))

# Feature importance
feat_imp = pd.Series(dt.feature_importances_,
                     index=df_model.columns).sort_values(ascending=False).head(10)
print("\n   Top 10 variables importantes :")
print(feat_imp.round(4).to_string())

# ══════════════════════════════════════════════════════════════
# PARTIE 3 — PRÉVISION : CA trimestriel (Linear Regression)
# ══════════════════════════════════════════════════════════════
print("\n🟢 PARTIE 3 : Prévision CA trimestriel (Régression linéaire)")

df_trend = query("""
    SELECT t.annee, t.trimestre,
           ROUND(SUM(f.prix_unitaire + f.frais_livraison), 2) AS ca_total
    FROM FAIT_VENTES f
    JOIN DIM_TEMPS t ON f.temps_id = t.temps_id
    GROUP BY t.annee, t.trimestre
    ORDER BY t.annee, t.trimestre
""")

df_trend["t"] = range(len(df_trend))
X_t = df_trend[["t"]]
y_t = df_trend["ca_total"]

lr = LinearRegression()
lr.fit(X_t, y_t)

# Predict 2 future quarters
future_t = pd.DataFrame({"t": [len(df_trend), len(df_trend)+1]})
future_pred = lr.predict(future_t)
df_trend["ca_prevu"] = lr.predict(X_t)

print(f"\n   Prévision T1 2019 : R$ {future_pred[0]:,.0f}")
print(f"   Prévision T2 2019 : R$ {future_pred[1]:,.0f}")
print(f"   R² du modèle      : {lr.score(X_t, y_t):.3f}")

# ══════════════════════════════════════════════════════════════
# VISUALISATIONS — export figures
# ══════════════════════════════════════════════════════════════
print("\n📊 Génération des figures …")

plt.style.use("dark_background")
colors = ["#a78bfa", "#34d399", "#fbbf24", "#f87171", "#60a5fa"]

fig = plt.figure(figsize=(18, 14))
fig.patch.set_facecolor("#0f0f1a")
gs = gridspec.GridSpec(3, 3, figure=fig, hspace=0.45, wspace=0.35)

# 1. Elbow curve
ax1 = fig.add_subplot(gs[0, 0])
ax1.plot(list(K_range), inertias, marker="o", color="#a78bfa", linewidth=2)
ax1.axvline(x=K, color="#f87171", linestyle="--", alpha=0.7, label=f"K={K} choisi")
ax1.set_title("Méthode du coude (K-Means)", color="white")
ax1.set_xlabel("Nombre de clusters K"); ax1.set_ylabel("Inertie")
ax1.legend(); ax1.set_facecolor("#1e1e2e")

# 2. Scatter clients (freq vs montant)
ax2 = fig.add_subplot(gs[0, 1:])
scatter_colors = [colors[s % len(colors)] for s in df_clients["segment"]]
sample = df_clients.sample(min(3000, len(df_clients)), random_state=42)
for seg in range(K):
    sub = sample[sample["segment"] == seg]
    ax2.scatter(sub["freq_achat"], sub["montant_moyen"],
                alpha=0.5, s=15, label=labels.get(seg, f"Seg {seg}"),
                color=colors[seg % len(colors)])
ax2.set_title("Segmentation clients — K-Means", color="white")
ax2.set_xlabel("Fréquence d'achat"); ax2.set_ylabel("Montant moyen (BRL)")
ax2.legend(fontsize=8); ax2.set_facecolor("#1e1e2e")
ax2.set_xlim(0, 6); ax2.set_ylim(0, 1000)

# 3. Segment bar chart
ax3 = fig.add_subplot(gs[1, 0])
seg_counts = df_clients["segment_label"].value_counts()
ax3.barh(seg_counts.index, seg_counts.values, color=colors[:len(seg_counts)])
ax3.set_title("Taille des segments", color="white")
ax3.set_xlabel("Nb clients"); ax3.set_facecolor("#1e1e2e")
ax3.tick_params(axis="y", labelsize=7)

# 4. Confusion matrix
ax4 = fig.add_subplot(gs[1, 1])
cm = confusion_matrix(y_test, y_pred)
disp = ConfusionMatrixDisplay(cm, display_labels=["Mauvaise", "Bonne"])
disp.plot(ax=ax4, colorbar=False, cmap="Purples")
ax4.set_title("Matrice de confusion — Decision Tree", color="white")
ax4.set_facecolor("#1e1e2e")

# 5. Feature importance
ax5 = fig.add_subplot(gs[1, 2])
feat_imp.sort_values().plot.barh(ax=ax5, color="#34d399")
ax5.set_title("Importance des variables", color="white")
ax5.set_facecolor("#1e1e2e")
ax5.tick_params(labelsize=7)

# 6. Trend + forecast
ax6 = fig.add_subplot(gs[2, :])
quarters = df_trend["annee"].astype(str) + "-T" + df_trend["trimestre"].astype(str)
ax6.bar(quarters, df_trend["ca_total"], color="#60a5fa", alpha=0.7, label="CA réel")
ax6.plot(quarters, df_trend["ca_prevu"], color="#fbbf24", linewidth=2,
         linestyle="--", marker="o", label="Régression linéaire")
future_labels = ["2019-T1", "2019-T2"]
ax6.bar(future_labels, future_pred, color="#f87171", alpha=0.8, label="Prévision")
ax6.set_title("Évolution trimestrielle du CA + Prévisions 2019", color="white")
ax6.set_xlabel("Trimestre"); ax6.set_ylabel("CA (BRL)")
ax6.legend(); ax6.set_facecolor("#1e1e2e")
plt.xticks(rotation=45, ha="right")

fig.suptitle("Fouille de données — Olist Brazilian E-Commerce · GLSI 2026",
             fontsize=14, color="#a78bfa", y=0.98)

plt.savefig("data_mining_results.png", dpi=150, bbox_inches="tight",
            facecolor="#0f0f1a")
print("   ✅ Figure sauvegardée : data_mining_results.png")
plt.show()

print("\n✅ Fouille de données terminée !")
