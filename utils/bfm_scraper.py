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
from bs4 import BeautifulSoup  # Added missing import

def get_taux_change(start_date, end_date, devise):
    """Récupère l'historique des taux de change (marché des changes)"""
    url = 'https://www.banky-foibe.mg/admin/wp-json/bfm/cours_mid_en_ar_filter'
    current_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    
    data = []

    with st.spinner("?? Téléchargement des taux de change..."):
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
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }

            try:
                with requests.Session() as s:
                    response = s.post(url, headers=headers, data=m, timeout=10)
                    if response.status_code == 200:
                        r_json = response.json()
                        try:
                            taux_str = r_json["data"]["data"]["coursMid"][date_format]
                            taux = float(taux_str.replace(",", "."))
                            data.append({
                                'Date': pd.to_datetime(date_format),
                                'Taux': taux
                            })
                        except (KeyError, ValueError, AttributeError):
                            pass
            except Exception:
                pass

            current_date += timedelta(days=1)
    
    df = pd.DataFrame(data)
    if not df.empty:
        df = df.sort_values('Date').reset_index(drop=True)
    return df

def get_taux_directeur():
    """Récupère l'historique du taux directeur"""
    try:
        url = "https://www.banky-foibe.mg/taux_evolution-du-taux-directeur-de-la-banque-centrale"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        content_div = soup.find('div', class_='content-article')
        if content_div:
            table = content_div.find('table')
            if table:
                rows = table.find_all('tr')[1:]  # Skip header

                data = []
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 2:
                        date_str = cols[0].text.strip()
                        taux_str = cols[1].text.strip().replace(',', '.').replace('%', '')
                        try:
                            date = pd.to_datetime(date_str, format='%d/%m/%Y')
                            taux = float(taux_str)
                            data.append({'Date': date, 'Taux': taux})
                        except (ValueError, TypeError):
                            continue
                df = pd.DataFrame(data)
                if not df.empty:
                    return df.sort_values('Date').reset_index(drop=True)
    except Exception as e:
        st.error(f"Erreur lors du scraping taux directeur : {str(e)}")
    return pd.DataFrame()

def get_inflation_latest():
    """Récupère le dernier taux d'inflation depuis la page d'accueil"""
    try:
        url = "https://www.banky-foibe.mg/"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for inflation text, e.g., "Taux d'inflation % ... en juillet 2025. 7,9"
        text = soup.get_text()
        match = re.search(r"Taux d'inflation %.*?en (\w+ \d{4})\.\s*([\d,]+)", text, re.IGNORECASE)
        if match:
            month_year = match.group(1)
            rate_str = match.group(2).replace(',', '.')
            # Parse month_year to date, approximate
            month_map = {'janvier': 1, 'février': 2, 'mars': 3, 'avril': 4, 'mai': 5, 'juin': 6,
                         'juillet': 7, 'août': 8, 'septembre': 9, 'octobre': 10, 'novembre': 11, 'décembre': 12}
            parts = month_year.split()
            month = month_map.get(parts[0].lower(), 1)
            year = int(parts[1])
            date = pd.to_datetime(f"{year}-{month:02d}-01")
            return pd.DataFrame([{'Date': date, 'Taux': float(rate_str)}])
    except Exception as e:
        st.error(f"Erreur scraping inflation latest: {e}")
    return pd.DataFrame()

