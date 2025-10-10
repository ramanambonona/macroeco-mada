import streamlit as st
import pandas as pd

# Helpers communs
try:
    from utils.common_ui import inject_css, build_module, floating_note
except ImportError:
    from common_ui import inject_css, build_module, floating_note

# Utilitaires de données (inchangés, maintenant préférentiellement depuis utils/)
try:
    from utils.api_worldbank import get_data as wb_get
except ImportError:
    from api_worldbank import get_data as wb_get

try:
    from utils.extract_data_instat import extract_data_instat as instat_get
except ImportError:
    from extract_data_instat import extract_data_instat as instat_get

st.set_page_config(page_title="Secteur réel", page_icon="📈", layout="wide")

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

# --- CHARGEMENT DONNÉES (sources inchangées) ---
WB_INDICATORS = {
    "PIB courant (USD)": "NY.GDP.MKTP.CD",
    "PIB réel – croissance (%)": "NY.GDP.MKTP.KD.ZG",
    "Inflation IPC (%)": "FP.CPI.TOTL.ZG",
    "Population (total)": "SP.POP.TOTL",
}

def _wb_series_to_df(label: str, code: str) -> pd.DataFrame:
    df = wb_get(code)  # renvoie colonnes ['Année','Valeur']
    if df is None or df.empty or "Année" not in df.columns:
        return pd.DataFrame()
    df = df.rename(columns={"Valeur": label})
    df["Date"] = pd.to_datetime(df["Année"].astype(int).astype(str) + "-01-01")
    return df[["Date", label]].sort_values("Date")

def load_data_reel() -> pd.DataFrame:
    frames = []
    # 1) World Bank
    for label, code in WB_INDICATORS.items():
        try:
            w = _wb_series_to_df(label, code)
            if not w.empty:
                frames.append(w)
        except Exception:
            pass

    # 2) INSTAT (si disponible)
    try:
        df_instat = instat_get()  # renvoie colonnes 'Année' + indicateurs
        if isinstance(df_instat, pd.DataFrame) and not df_instat.empty and "Année" in df_instat.columns:
            inst = df_instat.copy()
            inst["Date"] = pd.to_datetime(inst["Année"].astype(int).astype(str) + "-01-01")
            inst = inst.drop(columns=["Année"])
            cols = ["Date"] + [c for c in inst.columns if c != "Date"]
            inst = inst[cols]
            frames.append(inst)
    except Exception:
        pass

    if not frames:
        return pd.DataFrame(columns=["Date"])

    df = frames[0]
    for t in frames[1:]:
        df = df.merge(t, on="Date", how="outer")

    return df.sort_values("Date")

df = load_data_reel()

# Rendu standard (Traitement / Visualisation / Analyse / Prévisions + downloads)
build_module(df, "Secteur réel")

# Note flottante
floating_note()
