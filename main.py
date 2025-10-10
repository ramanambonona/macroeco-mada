import os, sys
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import streamlit as st
from modules.accueil import app as accueil
from modules.secteur_reel import app as secteur_reel
from modules.finances_publiques import app as finances_publiques
from modules.secteur_monetaire import app as secteur_monetaire
from modules.secteur_exterieur import app as secteur_exterieur

st.set_page_config(
    page_title="Économie de Madagascar",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

MENU = {
    "🏠 Accueil": accueil,
    "📊 Secteur Réel": secteur_reel,
    "💰 Finances Publiques": finances_publiques,
    "💳 Secteur Monétaire": secteur_monetaire,
    "🌍 Secteur Extérieur": secteur_exterieur,
}

with st.sidebar:
    st.title("📌 Menu principal")
    if "nav_choice" not in st.session_state:
        st.session_state["nav_choice"] = "🏠 Accueil"
    choix = st.radio("Navigation", list(MENU.keys()), key="nav_choice")

# Exécuter la page choisie
MENU[choix]()
