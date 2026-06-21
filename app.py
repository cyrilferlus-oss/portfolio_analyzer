import streamlit as st
import pandas as pd
from pathlib import Path

from data_loader import DatabaseLoader
from portfolio import Portfolio
from charts import geo_chart, currency_chart, holdings_chart, category_chart

DB_PATH = Path(__file__).parent / "data" / "base_de_donnees.xlsx"

st.set_page_config(
    page_title="Analyse de Portefeuille",
    page_icon="📈",
    layout="wide",
)

_DEFAULT_ROWS = 6


@st.cache_resource
def get_loader() -> DatabaseLoader:
    loader = DatabaseLoader(DB_PATH)
    loader.load()
    return loader


def get_portfolio_input() -> tuple[list[str], list[float], str | None]:
    st.subheader("Saisie du portefeuille")
    st.caption("Remplissez les lignes ci-dessous. Laissez le poids à 0 pour équipondérer automatiquement.")

    empty = pd.DataFrame({"ISIN": [""] * _DEFAULT_ROWS, "Poids (%)": [0.0] * _DEFAULT_ROWS})

    edited = st.data_editor(
        empty,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "ISIN": st.column_config.TextColumn("ISIN", help="Code ISIN de la valeur", width="medium"),
            "Poids (%)": st.column_config.NumberColumn("Poids (%)", help="Poids en % (ex: 25 pour 25%)", min_value=0.0, max_value=100.0, step=0.5, format="%.1f"),
        },
        hide_index=True,
    )

    rows = edited[edited["ISIN"].astype(str).str.strip() != ""]
    if rows.empty:
        return [], [], None

    isins = rows["ISIN"].astype(str).str.strip().tolist()
    weights = rows["Poids (%)"].fillna(0.0).tolist()

    if all(w == 0 for w in weights):
        weights = [1.0 / len(isins)] * len(isins)

    return isins, weights, None


def main():
    st.title("📈 Analyse de Portefeuille")
    st.markdown("Entrez vos ISIN et leurs poids pour analyser la composition de votre portefeuille.")

    loader = get_loader()
    db = loader.load()

    with st.expander("📋 Voir la base de données disponible", expanded=False):
        st.dataframe(db, use_container_width=True)

    st.divider()

    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        isins, weights, error = get_portfolio_input()
        analyze_btn = st.button("Analyser", type="primary", use_container_width=True)

    with col_right:
        st.subheader("Aide")
        st.info(
            "**ISIN** : saisissez le code ISIN de chaque valeur.\n\n"
            "**Poids** : en pourcentage (ex: `40` pour 40%). "
            "Les poids sont normalisés automatiquement à 100%.\n\n"
            "Laissez tous les poids à `0` pour équipondérer.\n\n"
            "**ISIN disponibles dans la base :**\n"
            + "\n".join(f"- `{i}`" for i in loader.list_isins())
        )

    if not analyze_btn:
        return

    if error:
        st.error(error)
        return

    if not isins:
        st.warning("Veuillez saisir au moins un ISIN.")
        return

    portfolio = Portfolio(loader)
    portfolio.load_from_input(isins, weights)

    if portfolio.errors:
        for e in portfolio.errors:
            st.warning(e)

    if not portfolio.positions:
        st.error("Aucune position valide trouvée.")
        return

    total_w = portfolio.total_weight()
    if abs(total_w - 100) > 0.01 and total_w != len(portfolio.positions):
        st.info(f"Poids normalisés de {total_w:.1f}% → 100%")

    st.divider()
    st.subheader("Composition du portefeuille")
    st.dataframe(portfolio.summary_table(), use_container_width=True, hide_index=True)

    overweight = portfolio.overweight_positions(threshold=5.0)
    if not overweight.empty:
        st.divider()
        st.subheader("⚠️ Positions représentant plus de 5% du portefeuille")
        st.dataframe(
            overweight.style.format({"Poids (%)": "{:.2f}%"}).highlight_between(
                subset=["Poids (%)"], left=5, right=100, color="#ffe0e0"
            ),
            use_container_width=True,
            hide_index=True,
        )

    st.divider()
    st.subheader("Analyses graphiques")

    tab_geo, tab_actions, tab_devise, tab_cat = st.tabs([
        "🌍 Répartition Géographique",
        "📊 Répartition par Action",
        "💱 Répartition par Devise",
        "🏷️ Répartition par Catégorie",
    ])

    with tab_geo:
        geo_df = portfolio.geo_breakdown()
        st.plotly_chart(geo_chart(geo_df), use_container_width=True)
        st.dataframe(geo_df.style.format({"Poids (%)": "{:.2f}%"}), hide_index=True)

    with tab_actions:
        hold_df = portfolio.holdings_breakdown()
        st.plotly_chart(holdings_chart(hold_df), use_container_width=True)
        st.dataframe(hold_df.style.format({"Poids (%)": "{:.2f}%"}), hide_index=True)

    with tab_devise:
        cur_df = portfolio.currency_breakdown()
        st.plotly_chart(currency_chart(cur_df), use_container_width=True)
        st.dataframe(cur_df.style.format({"Poids (%)": "{:.2f}%"}), hide_index=True)

    with tab_cat:
        cat_df = portfolio.category_breakdown()
        st.plotly_chart(category_chart(cat_df), use_container_width=True)
        st.dataframe(cat_df.style.format({"Poids (%)": "{:.2f}%"}), hide_index=True)


if __name__ == "__main__":
    main()
