import streamlit as st
import pandas as pd
import plotly.express as px
from utils.api_worldbank import get_data
from utils.excel_loader import load_excel

INDICATORS = {
    "Compte courant (%PIB)": "BN.CAB.XOKA.GD.ZS",
    "Compte financier net (%PIB)": "BN.FIN.TOTL.GD.ZS",
    "IDE net (%PIB)": "BX.KLT.DINV.WD.GD.ZS",
    "Transferts courants (%PIB)": "BX.TRF.PWKR.DT.GD.ZS",
    "Réserves internationales (USD)": "FI.RES.TOTL.CD",
}

def app():
    st.title("🌍 Secteur Extérieur – Balance des Paiements")

    source = st.radio("Source des données :", ["API Banque Mondiale", "Importer Excel"])

    if source == "Importer Excel":
        df = load_excel()
    else:
        dfs = []
        for nom, code in INDICATORS.items():
            data = get_data(code)
            if "Année" in data.columns:
                dfs.append(data.rename(columns={"Valeur": nom}).set_index("Année"))
        df = pd.concat(dfs, axis=1).dropna().reset_index() if dfs else None

    if df is not None and not df.empty:
        st.dataframe(df.set_index("Année"), use_container_width=True)
        fig = px.line(df, x='Année', y=["Compte courant (%PIB)", "Compte financier net (%PIB)", "IDE net (%PIB)", "Transferts courants (%PIB)"],
                      title="Évolution des principales composantes (% du PIB)")
        st.plotly_chart(fig, use_container_width=True)

        fig2 = px.line(df, x='Année', y="Réserves internationales (USD)",
                       title="Réserves Internationales (USD courants)")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.warning("⚠️ Aucune donnée disponible ou données invalides.")
