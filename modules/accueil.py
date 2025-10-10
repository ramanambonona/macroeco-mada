import streamlit as st
from datetime import datetime

# Helpers communs (désormais dans utils/)
try:
    from utils.common_ui import inject_css, floating_note
except ImportError:
    from common_ui import inject_css, floating_note  # fallback si exécuté à la racine

st.set_page_config(page_title="Accueil", page_icon="🏠", layout="wide")

# =========================
# Apparence / CSS / Palette
# =========================
inject_css("styles.css", palette=st.session_state.get("palette", "clair"))
with st.sidebar:
    st.subheader("🎨 Apparence")
    pal = st.selectbox(
        "Palette",
        ["clair", "creme", "ardoise-clair", "ardoise-sombre"],
        index=["clair", "creme", "ardoise-clair", "ardoise-sombre"].index(
            st.session_state.get("palette", "clair")
        ),
    )
    st.session_state.palette = pal
    inject_css("styles.css", palette=pal)  # ré-application immédiate

# =========
# En-tête
# =========
st.title("📚 Tableau de bord — Macroéconomie Madagascar")

with st.container():
    st.write(
        "Bienvenue. Choisissez un module dans la barre latérale : "
        "**Secteur réel**, **Finances publiques**, **Secteur monétaire**, **Secteur extérieur**."
    )
    st.info("Les sources de données restent celles de vos utilitaires : World Bank, INSTAT, FMI, BFM…")
    st.caption(f"Dernière mise à jour de l’app : {datetime.now():%d/%m/%Y}")

st.divider()

# ===================
# Grille de modules
# ===================
st.subheader("Accéder aux modules")
c1, c2 = st.columns(2)

with c1:
    # Chemins conformes à votre pages.toml (modules/...)
    st.page_link("modules/secteur_reel.py", label="📈 Secteur réel", help="Données WB, INSTAT…")
    st.markdown("- **Traitement** : période, transformations (log, YoY, MoM)  \n"
                "- **Visualisation** : lignes, barres, aires  \n"
                "- **Analyse** : décomposition, stats  \n"
                "- **Prévisions** : ARIMA/ETS/VAR/Prophet*, téléchargements CSV/Excel")

    st.page_link("modules/finances_publiques.py", label="💰 Finances publiques", help="FMI/SDMX (FM, GFS)")
    st.markdown("- Recettes, dépenses, solde, dette  \n"
                "- Menus : **Traitement / Visualisation / Analyse / Prévisions**  \n"
                "- Export CSV/Excel dans chaque onglet")

with c2:
    st.page_link("modules/secteur_monetaire.py", label="💳 Secteur monétaire", help="BFM, séries monétaires")
    st.markdown("- Taux de change, agrégats monétaires  \n"
                "- Menus standard + exports  \n"
                "- Outils de prévision incluant SNaive et Auto (min MAPE)")

    st.page_link("modules/secteur_exterieur.py", label="🌍 Secteur extérieur", help="WB, balance & flux externes")
    st.markdown("- Compte courant, flux IDE, réserves, échanges  \n"
                "- Menus standard + exports CSV/Excel")

st.divider()


# ============
# Crédit bas
# ============
floating_note()

