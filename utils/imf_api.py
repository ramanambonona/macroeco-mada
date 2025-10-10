import sdmx
import pandas as pd
import numpy as np

def get_imf_data(indicator_code: str, country_code: str = "MDG", start_year: int = 1991) -> pd.DataFrame:
    """
    Récupère les données d'un indicateur spécifique pour un pays donné
    à partir du dataset Fiscal Monitor (FM) du FMI via l'API SDMX.

    Args:
        indicator_code (str): Le code complet de l'indicateur SDMX (ex: "G1_S13_POGDP_PT.A").
        country_code (str): Code du pays (ex: "MDG" pour Madagascar).
        start_year (int): Année de début pour la récupération des données.

    Returns:
        pd.DataFrame: DataFrame contenant les colonnes 'Année' et 'Valeur'.
                      Retourne un DataFrame vide en cas d'erreur ou d'absence de données.
    """
    imf_client = sdmx.Client('IMF_DATA')
    
    # Construction de la clé SDMX basée sur le format confirmé : COUNTRY_CODE.INDICATOR_CODE
    # L'indicateur complet inclut déjà la fréquence (.A pour Annuel).
    sdmx_key = f"{country_code}.{indicator_code}"
    dataset_id = 'FM' # Le dataset Fiscal Monitor

    print(f"Tentative de récupération FMI (SDMX - FM) pour : {indicator_code} (Clé : {sdmx_key}, Année de début : {start_year})")
    
    try:
        # Récupération du message de données SDMX
        data_msg = imf_client.data(dataset_id, key=sdmx_key, params={'startPeriod': start_year})
        
        # Conversion du message SDMX en un DataFrame Pandas
        df = sdmx.to_pandas(data_msg)
        
        if df.empty:
            print(f"🚫 DataFrame vide pour {indicator_code} via SDMX. Aucune donnée trouvée ou toutes les valeurs sont nulles.")
            return pd.DataFrame()
        
        # --- Traitement du DataFrame sdmx pour obtenir les colonnes 'Année' et 'Valeur' ---
        
        # Le DataFrame SDMX a souvent un MultiIndex ou 'TIME_PERIOD' comme index.
        # Nous devons extraire la colonne d'année et la colonne de valeur.

        # Tente de réinitialiser l'index si 'TIME_PERIOD' est un niveau d'index
        if isinstance(df.index, pd.MultiIndex) and 'TIME_PERIOD' in df.index.names:
            df = df.reset_index(level='TIME_PERIOD')
        elif df.index.name == 'TIME_PERIOD': # Si 'TIME_PERIOD' est l'unique index
            df = df.reset_index()
        else:
            # Fallback si la structure de l'index n'est pas celle attendue.
            # Cela pourrait nécessiter un ajustement si les indicateurs ont des structures très variées.
            print(f"⚠️ Structure d'index inattendue pour {indicator_code}. Tentative de déduction de la colonne 'Année'.")
            df = df.reset_index(drop=False) # Conserve l'index comme colonne
            if 'TIME_PERIOD' in df.columns:
                df = df.rename(columns={'TIME_PERIOD': 'Année'})
            elif df.iloc[:,0].apply(lambda x: isinstance(x, int)).all(): # Si la première colonne est numérique (année)
                df = df.rename(columns={df.columns[0]: 'Année'})
            else:
                print(f"🚫 Impossible de trouver la colonne 'Année' pour l'indicateur {indicator_code}. Colonnes disponibles : {df.columns.tolist()}")
                return pd.DataFrame()

        # Renommer la colonne d'année
        if 'Année' not in df.columns:
             # Si 'Année' n'est pas directement nommée, essayer de trouver une colonne d'entiers
            year_candidate_cols = [col for col in df.columns if df[col].apply(lambda x: isinstance(x, (int, np.integer)) or (isinstance(x, str) and x.isdigit())).all()]
            if year_candidate_cols:
                df = df.rename(columns={year_candidate_cols[0]: 'Année'})
            else:
                print(f"🚫 Impossible de trouver la colonne 'Année' dans le DataFrame traité pour {indicator_code}.")
                return pd.DataFrame()

        # La colonne de valeur est généralement la première (ou unique) colonne numérique restante
        value_col = df.select_dtypes(include=np.number).columns
        if not value_col.empty:
            # S'il y a plusieurs colonnes numériques, prendre la première comme valeur.
            # Cela pourrait nécessiter une logique plus complexe si d'autres colonnes numériques sont présentes.
            df = df[['Année', value_col[0]]].rename(columns={value_col[0]: 'Valeur'})
        else:
            print(f"🚫 Aucune colonne numérique trouvée pour les valeurs dans {indicator_code} après traitement.")
            return pd.DataFrame()

        # S'assurer que la colonne 'Année' est de type entier
        df['Année'] = df['Année'].astype(int)
        
        # Filtrer par année de début si nécessaire
        df = df[df['Année'] >= start_year].copy() 
        
        if df.empty:
            print(f"🚫 DataFrame vide après traitement SDMX et filtrage pour l'indicateur: {indicator_code}. Soit toutes les données étaient nulles, soit hors période.")
            return pd.DataFrame()
        else:
            print(f"✅ Données récupérées pour l'indicateur: {indicator_code}. Nombre d'entrées: {len(df)}")
            df["Indicateur"] = indicator_code
            return df

    except sdmx.exceptions.HTTPError as e:
        print(f"❌ Erreur HTTP SDMX pour {indicator_code} (Dataset: {dataset_id}): {e}")
        return pd.DataFrame()
    except sdmx.exceptions.ResourceNotFound as e:
        print(f"❌ Ressource non trouvée SDMX pour {indicator_code} (Dataset: {dataset_id}): {e}. Vérifiez l'ID du dataset ou la clé de l'indicateur.")
        return pd.DataFrame()
    except Exception as e:
        print(f"Erreur inattendue SDMX pour {indicator_code}: {e}")
        return pd.DataFrame()

