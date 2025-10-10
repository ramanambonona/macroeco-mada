# extract_data_instat.py (version corrigée)

import streamlit as st
import pandas as pd
import requests
import io

def extract_data_instat():
    url = "https://www.instat.mg/documents/upload/main/ComptesNationauxRebases_2007_2021(Provisoires)_Nov2022.xlsx"
    
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        excel_file = pd.ExcelFile(io.BytesIO(response.content))
        st.success("Données INSTAT récupérées avec succès !")
    except Exception as e:
        st.error(f"Erreur de téléchargement : {str(e)}")
        return pd.DataFrame()

    # Fonction helper pour lire et nettoyer une sheet
    def read_and_clean_sheet(sheet_name, years):
        df = pd.read_excel(excel_file, sheet_name=sheet_name, skiprows=11, header=None)
        if df.empty:
            return pd.DataFrame()
        
        # Supprimer la colonne vide (généralement colonne 1)
        if len(df.columns) > 1 and df.iloc[:, 1].isna().all():
            df = df.drop(columns=1)
        
        # Définir colonnes : première = 'Libellé', reste = années
        df.columns = ['Libellé'] + [str(year) for year in years]
        
        # Nettoyer Libellé : strip espaces
        df['Libellé'] = df['Libellé'].astype(str).str.strip()
        
        # Supprimer lignes vides ou NaN en Libellé
        df = df[df['Libellé'].notna() & (df['Libellé'] != 'nan')]
        
        # Melt pour long format
        df = df.melt(id_vars=['Libellé'], var_name='Année', value_name='Valeur')
        df['Année'] = pd.to_numeric(df['Année'], errors='coerce')
        
        # Pivot pour années en index, Libellé en colonnes
        df = df.pivot(index='Année', columns='Libellé', values='Valeur').reset_index()
        
        # Conversion numérique
        for col in df.columns[1:]:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.').str.replace(' ', ''), errors='coerce')
        
        return df

    # Extraire sheet principale (prix constants)
    sheet_name = '1. ERE_Constant'
    years = range(2007, 2022)  # 2007-2021
    df = read_and_clean_sheet(sheet_name, years)
    if df.empty:
        st.warning("Aucune donnée extraite de la sheet principale.")
        return pd.DataFrame()
    
    # Renommer colonnes pour matcher indicateurs
    rename_map = {
        'Secteur Primaire': 'Secteur Primaire',
        'Secteur Secondaire': 'Secteur Secondaire',
        'Secteur Tertiaire': 'Secteur Tertiaire',
        'SIFIM': 'SIFIM',
        'PIB aux prix de base': 'PIB aux prix de base',
        'Impôts sur les produits': 'Impôts sur les produits',
        'PIB aux prix d\'acquisition': 'PIB',
        'Importations nettes de biens et services': 'Importations nettes',
        'Importations': 'Importations',
        'Exportations': 'Exportations',
        'Ressources disponibles totales': 'Ressources totales',
        'Dépenses de consommation finale': 'Consommation',
        'Dépenses de consommation finale des Administrations Publiques et des ISBLSM': 'Dépenses publiques',
        'Dépenses de consommation finale des Ménages': 'Consommation ménages',
        'Formation brute de capital': 'Investissement',
        'Formation brute de capital fixe': 'Investissement fixe',
        'Variation des stocks': 'Variation stocks'
    }
    df = df.rename(columns=rename_map)
    
    # Extraire sheet croissance
    growth_sheet = '3. ERE_Croissance'
    growth_years = range(2008, 2022)  # Croissance commence en 2008
    growth_df = read_and_clean_sheet(growth_sheet, growth_years)
    if not growth_df.empty:
        # Ajouter colonnes de croissance à df principal
        for col in growth_df.columns[1:]:
            new_col = f"Croissance {col} (%)"
            df = df.merge(growth_df[['Année', col]].rename(columns={col: new_col}), on='Année', how='left')
    
    # Filtrer années valides
    df = df[df['Année'].between(2007, 2021)]
    
    return df