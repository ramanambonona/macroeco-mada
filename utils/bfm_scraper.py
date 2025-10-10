# utils/bfm_scraper.py
import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from requests_toolbelt import MultipartEncoder
import random, string, io, re
from bs4 import BeautifulSoup
from pdfminer.high_level import extract_text

HEADERS = {"User-Agent": "Mozilla/5.0"}

# ------------------ Marché des changes ------------------
@st.cache_data(show_spinner=False, ttl=6*3600)
def get_taux_change(start_date, end_date, devise):
    """
    Récupère l'historique des taux de change (BFM) jour par jour.
    start_date/end_date: date/date-like
    """
    url = "https://www.banky-foibe.mg/admin/wp-json/bfm/cours_mid_en_ar_filter"
    current_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    data = []

    while current_date <= end_date:
        jour = f"{current_date.day:02d}"
        mois = f"{current_date.month:02d}"
        annee = f"{current_date.year}"
        date_bfm = f"{annee}/{mois}/{jour}"
        date_fmt = f"{annee}-{mois}-{jour}"

        fields = {"dateFilterDebut": date_bfm, "dateFilterFin": date_bfm, "filterData": devise}
        boundary = '----WebKitFormBoundary' + ''.join(random.sample(string.ascii_letters + string.digits, 16))
        m = MultipartEncoder(fields=fields, boundary=boundary)
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": m.content_type,
            "User-Agent": HEADERS["User-Agent"],
        }

        try:
            with requests.Session() as s:
                r = s.post(url, headers=headers, data=m, timeout=12)
                if r.status_code == 200:
                    rj = r.json()
                    try:
                        taux_str = rj["data"]["data"]["coursMid"][date_fmt]
                        taux = float(taux_str.replace(",", "."))
                        data.append({"Date": pd.to_datetime(date_fmt), "Taux": taux})
                    except (KeyError, ValueError, TypeError):
                        pass
        except Exception:
            # on ignore silencieusement ce jour
            pass

        current_date += timedelta(days=1)

    df = pd.DataFrame(data)
    if not df.empty:
        df = df.sort_values("Date").reset_index(drop=True)
    return df

# ------------------ Taux directeur ------------------
@st.cache_data(show_spinner=False, ttl=24*3600)
def get_taux_directeur():
    try:
        url = "https://www.banky-foibe.mg/taux_evolution-du-taux-directeur-de-la-banque-centrale"
        r = requests.get(url, headers=HEADERS, timeout=12)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        content = soup.find("div", class_="content-article")
        if content:
            table = content.find("table")
            if table:
                rows = table.find_all("tr")[1:]
                data = []
                for row in rows:
                    cols = row.find_all("td")
                    if len(cols) >= 2:
                        date_str = cols[0].get_text(strip=True)
                        taux_str = cols[1].get_text(strip=True).replace(",", ".").replace("%", "")
                        try:
                            d = pd.to_datetime(date_str, format="%d/%m/%Y")
                            taux = float(taux_str)
                            data.append({"Date": d, "Taux": taux})
                        except Exception:
                            continue
                df = pd.DataFrame(data)
                if not df.empty:
                    return df.sort_values("Date").reset_index(drop=True)
    except Exception as e:
        st.error(f"Erreur taux directeur : {e}")
    return pd.DataFrame()

# ------------------ Inflation (dernier taux affiché page d'accueil) ------------------
@st.cache_data(show_spinner=False, ttl=6*3600)
def get_inflation_latest():
    try:
        url = "https://www.banky-foibe.mg/"
        r = requests.get(url, headers=HEADERS, timeout=12)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text(" ").lower()

        # Exemple attendu: "taux d'inflation % ... en juillet 2025. 7,9"
        m = re.search(r"taux d'inflation\s*%.*?en\s+([a-zéû]+)\s+(\d{4}).*?([\d,]+)", text, re.IGNORECASE | re.DOTALL)
        if m:
            month_name, year, rate_str = m.group(1), m.group(2), m.group(3)
            month_map = {
                'janvier':1,'février':2,'fevrier':2,'mars':3,'avril':4,'mai':5,'juin':6,
                'juillet':7,'août':8,'aout':8,'septembre':9,'octobre':10,'novembre':11,'décembre':12,'decembre':12
            }
            month = month_map.get(month_name.lower(), 1)
            d = pd.to_datetime(f"{year}-{month:02d}-01")
            return pd.DataFrame([{"Date": d, "Taux": float(rate_str.replace(",", "."))}])
    except Exception as e:
        st.error(f"Erreur inflation latest : {e}")
    return pd.DataFrame()

