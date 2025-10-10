import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from utils.bfm_scraper import (
    get_taux_directeur,
    get_taux_change,
    get_agregats_monetaires,
    get_reserves_obligatoires
)

def app():
    st.title("💳 Secteur Monétaire")

    onglet_marche, onglet_agregats, onglet_politique = st.tabs([
        "🏦 Marché Monétaire", 
        "📉 Agrégats Monétaires", 
        "⚖️ Politique Monétaire"
    ])

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

    # === Agrégats Monétaires ===
    with onglet_agregats:
        st.header("Agrégats Monétaires")

        df_agregats = get_agregats_monetaires()

        if not df_agregats.empty:
            st.dataframe(df_agregats)

            indicateur = st.selectbox("Choisir un agrégat", options=[
                'M1 (Liquidités)', 'M2 (Masse monétaire)', 'M3 (Quasi-monnaie)'
            ])

            fig = px.bar(df_agregats, x='Date', y=indicateur,
                         title=f"Évolution de {indicateur}",
                         labels={indicateur: "Milliards MGA"})
            st.plotly_chart(fig, use_container_width=True)

        else:
            st.error("Erreur chargement agrégats monétaires.")

    # === Politique Monétaire ===
    with onglet_politique:
        st.header("Outils de Politique Monétaire")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Taux Directeur")
            df_taux = get_taux_directeur()
            if not df_taux.empty:
                fig = px.bar(df_taux, x='Date', y='Taux',
                            title="Historique des taux directeurs",
                            labels={'Taux': 'Taux (%)'})
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Réserves Obligatoires")
            df_reserves = get_reserves_obligatoires()
            if not df_reserves.empty:
                fig = px.line(df_reserves, x='Date', y='Taux',
                              title="Évolution des réserves obligatoires",
                              labels={'Taux': '% des dépôts'})
                st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    app()

