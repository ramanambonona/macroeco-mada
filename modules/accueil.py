import streamlit as st
from pathlib import Path

def load_css(path: str = "styles.css"):
    p = Path(path)
    if p.exists():
        st.markdown(f"<style>{p.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

load_css()  

def app():
    st.title("🏠 Bienvenue sur l'application Économie de Madagascar")

    st.markdown("""
    Cette application vous permet de visualiser et d'analyser en temps réel les données économiques de Madagascar.

    ## Contenu de l'application :
    - 📊 **Secteur Réel** : PIB, Investissements, Consommation, Dépenses publiques, Commerce extérieur.
    - 💰 **Finances Publiques** : Déficit, Dette/PIB, soutenabilité budgétaire.
    - 💳 **Secteur Monétaire** : Inflation, agrégats monétaires.
    - 🌍 **Secteur Extérieur** : Balance des paiements.

    Utilisez le menu à gauche pour naviguer entre les différentes sections.
    """)

