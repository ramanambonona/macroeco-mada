import streamlit as st
import pandas as pd

# UI et pipeline standard
try:
    from utils.common_ui import inject_css, build_module, floating_note, download_box
except ImportError:
    from common_ui import inject_css, build_module, floating_note, download_box

# Sources
try:
    from utils.imf_api import get_imf_data
except ImportError:
    from imf_api import get_imf_data

try:
    from utils.excel_loader import read_excel_any
except ImportError:
    from excel_loader import read_excel_any

# ————— Indicateurs IMF (exemples GFS/GFSR) —————
INDICATEURS_IMF = {
    "Recettes publiques (% PIB)": "G1_S13_POGDP_PT.A",
    "Dépenses publiques (% PIB)": "G2M_S13_POGDP_PT.A",
    "Dette brute (% PIB)": "G63G_S13_POGDP_PT.A",
    "Solde budgétaire (% PIB)": "GNLB_S13_POGDP_PT.A",
    "Solde primaire (% PIB)": "GPB_S13_POGDP_PT.A",
}

# -------- Helpers internes --------
def _imf_to_df(label: str, code: str) -> pd.DataFrame:
    df = get_imf_data(code, country_code="MDG", start_year=1991)  # attendu ['Année','Valeur']
    if df is None or df.empty or "Année" not in df.columns:
        return pd.DataFrame()
    out = df[["Année","Valeur"]].copy()
    out[label] = pd.to_numeric(out["Valeur"], errors="coerce")
    out["Date"] = pd.to_datetime(out["Année"].astype(int).astype(str) + "-01-01")
    return out[["Date", label]]

def _standardize_excel(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=["Date"])
    df = df.copy()
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    elif "Année" in df.columns:
        df["Date"] = pd.to_datetime(df["Année"].astype(int).astype(str) + "-01-01", errors="coerce")
    else:
        first = df.columns[0]
        try:
            test = pd.to_datetime(df[first], errors="coerce")
            if test.notna().sum() >= max(3, int(0.5 * len(df))):
                df["Date"] = test
            else:
                test2 = pd.to_datetime(df[first].astype(int).astype(str) + "-01-01", errors="coerce")
                df["Date"] = test2
        except Exception:
            df["Date"] = pd.NaT
    if df["Date"].isna().all():
        return pd.DataFrame(columns=["Date"])
    for c in [c for c in df.columns if c != "Date"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df[["Date"] + [c for c in df.columns if c != "Date"]].dropna(subset=["Date"]).sort_values("Date")

def _build_from_imf():
    st.subheader("⚙️ Paramètres FMI (IMF SDMX)")
    selected = st.multiselect(
        "Choisir les indicateurs",
        options=list(INDICATEURS_IMF.keys()),
        default=list(INDICATEURS_IMF.keys())[:3],
    )
    if not selected:
        st.info("Sélectionnez au moins un indicateur.")
        return pd.DataFrame(columns=["Date"])
    frames = []
    with st.spinner("Téléchargement des séries IMF…"):
        for label in selected:
            code = INDICATEURS_IMF[label]
            try:
                s = _imf_to_df(label, code)
                if not s.empty:
                    frames.append(s)
            except Exception:
                pass
    if not frames:
        st.warning("Aucune série IMF n’a pu être chargée.")
        return pd.DataFrame(columns=["Date"])
    df = frames[0]
    for t in frames[1:]:
        df = df.merge(t, on="Date", how="outer")
    df = df.sort_values("Date")
    download_box(df, "finances_publiques_imf", key_prefix="imf_fp")
    return df

def _build_from_mef():
    st.subheader("🏛️ MEF (à définir ultérieurement)")
    st.info(
        "Le connecteur MEF sera ajouté ultérieurement (API/CSV officiels). "
        "Pour l’instant, utilisez l’option « Excel (upload) » ci-dessous si vous avez un fichier MEF."
    )
    return pd.DataFrame(columns=["Date"])

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
    download_box(std, "finances_publiques_excel", key_prefix="xlsx_fp")
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

    st.title("💰 Finances Publiques")

    source = st.radio("Source des données", ["FMI", "MEF (à venir)", "Excel (upload)"], horizontal=True)

    if source == "FMI":
        df = _build_from_imf()
    elif source == "MEF (à venir)":
        df = _build_from_mef()
    else:
        df = _build_from_excel()

    # Rendu standard (Traitement / Visualisation / Analyse / Prévisions)
    build_module(df, "Finances Publiques")

    floating_note()
