import streamlit as st
from datetime import datetime

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

    if "nav_choice" not in st.session_state:
        st.session_state["nav_choice"] = "🏠 Accueil"

    st.title("📚 Tableau de bord — Macroéconomie Madagascar")
    st.write(
        "Bienvenue. Utilisez le menu à gauche ou les raccourcis ci-dessous pour accéder aux modules : "
        "**Secteur réel**, **Finances publiques**, **Secteur monétaire**, **Secteur extérieur**."
    )
    st.info("Sources : World Bank, INSTAT, FMI, BFM.")
    st.caption(f"Dernière mise à jour de l’app : {datetime.now():%d/%m/%Y}")

    st.divider()
    st.subheader("Accéder aux modules")

    def _goto(label):
        st.session_state["nav_choice"] = label
        st.rerun()

    c1, c2 = st.columns(2)
    with c1:
        st.button("📊 Secteur Réel", use_container_width=True, on_click=_goto, args=("📊 Secteur Réel",))
        st.button("💰 Finances Publiques", use_container_width=True, on_click=_goto, args=("💰 Finances Publiques",))
    with c2:
        st.button("💳 Secteur Monétaire", use_container_width=True, on_click=_goto, args=("💳 Secteur Monétaire",))
        st.button("🌍 Secteur Extérieur", use_container_width=True, on_click=_goto, args=("🌍 Secteur Extérieur",))

    st.divider()
    with st.expander("ℹ️ Aide rapide"):
        st.markdown(
            "- Chaque module propose **Traitement → Visualisation → Analyse → Prévisions** avec **téléchargements**.\n"
        )

    floating_note()

