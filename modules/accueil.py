import streamlit as st

def app():
    st.title("🏠 Bienvenue sur l'application Économie de Madagascar")

    st.markdown("""
    Cette application vous permet de visualiser et d'analyser en temps réel les données économiques de Madagascar.

    ## Contenu de l'application :
    - 📊 **Secteur Réel** : PIB, Investissements, Commerce extérieur.
    - 💰 **Finances Publiques** : Déficit, Dette/PIB, soutenabilité budgétaire.
    - 💳 **Secteur Monétaire** : Inflation, agrégats monétaires.
    - 🌍 **Secteur Extérieur** : Balance des paiements.

    Utilisez le menu à gauche pour naviguer entre les différentes sections.
    """)

    st.image("https://www.worldbank.org/content/dam/photos/780x439/2023/jul/MDG.jpg", caption="Madagascar - Source : Banque Mondiale")
