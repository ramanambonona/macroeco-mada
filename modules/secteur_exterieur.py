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

WB_EXT_INDICATORS = {
    "Compte courant (% PIB)": "BN.CAB.XOKA.GD.ZS",
    "Flux IDE net (% PIB)": "BX.KLT.DINV.WD.GD.ZS",
    "Transferts courants (% PIB)": "BX.TRF.PWKR.DT.GD.ZS",
    "Réserves internationales (USD)": "FI.RES.TOTL.CD",
    "Balance biens & services (% PIB)": "NE.RSB.GNFS.ZS",
}

def _wb_to_df(label: str, code: str) -> pd.DataFrame:
    df = wb_get(code)  # ['Année','Valeur']
    if df is None or df.empty or "Année" not in df.columns:
        return pd.DataFrame()
    df = df.rename(columns={"Valeur": label})
    df["Date"] = pd.to_datetime(df["Année"].astype(int).astype(str) + "-01-01")
    return df[["Date", label]]

def _load_data_ext() -> pd.DataFrame:
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

    df = _load_data_ext()
    build_module(df, "Secteur Extérieur")
    floating_note()
