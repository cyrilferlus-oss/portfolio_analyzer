import streamlit as st
import pandas as pd
from pathlib import Path

from data_loader import DatabaseLoader
from portfolio import Portfolio
from charts import geo_chart, currency_chart, holdings_chart

DB_PATH = Path(__file__).parent / "data" / "base_de_donnees.xlsx"

st.set_page_config(
    page_title="Analyse de Portefeuille",
    page_icon="📈",
    layout="wide",
)


@st.cache_resource
def get_loader() -> DatabaseLoader:
    loader = DatabaseLoader(DB_PATH)
    loader.load()
    return loader


def parse_inputs(isin_text: str, weight_text: str) -> tuple[list[str], list[float], str | None]:
    isins = [x.strip() for x in isin_text.strip().splitlines() if x.strip()]
    raw_weights = [x.strip() for x in weight_text.strip().splitlines() if x.strip()]

    if len(isins) == 0:
        return [], [], "Veuillez saisir au moins un ISIN."

    if len(raw_weights) == 0:
        weights = [1.0 / len(isins)] * len(isins)
        return isins, weights, None

    if len(raw_weights) != len(isins):
        return [], [], f"Nombre d'ISIN ({len(isins)}) ≠ nombre de poids ({len(raw_weights)})."

    try:
        weights = [float(w.replace(",", ".").replace("%", "")) for w in raw_weights]
    except ValueError:
        return [], [], "Les poids doivent être des nombres (ex: 25 ou 25.5 ou 25%)."

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
        st.subheader("Saisie du portefeuille")
        isin_input = st.text_area(
            "ISIN (un par ligne)",
            placeholder="FR01528475\nFR1545224\nUS556151562",
            height=180,
        )
        weight_input = st.text_area(
            "Poids (un par ligne, en % ou valeur — laisser vide pour équipondérer)",
            placeholder="40\n35\n25",
            height=180,
        )
        analyze_btn = st.button("Analyser", type="primary", use_container_width=True)

    with col_right:
        st.subheader("Aide")
        st.info(
            "**Format ISIN** : saisissez un code ISIN par ligne, sans espaces.\n\n"
            "**Poids** : en pourcentage (ex: `40` pour 40%) ou en valeur absolue. "
            "Les poids sont normalisés automatiquement à 100%.\n\n"
            "**ISIN disponibles dans la base :**\n"
            + "\n".join(f"- `{i}`" for i in loader.list_isins())
        )

    if not analyze_btn:
        return

    isins, weights, error = parse_inputs(isin_input, weight_input)
    if error:
        st.error(error)
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

    st.divider()
    st.subheader("Analyses graphiques")

    tab_geo, tab_actions, tab_devise = st.tabs(
        ["🌍 Répartition Géographique", "📊 Répartition par Action", "💱 Répartition par Devise"]
    )

    with tab_geo:
        geo_df = portfolio.geo_breakdown()
        fig = geo_chart(geo_df)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(geo_df.style.format({"Poids (%)": "{:.2f}%"}), hide_index=True)

    with tab_actions:
        hold_df = portfolio.holdings_breakdown()
        fig = holdings_chart(hold_df)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(hold_df.style.format({"Poids (%)": "{:.2f}%"}), hide_index=True)

    with tab_devise:
        cur_df = portfolio.currency_breakdown()
        fig = currency_chart(cur_df)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(cur_df.style.format({"Poids (%)": "{:.2f}%"}), hide_index=True)


if __name__ == "__main__":
    main()