def get_agregats_monetaires():
    """Récupère les agrégats monétaires à partir du PDF latest"""
    try:
        pdf_url = "https://www.banky-foibe.mg/pdf_monnaie-et-credit"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(pdf_url, headers=headers, stream=True)
        response.raise_for_status()
        text = extract_text(io.BytesIO(response.content)).lower()  # Lower for easier regex

        # Improved patterns based on snippets
        date_match = re.search(r'au\s+(\d{1,2}/\d{1,2}/\d{4})', text)
        date = pd.to_datetime(date_match.group(1), format='%d/%m/%Y') if date_match else datetime.now()

        # Patterns for values, e.g., "m3 ... 20 936,8" or "+6,5 %"
        m1_match = re.search(r'm1.*?([\d\s,]+)', text)
        m2_match = re.search(r'm2.*?([\d\s,]+)', text)
        m3_match = re.search(r'm3.*?([\d\s,]+)', text)

        data = {'Date': date}
        for key, match in [('M1', m1_match), ('M2', m2_match), ('M3', m3_match)]:
            if match:
                value_str = match.group(1).replace(' ', '').replace(',', '.')
                data[key] = float(value_str)

        df = pd.DataFrame([data])
        df = df.rename(columns={'M1': 'M1 (Liquidités)', 'M2': 'M2 (Masse monétaire)', 'M3': 'M3 (Quasi-monnaie)'})
        return df

    except Exception as e:
        st.error(f"Erreur lecture agrégats monétaires : {str(e)}")
        return pd.DataFrame()

def get_marche_monetaire_rates():
    """Récupère les taux du marché monétaire depuis PDF"""
    try:
        pdf_url = "https://www.banky-foibe.mg/pdf_marche-monetaire"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(pdf_url, headers=headers, stream=True)
        text = extract_text(io.BytesIO(response.content)).lower()

        date_match = re.search(r'au\s+(\d{1,2}/\d{1,2}/\d{4})', text)
        date = pd.to_datetime(date_match.group(1), format='%d/%m/%Y') if date_match else datetime.now()

        # Patterns for TMP
        lt7_match = re.search(r'tmp\s*<7\s*jours?\s*[:\-]?\s*([\d,]+)', text)
        gt7_match = re.search(r'tmp\s*>7\s*jours?\s*[:\-]?\s*([\d,]+)', text)

        data = {'Date': date}
        if lt7_match:
            data['TMP_lt7'] = float(lt7_match.group(1).replace(',', '.'))
        if gt7_match:
            data['TMP_gt7'] = float(gt7_match.group(1).replace(',', '.'))

        return pd.DataFrame([data])
    except Exception as e:
        st.error(f"Erreur marché monétaire : {str(e)}")
        return pd.DataFrame()

def get_bta_rates():
    """Récupère les taux des BTA depuis PDFs"""
    urls = [
        "https://www.banky-foibe.mg/pdf_evolution_des_taux_des_bta",
        "https://www.banky-foibe.mg/pdf_taux-de-rendement-moyen-des-bta"
    ]
    data = []
    maturities = ['4 sem', '12 sem', '24 sem', '36 sem', '52 sem']
    for url in urls:
        try:
            response = requests.get(url, stream=True)
            text = extract_text(io.BytesIO(response.content)).lower()
            for mat in maturities:
                match = re.search(rf'{mat.replace(" ", "\s*")}.*?([\d,]+)', text)
                if match:
                    rate = float(match.group(1).replace(',', '.'))
                    data.append({'Maturité': mat, 'Taux': rate})
        except:
            pass
    df = pd.DataFrame(data)
    return df.drop_duplicates()

def get_reserves_obligatoires():
    """Récupère les historiques des réserves obligatoires"""
    try:
        url = "https://www.banky-foibe.mg/taux_coefficient-de-reserve-obligatoire"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        content_div = soup.find('div', class_='content-article')
        if content_div:
            table = content_div.find('table')
            if table:
                rows = table.find_all('tr')[1:]

                data = []
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 2:
                        date_str = cols[0].text.strip()
                        taux_str = cols[1].text.strip().replace(',', '.').replace('%', '')
                        try:
                            date = pd.to_datetime(date_str, format='%d/%m/%Y')
                            taux = float(taux_str)
                            data.append({'Date': date, 'Taux': taux})
                        except (ValueError, TypeError):
                            continue
                df = pd.DataFrame(data)
                if not df.empty:
                    return df.sort_values('Date').reset_index(drop=True)
    except Exception as e:
        st.error(f"Erreur lors du scraping réserves obligatoires : {str(e)}")
    return pd.DataFrame()
