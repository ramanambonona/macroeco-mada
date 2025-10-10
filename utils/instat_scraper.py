# utils/instat_scraper.py

from playwright.sync_api import sync_playwright
import pandas as pd
from io import StringIO
from bs4 import BeautifulSoup
import streamlit as st

def load_data(labels, from_year, to_year, headless=True):
    """Fonction améliorée pour extraire les données via Playwright."""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            page = browser.new_page()
            page.goto("https://instat.mg/statistiques/bases-de-donnees/comptes-nationaux")
            page.wait_for_load_state("networkidle")
            
            # Cocher labels spécifiques (adaptez sélecteurs ; utilisez XPath si mieux)
            for label in labels:
                page.check(f'//label[contains(text(), "{label}")]/preceding-sibling::input')  # Exemple XPath
            
            # Sélectionner périodes (adaptez names après inspection)
            page.select_option('select[name="periode_debut"]', from_year)
            page.select_option('select[name="periode_fin"]', to_year)
            
            # Cliquer bouton
            page.click('input[value="Actualiser le tableau"]')  # Ou button[type="submit"]
            page.wait_for_selector("table", timeout=10000)
            
            # Extraire HTML et parser avec BeautifulSoup + pandas
            html = page.inner_html("table")
            soup = BeautifulSoup(html, 'html.parser')
            df = pd.read_html(StringIO(str(soup)))[0]
            
            # Nettoyage basique
            df.columns = df.columns.str.strip()
            numeric_cols = df.columns[1:]  # Suppose première colonne = 'Libellé'
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col].str.replace(' ', ''), errors='coerce')
            
            browser.close()
            return df
    except Exception as e:
        st.error(f"Erreur lors du scraping : {str(e)}")
        return pd.DataFrame()