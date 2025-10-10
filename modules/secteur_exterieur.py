import streamlit as st
import pandas as pd

# Helpers communs
try:
    from utils.common_ui import inject_css, build_module, floating_note
except ImportError:
    from common_ui import inject_css, build_module, floating_note

# World Bank
try:
    from utils.api_worldbank import get_data as wb_get
except ImportError:
    from api_worldbank import get_data as wb_get

st.set_page_config(page_title="Secteur extérieur", page_icon="🌍", layout="wide")

# CSS + palette
inject_css("styles.css", palette=st.session_state.get("palette", "clair"))
with st.sidebar:
    st.subheader("🎨 Apparence")
    pal = st.selectbox(
        "Palette", ["clair", "creme", "ardoise-clair", "ardoise-sombre"],
        index=["clair", "creme", "ardoise-clair", "ardoise-sombre"].index(st.session_state.get("palette", "clair")),
    )
    st.session_state.palette = pal
    inject_css("styles.css", palette=pal)

# --- CHARGEMENT DONNÉES (World Bank) ---
WB_EXT_INDICATORS = {
    "Compte courant (% PIB)": "BN.CAB.XOKA.GD.ZS",
    "Flux IDE net (% PIB)": "BX.KLT.DINV.WD.GD.ZS",
    "Transferts courants (% PIB)": "BX.TRF.PWKR.DT.GD.ZS",
    "Réserves internationales (USD)": "FI.RES.TOTL.CD",
    "Balance biens & services (% PIB)": "NE.RSB.GNFS.ZS",
}

def _wb_to_df(label: str, code: str) -> pd.DataFrame:
    df = wb_get(code)  # renvoie ['Année','Valeur']
    if df is None or df.empty or "Année" not in df.columns:
        return pd.DataFrame()
    df = df.rename(columns={"Valeur": label})
    df["Date"] = pd.to_datetime(df["Année"].astype(int).astype(str) + "-01-01")
    return df[["Date", label]]

def load_data_ext() -> pd.DataFrame:
    frames = []
    for label, code in WB_EXT_INDICATORS.items():
        try:
            s = _wb_to_df(label, code)
            if not s.empty:
                frames.append(s)
        except Exception:
            pass
    if not frames:
        return pd.DataFrame(columns=["Date"])
    df = frames[0]
    for t in frames[1:]:
        df = df.merge(t, on="Date", how="outer")
    return df.sort_values("Date")

df = load_data_ext()

# Rendu standard
build_module(df, "Secteur extérieur")

# Note flottante
floating_note()
