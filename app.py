import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import date
import io

from data_loader import DatabaseLoader
from portfolio import Portfolio
from charts import geo_chart, currency_chart, holdings_chart, category_chart
from report import generate_pdf

st.set_page_config(
    page_title="Analyse de Portefeuille",
    page_icon="📈",
    layout="wide",
)

_DEFAULT_ROWS = 6


def get_loader_from_upload(uploaded_file) -> DatabaseLoader | None:
    if uploaded_file is None:
        return None
    bytes_data = uploaded_file.read()
    loader = DatabaseLoader(io.BytesIO(bytes_data))
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

    st.divider()

    # Upload de la base de données
    st.subheader("📂 Base de données")
    uploaded_file = st.file_uploader(
        "Uploadez votre fichier Excel (base de données)",
        type=["xlsx"],
        help="Le fichier reste sur votre navigateur et n'est jamais stocké en ligne.",
    )

    if uploaded_file is None:
        st.info("Veuillez uploader votre base de données Excel pour commencer.")
        return

    loader = get_loader_from_upload(uploaded_file)
    if loader is None:
        st.error("Impossible de charger le fichier Excel.")
        return

    db = loader.load()
    with st.expander("📋 Voir la base de données chargée", expanded=False):
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
        fig_cat = category_chart(cat_df)
        st.plotly_chart(fig_cat, use_container_width=True)
        st.dataframe(cat_df.style.format({"Poids (%)": "{:.2f}%"}), hide_index=True)

    st.divider()
    st.subheader("Téléchargement")

    with st.spinner("Génération du rapport PDF..."):
        pdf_bytes = generate_pdf(
            summary_df=portfolio.summary_table(),
            overweight_df=overweight,
            fig_geo=geo_chart(portfolio.geo_breakdown()),
            fig_holdings=holdings_chart(portfolio.holdings_breakdown()),
            fig_currency=currency_chart(portfolio.currency_breakdown()),
            fig_category=fig_cat,
        )

    st.download_button(
        label="📄 Télécharger le rapport PDF",
        data=pdf_bytes,
        file_name=f"rapport_portefeuille_{date.today().strftime('%Y%m%d')}.pdf",
        mime="application/pdf",
        type="primary",
        use_container_width=True,
    )


if __name__ == "__main__":
    main()
