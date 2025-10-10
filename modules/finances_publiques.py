import streamlit as st
import pandas as pd

# Helpers communs
try:
    from utils.common_ui import inject_css, build_module, floating_note
except ImportError:
    from common_ui import inject_css, build_module, floating_note

# FMI SDMX
try:
    from utils.imf_api import get_imf_data
except ImportError:
    from imf_api import get_imf_data

st.set_page_config(page_title="Finances publiques", page_icon="💰", layout="wide")

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

# --- CHARGEMENT DONNÉES (FMI — vos codes) ---
INDICATEURS_IMF = {
    "Recettes publiques (% PIB)": "G1_S13_POGDP_PT.A",
    "Dépenses publiques (% PIB)": "G2M_S13_POGDP_PT.A",
    "Dette brute (% PIB)": "G63G_S13_POGDP_PT.A",
    "Solde budgétaire (% PIB)": "GNLB_S13_POGDP_PT.A",
    "Solde primaire (% PIB)": "GPB_S13_POGDP_PT.A",
}

def _imf_to_df(label: str, code: str) -> pd.DataFrame:
    df = get_imf_data(code, country_code="MDG", start_year=1991)
    # attendu: colonnes ['Année','Valeur']
    if df is None or df.empty or "Année" not in df.columns:
        return pd.DataFrame()
    out = df[["Année", "Valeur"]].copy()
    out[label] = pd.to_numeric(out["Valeur"], errors="coerce")
    out["Date"] = pd.to_datetime(out["Année"].astype(int).astype(str) + "-01-01")
    return out[["Date", label]]

def load_data_fp() -> pd.DataFrame:
    frames = []
    for label, code in INDICATEURS_IMF.items():
        try:
            s = _imf_to_df(label, code)
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

df = load_data_fp()

# Rendu standard
build_module(df, "Finances publiques")

# Note flottante
floating_note()
