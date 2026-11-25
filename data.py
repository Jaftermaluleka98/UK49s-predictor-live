import requests
import pandas as pd
from datetime import datetime, timedelta

# UK49s results from 49s API (public results page)
# We scrape last 90 days - Lunchtime 12:49, Teatime 17:49 UK time

def fetch_draws():
    # Using 49s.co.uk results archive
    all_rows = []
    # Try last 30 days, day by day
    for i in range(60):
        d = datetime.now() - timedelta(days=i)
        date_str = d.strftime("%Y-%m-%d")
        # This endpoint returns JSON for that date
        url = f"https://www.49s.co.uk/results/{date_str}"
        try:
            r = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
            # If site blocks, we fall back to manual CSV below
            print(f"Checked {date_str}")
        except:
            pass
    return all_rows

if __name__ == "__main__":
    print("NOTE: 49s site blocks auto-scraping sometimes.")
    print("Easiest reliable way: download CSV manually once, then app does the analysis.")
    print("Go to https://www.49s.co.uk/results -> download / copy last 100 draws into data.csv")