# ------------------ Agrégats monétaires (PDF) ------------------
@st.cache_data(show_spinner=False, ttl=24*3600)
def get_agregats_monetaires():
    try:
        pdf_url = "https://www.banky-foibe.mg/pdf_monnaie-et-credit"
        r = requests.get(pdf_url, headers=HEADERS, stream=True, timeout=20)
        r.raise_for_status()
        # Vérifie rapidement que c'est bien du PDF
        if "application/pdf" not in r.headers.get("Content-Type","").lower():
            return pd.DataFrame()
        text = extract_text(io.BytesIO(r.content)).lower()

        date_match = re.search(r'au\s+(\d{1,2}/\d{1,2}/\d{4})', text)
        d = pd.to_datetime(date_match.group(1), format="%d/%m/%Y") if date_match else datetime.now()

        # Motifs basiques (dépend du PDF réel)
        m1 = re.search(r'\bm1\b.*?([\d\s,]+)', text)
        m2 = re.search(r'\bm2\b.*?([\d\s,]+)', text)
        m3 = re.search(r'\bm3\b.*?([\d\s,]+)', text)

        data = {"Date": d}
        for k, m in (("M1 (Liquidités)", m1), ("M2 (Masse monétaire)", m2), ("M3 (Quasi-monnaie)", m3)):
            if m:
                v = m.group(1).replace(" ", "").replace(",", ".")
                try:
                    data[k] = float(v)
                except Exception:
                    pass

        df = pd.DataFrame([data])
        return df
    except Exception as e:
        st.error(f"Erreur agrégats monétaires : {e}")
        return pd.DataFrame()

# ------------------ Taux marché monétaire (PDF) ------------------
@st.cache_data(show_spinner=False, ttl=24*3600)
def get_marche_monetaire_rates():
    try:
        pdf_url = "https://www.banky-foibe.mg/pdf_marche-monetaire"
        r = requests.get(pdf_url, headers=HEADERS, stream=True, timeout=20)
        r.raise_for_status()
        if "application/pdf" not in r.headers.get("Content-Type","").lower():
            return pd.DataFrame()
        text = extract_text(io.BytesIO(r.content)).lower()

        date_match = re.search(r'au\s+(\d{1,2}/\d{1,2}/\d{4})', text)
        d = pd.to_datetime(date_match.group(1), format="%d/%m/%Y") if date_match else datetime.now()

        lt7 = re.search(r'tmp\s*<\s*7\s*jours?\s*[:\-]?\s*([\d,]+)', text)
        gt7 = re.search(r'tmp\s*>\s*7\s*jours?\s*[:\-]?\s*([\d,]+)', text)

        data = {"Date": d}
        if lt7:
            data["TMP_lt7"] = float(lt7.group(1).replace(",", "."))
        if gt7:
            data["TMP_gt7"] = float(gt7.group(1).replace(",", "."))

        return pd.DataFrame([data])
    except Exception as e:
        st.error(f"Erreur marché monétaire : {e}")
        return pd.DataFrame()

# ------------------ BTA (PDFs) ------------------
@st.cache_data(show_spinner=False, ttl=24*3600)
def get_bta_rates():
    urls = [
        "https://www.banky-foibe.mg/pdf_evolution_des_taux_des_bta",
        "https://www.banky-foibe.mg/pdf_taux-de-rendement-moyen-des-bta",
    ]
    data = []
    maturities = ["4 sem", "12 sem", "24 sem", "36 sem", "52 sem"]
    for url in urls:
        try:
            r = requests.get(url, headers=HEADERS, stream=True, timeout=20)
            r.raise_for_status()
            if "application/pdf" not in r.headers.get("Content-Type","").lower():
                continue
            text = extract_text(io.BytesIO(r.content)).lower()
            for mat in maturities:
                # ✅ regex avec espaces flexibles: "4\s*sem", etc.
                #   ATTENTION: utiliser r"\s*" pour un vrai motif regex
                mat_regex = re.sub(r"\s+", r"\\s*", mat)  # "4 sem" -> "4\s*sem"
                m = re.search(rf'{mat_regex}.*?([\d,]+)', text)
                if m:
                    rate = float(m.group(1).replace(",", "."))
                    data.append({"Maturité": mat, "Taux": rate})
        except Exception:
            pass
    df = pd.DataFrame(data)
    return df.drop_duplicates().reset_index(drop=True)

# ------------------ Réserves obligatoires ------------------
@st.cache_data(show_spinner=False, ttl=24*3600)
def get_reserves_obligatoires():
    try:
        url = "https://www.banky-foibe.mg/taux_coefficient-de-reserve-obligatoire"
        r = requests.get(url, headers=HEADERS, timeout=12)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        content = soup.find("div", class_="content-article")
        if content:
            table = content.find("table")
            if table:
                rows = table.find_all("tr")[1:]
                data = []
                for row in rows:
                    cols = row.find_all("td")
                    if len(cols) >= 2:
                        date_str = cols[0].get_text(strip=True)
                        taux_str = cols[1].get_text(strip=True).replace(",", ".").replace("%", "")
                        try:
                            d = pd.to_datetime(date_str, format="%d/%m/%Y")
                            taux = float(taux_str)
                            data.append({"Date": d, "Taux": taux})
                        except Exception:
                            continue
                df = pd.DataFrame(data)
                if not df.empty:
                    return df.sort_values("Date").reset_index(drop=True)
    except Exception as e:
        st.error(f"Erreur réserves obligatoires : {e}")
    return pd.DataFrame()
