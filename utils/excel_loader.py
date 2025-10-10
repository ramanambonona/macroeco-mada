import pandas as pd
import streamlit as st

def load_excel():
    uploaded_file = st.file_uploader("Importer votre fichier Excel (.xlsx)", type=["xlsx"])
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        return df
    return None
