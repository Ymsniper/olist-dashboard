"""
Dashboard KPIs interactif — Olist E-Commerce
Projet Entrepôt de données · GLSI 2026

Install: pip install dash plotly pandas sqlite3
Run:     python dashboard.py
Open:    http://127.0.0.1:8050
"""

import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output

DB = "olist_dw.db"

# ── Helper ──────────────────────────────────────────────
def query(sql):
    conn = sqlite3.connect(DB)
    df = pd.read_sql_query(sql, conn)
    conn.close()
    return df

# ── Pre-load data ───────────────────────────────────────
df_ca = query("""
    SELECT t.annee, t.mois, t.nom_mois, c.region,
           ROUND(SUM(f.prix_unitaire + f.frais_livraison), 2) AS ca_total,
           COUNT(DISTINCT f.commande_id) AS nb_commandes,
           ROUND(AVG(f.prix_unitaire), 2) AS panier_moyen
    FROM FAIT_VENTES f
    JOIN DIM_TEMPS  t ON f.temps_id  = t.temps_id
    JOIN DIM_CLIENT c ON f.client_id = c.client_id
    GROUP BY t.annee, t.mois, t.nom_mois, c.region
    ORDER BY t.annee, t.mois
""")
df_ca["periode"] = df_ca["annee"].astype(str) + "-" + df_ca["mois"].astype(str).str.zfill(2)

df_cat = query("""
    SELECT p.categorie,
           ROUND(SUM(f.prix_unitaire), 2) AS ca_categorie,
           ROUND(AVG(f.score_satisfaction), 2) AS score_moyen,
           COUNT(*) AS nb_ventes
    FROM FAIT_VENTES f
    JOIN DIM_PRODUIT p ON f.produit_id = p.produit_id
    GROUP BY p.categorie
    ORDER BY ca_categorie DESC
    LIMIT 15
""")

df_delai = query("""
    SELECT c.etat, c.region,
           ROUND(AVG(f.delai_livraison_jours), 1) AS delai_moyen,
           COUNT(DISTINCT f.commande_id) AS nb_commandes
    FROM FAIT_VENTES f
    JOIN DIM_CLIENT c ON f.client_id = c.client_id
    WHERE f.delai_livraison_jours > 0
    GROUP BY c.etat, c.region
    ORDER BY delai_moyen DESC
""")

df_score = query("""
    SELECT f.score_satisfaction, COUNT(*) AS nb
    FROM FAIT_VENTES f
    WHERE f.score_satisfaction IS NOT NULL
    GROUP BY f.score_satisfaction
    ORDER BY f.score_satisfaction
""")

df_trimestre = query("""
    SELECT t.annee, t.trimestre,
           t.annee || '-T' || t.trimestre AS periode,
           ROUND(SUM(f.prix_unitaire + f.frais_livraison), 2) AS ca_total
    FROM FAIT_VENTES f
    JOIN DIM_TEMPS t ON f.temps_id = t.temps_id
    GROUP BY t.annee, t.trimestre
    ORDER BY t.annee, t.trimestre
""")

# ── KPI summary numbers ─────────────────────────────────
total_ca     = df_ca["ca_total"].sum()
total_cmd    = df_ca["nb_commandes"].sum()
score_global = query("SELECT ROUND(AVG(score_satisfaction),2) AS s FROM FAIT_VENTES WHERE score_satisfaction IS NOT NULL")["s"][0]
delai_global = query("SELECT ROUND(AVG(delai_livraison_jours),1) AS d FROM FAIT_VENTES WHERE delai_livraison_jours > 0")["d"][0]

regions = ["Toutes"] + sorted(df_ca["region"].unique().tolist())

# ── App layout ───────────────────────────────────────────
app = Dash(__name__)
app.title = "Dashboard Olist DW — GLSI 2026"

CARD = {"background": "#1e1e2e", "borderRadius": "12px",
        "padding": "20px", "margin": "10px", "color": "white"}

