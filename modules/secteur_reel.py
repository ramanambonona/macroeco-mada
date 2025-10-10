# secteur_reel.py

import streamlit as st
import pandas as pd
import plotly.express as px
from utils.api_worldbank import get_data
from utils.excel_loader import load_excel
from utils.forecast_tools import streamlit_forecast_interface
from utils.extract_data_instat import extract_data_instat  

# === Indicateurs de base (pour l'API Banque Mondiale) ===
INDICATORS = {
    "PIB": "NY.GDP.MKTP.CD",
    "Consommation": "NE.CON.TOTL.CD",
    "Investissement": "NE.GDI.TOTL.CD",
    "Dépenses publiques": "NE.CON.GOVT.CD",
    "Exportations": "NE.EXP.GNFS.CD",
    "Importations": "NE.IMP.GNFS.CD",
}

def app():
    st.title("📊 Secteur Réel de l'Économie Malagasy")

    onglet_data, onglet_prev = st.tabs(["📈 Données Historiques", "🔮 Prévision"])

    with onglet_data:
        source = st.radio("📦 Source des données", ["API Banque Mondiale", "Importer Excel", "INSTAT"])
        df = None  # Initialiser le DataFrame

        if source == "Importer Excel":
            df = load_excel()
        elif source == "INSTAT":
            # Appel à la fonction modifiée pour extraire de l'Excel INSTAT
            df = extract_data_instat()
        else:  # API Banque Mondiale
            dfs = []
            for nom, code in INDICATORS.items():
                data = get_data(code)
                if not data.empty and "Année" in data.columns:
                    dfs.append(data.rename(columns={"Valeur": nom}).set_index("Année"))
            df = pd.concat(dfs, axis=1).dropna(how="all").reset_index() if dfs else None

        if df is None or df.empty:
            st.warning("⚠️ Aucune donnée disponible pour la source sélectionnée.")
            return

        # Assurer que 'Année' est de type int
        if 'Année' in df.columns:
            df['Année'] = df['Année'].astype(int)

        # === Calculs supplémentaires (conditionnels à la présence des colonnes) ===
        required_for_calculations = ["PIB", "Exportations", "Importations", "Investissement", "Dépenses publiques"]
        
        if all(col in df.columns for col in required_for_calculations):
            df["Balance Commerciale"] = df["Exportations"] - df["Importations"]
            df["Investissement/PIB (%)"] = df["Investissement"] / df["PIB"] * 100
            df["Dépenses/PIB (%)"] = df["Dépenses publiques"] / df["PIB"] * 100
            df["Exportations/PIB (%)"] = df["Exportations"] / df["PIB"] * 100
            
            # Calcul des taux de croissance si non déjà présents (pour INSTAT, ils le sont partiellement)
            base_cols = ["PIB", "Consommation", "Investissement", "Dépenses publiques", "Exportations", "Importations"]
            for col in base_cols:
                if col in df.columns and f"Croissance {col} (%)" not in df.columns:
                    df[f"Croissance {col} (%)"] = df[col].pct_change() * 100

        else:
            st.info("Les données extraites ne permettent pas de calculer tous les ratios (PIB, Investissement, etc. manquants). Affichage des données brutes.")

        st.dataframe(df.set_index("Année"), use_container_width=True)

        # Groupes dynamiques, incluant nouveaux indicateurs INSTAT
        groupes = {
            "Valeurs": [col for col in ["PIB", "Consommation", "Investissement", "Dépenses publiques", "Exportations", "Importations", "Secteur Primaire", "Secteur Secondaire", "Secteur Tertiaire"] if col in df.columns],
            "Ratios": [col for col in ["Investissement/PIB (%)", "Dépenses/PIB (%)", "Exportations/PIB (%)"] if col in df.columns],
            "Croissance": [col for col in df.columns if col.startswith("Croissance")],
            "Commerce Extérieur": [col for col in ["Exportations", "Importations", "Balance Commerciale"] if col in df.columns]
        }
        
        groupes = {k: v for k, v in groupes.items() if v}
        
        if not groupes:
            st.info("Le DataFrame est trop limité pour la visualisation. Impossible de créer des groupes.")
            return

        regroupement = st.radio("Regrouper par type de variable", list(groupes.keys()))

        default_selection = groupes[regroupement] if groupes.get(regroupement) else []

        selection = st.multiselect("Sélectionnez les variables à afficher", groupes[regroupement], default=default_selection)

        if not selection:
            st.warning("Veuillez sélectionner au moins une variable à afficher.")
        else:
            fig = px.line(df, x="Année", y=selection, title=f"{regroupement} - Visualisation")
            st.plotly_chart(fig, use_container_width=True)

    with onglet_prev:
        if df is not None and not df.empty and 'selection' in locals() and selection:
            st.markdown("### 🔮 Prévision des variables choisies")
            streamlit_forecast_interface(df, selection, multivariate=len(selection) > 1)
        else:
            st.warning("Importez ou récupérez d'abord les données pour effectuer une prévision.")