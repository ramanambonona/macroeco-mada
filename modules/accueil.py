import streamlit as st
from datetime import datetime

# Helpers communs
try:
    from utils.common_ui import inject_css, floating_note
except ImportError:
    from common_ui import inject_css, floating_note  # fallback local

def app():
    # Apparence / CSS / palette
    inject_css("styles.css", palette=st.session_state.get("palette", "clair"))
    with st.sidebar:
        with st.expander("🎨 Apparence", expanded=False):
            pal = st.selectbox(
                "Palette",
                ["clair", "creme", "ardoise-clair", "ardoise-sombre"],
                index=["clair","creme","ardoise-clair","ardoise-sombre"].index(
                    st.session_state.get("palette","clair")
                ),
            )
            st.session_state.palette = pal
            inject_css("styles.css", palette=pal)

    # Valeur par défaut pour la navigation (clé utilisée par main.py)
    if "nav_choice" not in st.session_state:
        st.session_state["nav_choice"] = "🏠 Accueil"

    st.title("📚 Tableau de bord — Macroéconomie Madagascar")
    st.write(
        "Bienvenue. Choisissez un module dans la barre latérale ou via les boutons ci-dessous : "
        "**Secteur réel**, **Finances publiques**, **Secteur monétaire**, **Secteur extérieur**."
    )
    st.info("Les sources de données restent celles de vos utilitaires : World Bank, INSTAT, FMI (SDMX), BFM…")
    st.caption(f"Dernière mise à jour de l’app : {datetime.now():%d/%m/%Y}")

    st.divider()
    st.subheader("Accéder aux modules")

    def _goto(menu_label: str):
        st.session_state["nav_choice"] = menu_label  # doit correspondre EXACTEMENT aux clés de MENU dans main.py
        st.rerun()

    c1, c2 = st.columns(2)
    with c1:
        st.button("📈 Secteur Réel", use_container_width=True, on_click=_goto, args=("📊 Secteur Réel",))
        st.markdown("- Traitement : filtre période, transformations (log, YoY, MoM)\n"
                    "- Visualisation : lignes, barres, aires\n"
                    "- Analyse : décomposition, stats\n"
                    "- Prévisions : ARIMA/ETS/VAR/Prophet*, export CSV/Excel")

        st.button("💰 Finances Publiques", use_container_width=True, on_click=_goto, args=("💰 Finances Publiques",))
        st.markdown("- Recettes, dépenses, solde, dette\n"
                    "- Menus : Traitement / Visualisation / Analyse / Prévisions\n"
                    "- Export CSV/Excel partout")

    with c2:
        st.button("💳 Secteur Monétaire", use_container_width=True, on_click=_goto, args=("💳 Secteur Monétaire",))
        st.markdown("- Taux de change (BFM), agrégats\n"
                    "- Menus standard + exports\n"
                    "- Modèles SNaive et Auto (min MAPE)")

        st.button("🌍 Secteur Extérieur", use_container_width=True, on_click=_goto, args=("🌍 Secteur Extérieur",))
        st.markdown("- Compte courant, IDE, réserves, échanges (WB)\n"
                    "- Menus standard + exports CSV/Excel")

    st.divider()
    with st.expander("ℹ️ Aide rapide"):
        st.markdown(
            "- Chaque module propose **Traitement → Visualisation → Analyse → Prévisions** avec **téléchargements**."
        )

    floating_note()
