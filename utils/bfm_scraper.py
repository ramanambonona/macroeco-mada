import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from requests_toolbelt import MultipartEncoder
import random
import string
from pdfminer.high_level import extract_text
import io
import re

def get_taux_change(start_date, end_date, devise):
    """Récupère l'historique des taux de change (marché des changes)"""
    url = 'https://www.banky-foibe.mg/admin/wp-json/bfm/cours_mid_en_ar_filter'
    current_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    
    data = []

    with st.spinner("🔄 Téléchargement des taux de change..."):
        while current_date <= end_date:
            jour = f"{current_date.day:02d}"
            mois = f"{current_date.month:02d}"
            annee = f"{current_date.year}"
            date_bfm = f"{annee}/{mois}/{jour}"
            date_format = f"{annee}-{mois}-{jour}"

            fields = {
                'dateFilterDebut': date_bfm,
                'dateFilterFin': date_bfm,
                'filterData': devise
            }

            boundary = '----WebKitFormBoundary' + ''.join(random.sample(string.ascii_letters + string.digits, 16))
            m = MultipartEncoder(fields=fields, boundary=boundary)

            headers = {
                "Accept": "application/json, text/plain, */*",
                "Content-Type": m.content_type,
                "User-Agent": "Mozilla/5.0"
            }

            try:
                with requests.Session() as s:
                    response = s.post(url, headers=headers, data=m, timeout=10)
                    if response.status_code == 200:
                        r_json = response.json()
                        try:
                            taux = float(r_json["data"]["data"]["coursMid"][f"{annee}-{mois}-{jour}"].replace(",", "."))
                            data.append({
                                'Date': pd.to_datetime(f"{annee}-{mois}-{jour}"),
                                'Taux': taux
                            })
                        except Exception:
                            pass
            except Exception:
                pass

            current_date += timedelta(days=1)
    
    df = pd.DataFrame(data)
    return df

def get_taux_directeur():
    """Récupère l'historique du taux directeur"""
    try:
        url = "https://www.banky-foibe.mg/taux_evolution-du-taux-directeur-de-la-banque-centrale"
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        table = soup.find('div', {'class': 'content-article'}).find('table')
        rows = table.find_all('tr')[1:]

        data = []
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 2:
                data.append({
                    'Date': pd.to_datetime(cols[0].text.strip(), format='%d/%m/%Y'),
                    'Taux': float(cols[1].text.strip().replace(',', '.'))
                })

        return pd.DataFrame(data)

    except Exception as e:
        st.error(f"Erreur lors du scraping taux directeur : {str(e)}")
        return pd.DataFrame()

def get_agregats_monetaires():
    """Récupère les agrégats monétaires à partir d'un PDF"""
    try:
        pdf_url = "https://www.banky-foibe.mg/pdf_monnaie-et-credit"
        response = requests.get(pdf_url, stream=True)
        text = extract_text(io.BytesIO(response.content))

        patterns = {
            'M1': r"M1\s+([\d\s,]+)",
            'M2': r"M2\s+([\d\s,]+)",
            'M3': r"M3\s+([\d\s,]+)",
            'Date': r"au\s(\d{1,2}/\d{1,2}/\d{4})"
        }

        data = {}
        for key, pattern in patterns.items():
            match = re.search(pattern, text)
            if match:
                value = match.group(1).replace(' ', '').replace(',', '.')
                if key == 'Date':
                    data[key] = datetime.strptime(value, '%d/%m/%Y')
                else:
                    data[key] = float(value)
        
        df = pd.DataFrame([data])
        df = df.rename(columns={
            'M1': 'M1 (Liquidités)',
            'M2': 'M2 (Masse monétaire)',
            'M3': 'M3 (Quasi-monnaie)'
        })
        return df

    except Exception as e:
        st.error(f"Erreur lecture agrégats monétaires : {str(e)}")
        return pd.DataFrame()

def get_reserves_obligatoires():
    """Récupère les historiques des réserves obligatoires"""
    try:
        url = "https://www.banky-foibe.mg/taux_coefficient-de-reserve-obligatoire"
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        table = soup.find('div', {'class': 'content-article'}).find('table')
        rows = table.find_all('tr')[1:]

        data = []
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 2:
                data.append({
                    'Date': pd.to_datetime(cols[0].text.strip(), format='%d/%m/%Y'),
                    'Taux': float(cols[1].text.strip().replace(',', '.'))
                })

        return pd.DataFrame(data)

    except Exception as e:
        st.error(f"Erreur lors du scraping réserves obligatoires : {str(e)}")
        return pd.DataFrame()

