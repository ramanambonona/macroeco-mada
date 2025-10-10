# modules/secteur_monetaire.py  # Note: Updated path to match main.py import
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from utils.bfm_scraper import (
    get_taux_directeur,
    get_taux_change,
    get_agregats_monetaires,
    get_reserves_obligatoires,
    get_inflation_latest,
    get_marche_monetaire_rates,
    get_bta_rates
)

def app():
    st.title("💳 Secteur Monétaire")

    # Expanded tabs for all variables
    onglet_inflation, onglet_marche, onglet_bta, onglet_agregats, onglet_politique = st.tabs([
        "📈 Inflation", 
        "🏦 Marché Monétaire", 
        "📋 Marché des BTA",
        "📉 Agrégats Monétaires", 
        "⚖️ Politique Monétaire"
    ])

    # === Inflation ===
    with onglet_inflation:
        st.header("Inflation (IPC - Dernier Taux)")
        df_inflation = get_inflation_latest()
        if not df_inflation.empty:
            st.metric("Taux d'inflation glissement annuel", f"{df_inflation.iloc[0]['Taux']:.1f}%", label=f"({df_inflation.iloc[0]['Date'].strftime('%B %Y')})")
            # For historical, note: Add manual or bulletin scraping
            st.info("Pour historique complet, consultez les bulletins de conjoncture sur le site BFM.")
        else:
            st.warning("Pas de données inflation disponibles.")

    # === Marché Monétaire ===
    with onglet_marche:
        st.header("Marché des Changes")

        col1, col2, col3 = st.columns(3)
        with col1:
            start_date = st.date_input("Début", value=datetime(2023, 1, 1))
        with col2:
            end_date = st.date_input("Fin", value=datetime.today())
        with col3:
            devise = st.selectbox("Devise", ["EUR", "USD", "JPY"])

        if start_date <= end_date:
            df_change = get_taux_change(start_date, end_date, devise)

            if not df_change.empty:
                fig = px.line(df_change, x='Date', y='Taux',
                              title=f"Évolution du taux {devise}/MGA",
                              labels={'Taux': f'MGA pour 1 {devise}'})
                st.plotly_chart(fig, use_container_width=True)

                dernier_taux = df_change.iloc[-1]['Taux']
                st.metric(f"Dernier taux {devise}/MGA",
                          f"{dernier_taux:,.2f}",
                          delta=None)
            else:
                st.warning("❌ Pas de données disponibles sur cette période.")
        else:
            st.error("La date de fin doit être postérieure à la date de début.")

        # Taux interbancaires
        st.subheader("Taux Interbancaires (TMP)")
        df_rates = get_marche_monetaire_rates()
        if not df_rates.empty:
            st.dataframe(df_rates)
            if 'TMP_lt7' in df_rates.columns:
                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric("TMP <7 jours", f"{df_rates['TMP_lt7'].iloc[0]:.2f}%")
                with col_b:
                    if 'TMP_gt7' in df_rates.columns:
                        st.metric("TMP >7 jours", f"{df_rates['TMP_gt7'].iloc[0]:.2f}%")
        else:
            st.warning("Pas de données taux marché.")

    # === Marché BTA ===
    with onglet_bta:
        st.header("Marché des Bons du Trésor (BTA)")
        df_bta = get_bta_rates()
        if not df_bta.empty:
            fig = px.bar(df_bta, x='Maturité', y='Taux',
                         title="Taux de Rendement Moyen des BTA",
                         labels={'Taux': 'Taux (%)'})
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(df_bta)
        else:
            st.warning("Pas de données BTA disponibles.")

    # === Agrégats Monétaires ===
    with onglet_agregats:
        st.header("Agrégats Monétaires (Latest)")

        df_agregats = get_agregats_monetaires()

        if not df_agregats.empty:
            st.dataframe(df_agregats)

            indicateur = st.selectbox("Choisir un agrégat", options=[col for col in df_agregats.columns if col != 'Date'])

            fig = px.bar(df_agregats, x='Date', y=indicateur,
                         title=f"Valeur de {indicateur}",
                         labels={indicateur: "Milliards MGA"})
            st.plotly_chart(fig, use_container_width=True)
            st.info("Pour historique, implémentez scraping des bulletins trimestriels.")

        else:
            st.error("Erreur chargement agrégats monétaires.")

    # === Politique Monétaire ===
    with onglet_politique:
        st.header("Outils de Politique Monétaire")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Taux Directeur Historique")
            df_taux = get_taux_directeur()
            if not df_taux.empty:
                fig = px.line(df_taux, x='Date', y='Taux',
                              title="Évolution du Taux Directeur",
                              labels={'Taux': 'Taux (%)'})
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(df_taux.tail(5))
            else:
                st.warning("Pas de données taux directeur.")

        with col2:
            st.subheader("Réserves Obligatoires Historique")
            df_reserves = get_reserves_obligatoires()
            if not df_reserves.empty:
                fig = px.line(df_reserves, x='Date', y='Taux',
                              title="Évolution des Réserves Obligatoires",
                              labels={'Taux': '% des dépôts'})
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(df_reserves.tail(5))
            else:
                st.warning("Pas de données réserves obligatoires.")

if __name__ == "__main__":
    app()