app.layout = html.Div(style={"background": "#0f0f1a", "minHeight": "100vh",
                               "fontFamily": "Segoe UI, sans-serif", "padding": "20px"}, children=[

    html.H1("📦 Entrepôt de données — Olist Brazilian E-Commerce",
            style={"color": "#a78bfa", "textAlign": "center", "marginBottom": "4px"}),
    html.P("GLSI 2026 · Houcine ESSID · Source: Kaggle Olist Dataset",
           style={"color": "#6b7280", "textAlign": "center", "marginBottom": "20px"}),

    # ── KPI cards ──
    html.Div(style={"display": "flex", "flexWrap": "wrap", "justifyContent": "center"}, children=[
        html.Div(style={**CARD, "minWidth": "180px", "textAlign": "center"}, children=[
            html.H2(f"R$ {total_ca:,.0f}", style={"color": "#34d399", "margin": "0"}),
            html.P("Chiffre d'affaires total", style={"color": "#9ca3af", "margin": "0"})
        ]),
        html.Div(style={**CARD, "minWidth": "180px", "textAlign": "center"}, children=[
            html.H2(f"{total_cmd:,.0f}", style={"color": "#60a5fa", "margin": "0"}),
            html.P("Commandes livrées", style={"color": "#9ca3af", "margin": "0"})
        ]),
        html.Div(style={**CARD, "minWidth": "180px", "textAlign": "center"}, children=[
            html.H2(f"⭐ {score_global}", style={"color": "#fbbf24", "margin": "0"}),
            html.P("Score satisfaction moyen", style={"color": "#9ca3af", "margin": "0"})
        ]),
        html.Div(style={**CARD, "minWidth": "180px", "textAlign": "center"}, children=[
            html.H2(f"🚚 {delai_global} j", style={"color": "#f87171", "margin": "0"}),
            html.P("Délai livraison moyen", style={"color": "#9ca3af", "margin": "0"})
        ]),
    ]),

    # ── Filter ──
    html.Div(style={"textAlign": "center", "margin": "20px 0"}, children=[
        html.Label("Filtrer par région :", style={"color": "#d1d5db", "marginRight": "10px"}),
        dcc.Dropdown(id="region-filter", options=[{"label": r, "value": r} for r in regions],
                     value="Toutes", clearable=False,
                     style={"width": "300px", "display": "inline-block",
                            "background": "#1e1e2e", "color": "black"})
    ]),

    # ── Charts row 1 ──
    html.Div(style={"display": "flex", "flexWrap": "wrap"}, children=[
        html.Div(style={**CARD, "flex": "2", "minWidth": "400px"}, children=[
            html.H3("CA mensuel par région", style={"color": "#c4b5fd"}),
            dcc.Graph(id="ca-mensuel-chart")
        ]),
        html.Div(style={**CARD, "flex": "1", "minWidth": "300px"}, children=[
            html.H3("Distribution des scores", style={"color": "#c4b5fd"}),
            dcc.Graph(id="score-chart")
        ]),
    ]),

    # ── Charts row 2 ──
    html.Div(style={"display": "flex", "flexWrap": "wrap"}, children=[
        html.Div(style={**CARD, "flex": "1", "minWidth": "350px"}, children=[
            html.H3("Top 15 catégories — CA", style={"color": "#c4b5fd"}),
            dcc.Graph(id="categorie-chart")
        ]),
        html.Div(style={**CARD, "flex": "1", "minWidth": "350px"}, children=[
            html.H3("Délai moyen de livraison par état", style={"color": "#c4b5fd"}),
            dcc.Graph(id="delai-chart")
        ]),
    ]),

    # ── Trend chart ──
    html.Div(style=CARD, children=[
        html.H3("📈 Évolution trimestrielle du CA (base pour prévisions)", style={"color": "#c4b5fd"}),
        dcc.Graph(id="trend-chart")
    ]),
])

TEMPLATE = "plotly_dark"

# ── Callbacks ────────────────────────────────────────────
@app.callback(
    Output("ca-mensuel-chart", "figure"),
    Output("score-chart", "figure"),
    Output("categorie-chart", "figure"),
    Output("delai-chart", "figure"),
    Output("trend-chart", "figure"),
    Input("region-filter", "value"),
)
def update_charts(region):
    df = df_ca if region == "Toutes" else df_ca[df_ca["region"] == region]
    df_agg = df.groupby("periode", as_index=False)["ca_total"].sum()
    df_agg = df_agg.sort_values("periode")

    fig_ca = px.bar(df_agg, x="periode", y="ca_total", template=TEMPLATE,
                    color="ca_total", color_continuous_scale="Purples",
                    labels={"ca_total": "CA (BRL)", "periode": "Mois"})
    fig_ca.update_layout(showlegend=False, paper_bgcolor="rgba(0,0,0,0)",
                         plot_bgcolor="rgba(0,0,0,0)")

    fig_score = px.bar(df_score, x="score_satisfaction", y="nb", template=TEMPLATE,
                       color="score_satisfaction",
                       color_continuous_scale=["#ef4444","#fb923c","#facc15","#4ade80","#22d3ee"],
                       labels={"nb": "Nb avis", "score_satisfaction": "Score (1-5)"})
    fig_score.update_layout(showlegend=False, paper_bgcolor="rgba(0,0,0,0)",
                             plot_bgcolor="rgba(0,0,0,0)")

    fig_cat = px.bar(df_cat.sort_values("ca_categorie"), x="ca_categorie", y="categorie",
                     orientation="h", template=TEMPLATE, color="score_moyen",
                     color_continuous_scale="Tealgrn",
                     labels={"ca_categorie": "CA (BRL)", "categorie": "Catégorie",
                             "score_moyen": "Score moy."})
    fig_cat.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")

    dd = df_delai if region == "Toutes" else df_delai[df_delai["region"] == region]
    fig_delai = px.bar(dd.head(20).sort_values("delai_moyen"), x="delai_moyen", y="etat",
                       orientation="h", template=TEMPLATE, color="delai_moyen",
                       color_continuous_scale="Reds",
                       labels={"delai_moyen": "Délai (jours)", "etat": "État"})
    fig_delai.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")

    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(
        x=df_trimestre["periode"], y=df_trimestre["ca_total"],
        mode="lines+markers", name="CA",
        line=dict(color="#a78bfa", width=3),
        marker=dict(size=8)
    ))
    fig_trend.update_layout(template=TEMPLATE, paper_bgcolor="rgba(0,0,0,0)",
                             plot_bgcolor="rgba(0,0,0,0)",
                             xaxis_title="Trimestre", yaxis_title="CA (BRL)")

    return fig_ca, fig_score, fig_cat, fig_delai, fig_trend


# Expose Flask server for gunicorn (required for production hosting)
server = app.server

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8050))
    debug = os.environ.get("DASH_DEBUG", "false").lower() == "true"
    print(f"🚀 Starting dashboard → http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
