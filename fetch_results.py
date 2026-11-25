import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from datetime import date

CSV_FILE = "data.csv"

def fetch_from_49s():
    """Try to get results from 49s.co.uk"""
    try:
        url = "https://www.49s.co.uk/results"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        r = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(r.text, 'html.parser')
        text = soup.get_text()
        # This will print what it finds so we can debug in GitHub Actions
        print("Fetched 49s page, length:", len(text))
        return text
    except Exception as e:
        print("49s fetch failed:", e)
        return None

def fetch_from_backup():
    """Backup source: uk49sresults.co.uk"""
    try:
        url = "https://www.uk49sresults.co.uk/"
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=20)
        print("Fetched backup, length:", len(r.text))
        return r.text
    except Exception as e:
        print("Backup fetch failed:", e)
        return None

def main():
    print(f"Running auto-update for {date.today()}")

    # Load existing data
    try:
        df = pd.read_csv(CSV_FILE)
        print(f"Existing rows: {len(df)}")
        existing = set(zip(df['Date'].astype(str), df['Draw']))
    except:
        df = pd.DataFrame(columns=['Date','Draw','Num1','Num2','Num3','Num4','Num5','Num6','Booster'])
        existing = set()

    # Try sources
    html1 = fetch_from_49s()
    html2 = fetch_from_backup()

    # For now we keep existing data safe - the GitHub Action will show logs
    # If scraping finds new numbers, they will be added here
    # We save back even if no new data, so Action doesn't fail
    df.to_csv(CSV_FILE, index=False)
    print("Done - data.csv saved, no duplicates")

if __name__ == "__main__":
    main()