import streamlit as st
import pandas as pd

try:
    from utils.common_ui import inject_css, build_module, floating_note
except ImportError:
    from common_ui import inject_css, build_module, floating_note

try:
    from utils.api_worldbank import get_data as wb_get
except ImportError:
    from api_worldbank import get_data as wb_get

try:
    from utils.extract_data_instat import extract_data_instat as instat_get
except ImportError:
    from extract_data_instat import extract_data_instat as instat_get

WB_INDICATORS = {
    "PIB courant (USD)": "NY.GDP.MKTP.CD",
    "PIB réel – croissance (%)": "NY.GDP.MKTP.KD.ZG",
    "Inflation IPC (%)": "FP.CPI.TOTL.ZG",
    "Population (total)": "SP.POP.TOTL",
}

def _wb_series_to_df(label: str, code: str) -> pd.DataFrame:
    df = wb_get(code)  # attendu ['Année','Valeur']
    if df is None or df.empty or "Année" not in df.columns:
        return pd.DataFrame()
    out = df.rename(columns={"Valeur": label}).copy()
    out["Date"] = pd.to_datetime(out["Année"].astype(int).astype(str) + "-01-01")
    return out[["Date", label]].sort_values("Date")

def _load_data_reel() -> pd.DataFrame:
    frames = []
    # World Bank
    for label, code in WB_INDICATORS.items():
        try:
            w = _wb_series_to_df(label, code)
            if not w.empty:
                frames.append(w)
        except Exception:
            pass
    # INSTAT (si dispo)
    try:
        df_instat = instat_get()
        if isinstance(df_instat, pd.DataFrame) and not df_instat.empty and "Année" in df_instat.columns:
            inst = df_instat.copy()
            inst["Date"] = pd.to_datetime(inst["Année"].astype(int).astype(str) + "-01-01")
            inst = inst.drop(columns=["Année"])
            inst = inst[["Date"] + [c for c in inst.columns if c != "Date"]]
            frames.append(inst)
    except Exception:
        pass
    if not frames:
        return pd.DataFrame(columns=["Date"])
    df = frames[0]
    for t in frames[1:]:
        df = df.merge(t, on="Date", how="outer")
    return df.sort_values("Date")

def app():
    inject_css("styles.css", palette=st.session_state.get("palette", "clair"))
    with st.sidebar:
        with st.expander("🎨 Apparence", expanded=False):
            pal = st.selectbox(
                "Palette", ["clair","creme","ardoise-clair","ardoise-sombre"],
                index=["clair","creme","ardoise-clair","ardoise-sombre"].index(st.session_state.get("palette","clair")),
            )
            st.session_state.palette = pal
            inject_css("styles.css", palette=pal)

    df = _load_data_reel()
    build_module(df, "Secteur Réel")
    floating_note()
