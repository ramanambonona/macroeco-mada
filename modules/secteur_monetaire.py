import streamlit as st
import pandas as pd
from datetime import date, timedelta

# Helpers communs
try:
    from utils.common_ui import inject_css, build_module, floating_note
except ImportError:
    from common_ui import inject_css, build_module, floating_note

# BFM scraper
try:
    from utils.bfm_scraper import get_taux_change
except ImportError:
    from bfm_scraper import get_taux_change

st.set_page_config(page_title="Secteur monétaire", page_icon="💳", layout="wide")

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

# --- CHARGEMENT DONNÉES (BFM, etc.) ---
def load_data_monetary() -> pd.DataFrame:
    end = date.today()
    start = end - timedelta(days=5 * 365)

    frames = []

    # Taux USD/MGA
    try:
        usd = get_taux_change(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"), "USD")
        if isinstance(usd, pd.DataFrame) and not usd.empty and "Date" in usd.columns:
            val_col = "Taux" if "Taux" in usd.columns else [c for c in usd.columns if c != "Date"][0]
            usd = usd.rename(columns={val_col: "Taux USD/MGA"})
            frames.append(usd[["Date", "Taux USD/MGA"]])
    except Exception:
        pass

    # Taux EUR/MGA
    try:
        eur = get_taux_change(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"), "EUR")
        if isinstance(eur, pd.DataFrame) and not eur.empty and "Date" in eur.columns:
            val_col = "Taux" if "Taux" in eur.columns else [c for c in eur.columns if c != "Date"][0]
            eur = eur.rename(columns={val_col: "Taux EUR/MGA"})
            frames.append(eur[["Date", "Taux EUR/MGA"]])
    except Exception:
        pass

    if not frames:
        return pd.DataFrame(columns=["Date"])

    df = frames[0]
    for t in frames[1:]:
        df = df.merge(t, on="Date", how="outer")

    return df.sort_values("Date")

df = load_data_monetary()

# Rendu standard
build_module(df, "Secteur monétaire")

# Note flottante
floating_note()
