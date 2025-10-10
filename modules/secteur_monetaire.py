import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

try:
    from utils.common_ui import inject_css, floating_note, download_box
except ImportError:
    from common_ui import inject_css, floating_note, download_box

from utils.bfm_scraper import (
    get_taux_directeur,
    get_taux_change,
    get_agregats_monetaires,
    get_reserves_obligatoires,
    get_inflation_latest,
    get_marche_monetaire_rates,
    get_bta_rates,
)

def app():
    # Apparence / CSS / palette
    inject_css("styles.css", palette=st.session_state.get("palette", "clair"))
    with st.sidebar:
        with st.expander("🎨 Apparence", expanded=False):
            pal = st.selectbox(
                "Palette",
                ["clair", "creme", "ardoise-clair", "ardoise-sombre"],
                index=["clair","creme","ardoise-clair","ardoise-sombre"].index(
                    st.session_state.get("palette","clair")
                ),
            )
            st.session_state.palette = pal
            inject_css("styles.css", palette=pal)

    st.title("💳 Secteur Monétaire")

    onglet_inflation, onglet_marche, onglet_bta, onglet_agregats, onglet_politique = st.tabs([
        "📈 Inflation", 
        "🏦 Marché Monétaire", 
        "📋 Marché des BTA",
        "📉 Agrégats Monétaires", 
        "⚖️ Politique Monétaire"
    ])

    # Inflation
    with onglet_inflation:
        st.header("Inflation (IPC - Dernier Taux)")
        df_inflation = get_inflation_latest()
        if not df_inflation.empty:
            period_txt = df_inflation.iloc[0]['Date'].strftime('%B %Y')
            st.metric("Taux d'inflation (glissement annuel)", f"{df_inflation.iloc[0]['Taux']:.1f}%", help=f"Période: {period_txt}")
            download_box(df_inflation, "inflation_dernier_taux", key_prefix="infl")
        else:
            st.warning("Pas de données inflation disponibles.")

    # Marché des changes + TMP
    with onglet_marche:
        st.header("Marché des Changes")
        c1, c2, c3 = st.columns(3)
        with c1: start_date = st.date_input("Début", value=datetime(2023,1,1))
        with c2: end_date   = st.date_input("Fin", value=datetime.today())
        with c3: devise     = st.selectbox("Devise", ["EUR","USD","JPY"])

        if start_date <= end_date:
            df_change = get_taux_change(start_date, end_date, devise)
            if not df_change.empty:
                fig = px.line(df_change, x='Date', y='Taux',
                              title=f"Évolution du taux {devise}/MGA",
                              labels={'Taux': f'MGA pour 1 {devise}'})
                st.plotly_chart(fig, use_container_width=True)
                st.metric(f"Dernier taux {devise}/MGA", f"{df_change.iloc[-1]['Taux']:,.2f}")
                download_box(df_change, f"taux_change_{devise}", key_prefix="fx")
            else:
                st.warning("❌ Pas de données disponibles sur cette période.")
        else:
            st.error("La date de fin doit être postérieure à la date de début.")

        st.subheader("Taux Interbancaires (TMP)")
        df_rates = get_marche_monetaire_rates()
        if not df_rates.empty:
            st.dataframe(df_rates, use_container_width=True)
            cc1, cc2 = st.columns(2)
            if 'TMP_lt7' in df_rates.columns and pd.notna(df_rates['TMP_lt7'].iloc[0]):
                with cc1: st.metric("TMP < 7 jours", f"{df_rates['TMP_lt7'].iloc[0]:.2f}%")
            if 'TMP_gt7' in df_rates.columns and pd.notna(df_rates['TMP_gt7'].iloc[0]):
                with cc2: st.metric("TMP > 7 jours", f"{df_rates['TMP_gt7'].iloc[0]:.2f}%")
            download_box(df_rates, "taux_marche_monetaire", key_prefix="tmp")
        else:
            st.warning("Pas de données taux marché.")

    with onglet_bta:
        st.header("Marché des Bons du Trésor (BTA)")
        df_bta = get_bta_rates()
        if not df_bta.empty:
            fig = px.bar(df_bta, x='Maturité', y='Taux',
                         title="Taux de rendement moyen des BTA",
                         labels={'Taux': 'Taux (%)'})
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(df_bta, use_container_width=True)
            download_box(df_bta, "bta_taux", key_prefix="bta")
        else:
            st.warning("Pas de données BTA disponibles.")

    with onglet_agregats:
        st.header("Agrégats Monétaires (Dernière publication)")
        df_agregats = get_agregats_monetaires()
        if not df_agregats.empty:
            st.dataframe(df_agregats, use_container_width=True)
            indicateur = st.selectbox("Choisir un agrégat", options=[c for c in df_agregats.columns if c != 'Date'])
            fig = px.bar(df_agregats, x='Date', y=indicateur,
                         title=f"Valeur de {indicateur}",
                         labels={indicateur: "Milliards MGA"})
            st.plotly_chart(fig, use_container_width=True)
            download_box(df_agregats, "agregats_monetaire_latest", key_prefix="agreg")
        else:
            st.error("Erreur chargement agrégats monétaires.")

    with onglet_politique:
        st.header("Outils de Politique Monétaire")
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Taux Directeur (Historique)")
            df_taux = get_taux_directeur()
            if not df_taux.empty:
                fig = px.line(df_taux, x='Date', y='Taux',
                              title="Évolution du Taux Directeur",
                              labels={'Taux': 'Taux (%)'})
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(df_taux.tail(5), use_container_width=True)
                download_box(df_taux, "taux_directeur_historique", key_prefix="tauxdir")
            else:
                st.warning("Pas de données taux directeur.")

        with col2:
            st.subheader("Réserves Obligatoires (Historique)")
            df_res = get_reserves_obligatoires()
            if not df_res.empty:
                fig = px.line(df_res, x='Date', y='Taux',
                              title="Évolution des Réserves Obligatoires",
                              labels={'Taux': '% des dépôts'})
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(df_res.tail(5), use_container_width=True)
                download_box(df_res, "reserves_obligatoires_historique", key_prefix="resob")
            else:
                st.warning("Pas de données réserves obligatoires.")

    floating_note()
