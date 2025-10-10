import streamlit as st
import pandas as pd

# UI et pipeline standard
try:
    from utils.common_ui import inject_css, build_module, floating_note, download_box
except ImportError:
    from common_ui import inject_css, build_module, floating_note, download_box

# Sources
try:
    from utils.api_worldbank import get_data as wb_get
except ImportError:
    from api_worldbank import get_data as wb_get

try:
    from utils.extract_data_instat import extract_data_instat as instat_get
except ImportError:
    from extract_data_instat import extract_data_instat as instat_get

try:
    from utils.excel_loader import read_excel_any
except ImportError:
    from excel_loader import read_excel_any

# ————— Indicateurs World Bank (par défaut) —————
WB_INDICATORS = {
    "PIB courant (USD)": "NY.GDP.MKTP.CD",
    "PIB réel – croissance (%)": "NY.GDP.MKTP.KD.ZG",
    "Inflation IPC (%)": "FP.CPI.TOTL.ZG",
    "Population (total)": "SP.POP.TOTL",
}

# -------- Helpers internes --------
def _wb_series_to_df(label: str, code: str) -> pd.DataFrame:
    df = wb_get(code)  # attendu ['Année','Valeur']
    if df is None or df.empty or "Année" not in df.columns:
        return pd.DataFrame()
    out = df.rename(columns={"Valeur": label}).copy()
    out["Date"] = pd.to_datetime(out["Année"].astype(int).astype(str) + "-01-01")
    return out[["Date", label]].sort_values("Date")

def _standardize_excel(df: pd.DataFrame) -> pd.DataFrame:
    """Essaie d'obtenir une colonne Date (à partir de 'Date' ou 'Année' ou 1ère colonne)"""
    if df is None or df.empty:
        return pd.DataFrame(columns=["Date"])
    df = df.copy()

    # Priorité à une vraie colonne Date
    if "Date" in df.columns:
        try:
            df["Date"] = pd.to_datetime(df["Date"])
        except Exception:
            pass
    elif "Année" in df.columns:
        try:
            df["Date"] = pd.to_datetime(df["Année"].astype(int).astype(str) + "-01-01")
        except Exception:
            df["Date"] = pd.to_datetime(df["Année"], errors="coerce")
    else:
        # Tente 1ère colonne
        first = df.columns[0]
        try:
            test = pd.to_datetime(df[first], errors="coerce")
            if test.notna().sum() >= max(3, int(0.5 * len(df))):
                df["Date"] = test
            else:
                # si ce sont des années
                test2 = pd.to_datetime(df[first].astype(int).astype(str) + "-01-01", errors="coerce")
                df["Date"] = test2
        except Exception:
            df["Date"] = pd.NaT

    # Nettoyage
    if df["Date"].isna().all():
        return pd.DataFrame(columns=["Date"])
    # garde Date + num
    num_cols = [c for c in df.columns if c != "Date"]
    for c in num_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    out = df[["Date"] + num_cols].dropna(subset=["Date"]).sort_values("Date")
    return out

def _build_from_worldbank():
    st.subheader("⚙️ Paramètres World Bank")
    selected = st.multiselect(
        "Choisir les indicateurs",
        options=list(WB_INDICATORS.keys()),
        default=list(WB_INDICATORS.keys())[:2],
    )
    if not selected:
        st.info("Sélectionnez au moins un indicateur.")
        return pd.DataFrame(columns=["Date"])
    frames = []
    with st.spinner("Téléchargement des séries World Bank…"):
        for label in selected:
            code = WB_INDICATORS[label]
            try:
                w = _wb_series_to_df(label, code)
                if not w.empty:
                    frames.append(w)
            except Exception:
                pass
    if not frames:
        st.warning("Aucune série WB n’a pu être chargée.")
        return pd.DataFrame(columns=["Date"])
    df = frames[0]
    for t in frames[1:]:
        df = df.merge(t, on="Date", how="outer")
    df = df.sort_values("Date")
    download_box(df, "secteur_reel_worldbank", key_prefix="wb_reel")
    return df

def _build_from_instat():
    st.subheader("📗 INSTAT (données historiques)")
    st.caption("Chargement depuis votre fichier local défini dans `utils/extract_data_instat.py` (par défaut `data/instat.xlsx`).")
    with st.spinner("Chargement INSTAT…"):
        df = instat_get()
    if not isinstance(df, pd.DataFrame) or df.empty:
        st.warning("Aucune donnée INSTAT trouvée (vérifiez `data/instat.xlsx`).")
        return pd.DataFrame(columns=["Date"])
    std = _standardize_excel(df)
    if std.empty:
        st.warning("Le fichier INSTAT n’a pas de colonne 'Date'/'Année' exploitable.")
        return pd.DataFrame(columns=["Date"])
    download_box(std, "secteur_reel_instat", key_prefix="instat_reel")
    return std

def _build_from_excel():
    st.subheader("📥 Import Excel/CSV")
    up = st.file_uploader("Déposez un fichier", type=["xlsx","xls","csv"])
    if not up:
        st.info("Veuillez importer un fichier pour continuer.")
        return pd.DataFrame(columns=["Date"])
    try:
        df = read_excel_any(up)
    except Exception as e:
        st.error(f"Erreur de lecture : {e}")
        return pd.DataFrame(columns=["Date"])
    std = _standardize_excel(df)
    if std.empty:
        st.warning("Impossible d’identifier une colonne 'Date'/'Année' ou des dates valides.")
        return pd.DataFrame(columns=["Date"])
    download_box(std, "secteur_reel_excel", key_prefix="xlsx_reel")
    return std

# -------- Page --------
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

    st.title("📊 Secteur Réel")

    source = st.radio("Source des données", ["Banque mondiale", "INSTAT", "Excel (upload)"], horizontal=True)

    if source == "Banque mondiale":
        df = _build_from_worldbank()
    elif source == "INSTAT":
        df = _build_from_instat()
    else:
        df = _build_from_excel()

    # Rendu standard (Traitement / Visualisation / Analyse / Prévisions)
    build_module(df, "Secteur Réel")

    floating_note()
