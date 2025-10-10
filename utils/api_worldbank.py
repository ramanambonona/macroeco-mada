import requests
import pandas as pd

BASE_URL = "https://api.worldbank.org/v2/country"
COUNTRY = "MDG"

def get_data(indicator):
    url = f"{BASE_URL}/{COUNTRY}/indicator/{indicator}?format=json&per_page=100"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data and len(data) > 1:
            df = pd.DataFrame([{
                'Année': int(entry['date']),
                'Valeur': entry['value']
            } for entry in data[1] if entry['value'] is not None])
            return df.sort_values(by='Année')
    return pd.DataFrame()
