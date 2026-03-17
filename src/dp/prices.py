"""
AEMO NEM price data — download and load.

Data source: AEMO aggregated price and demand (public, no auth required).
Region: NSW1 (covers ACT).
Resolution: 5-minute dispatch intervals, resampled to 30-minute.
"""

import pandas as pd 
import numpy as np
import requests
import os
import time

URL_TEMPLATE = (
    'https://aemo.com.au/aemo/data/nem/priceanddemand/'
    'PRICE_AND_DEMAND_{yyyymm}_{region}.csv'
)

def download_prices(start_year, start_month, end_year, end_month,
                    region='NSW1', data_dir='data/aemo'):
    """
    Download monthly price CSVs from AEMO.

    Returns:
        list of downloaded file paths
    """
    os.makedirs(data_dir, exist_ok=True)
    filepaths = []
    year, month = start_year, start_month

    while (year, month) <= (end_year, end_month):
        yyyymm = f"{year}{month:02d}"
        filename = f"PRICE_AND_DEMAND_{yyyymm}_{region}.csv"
        filepath = os.path.join(data_dir, filename)

        if os.path.exists(filepath):
            print(f"  Already exists: {filename}")
            filepaths.append(filepath)
        else:
            url = URL_TEMPLATE.format(yyyymm=yyyymm, region=region)
            print(f"  Downloading: {filename}")
            headers = {'User-Agent': 'Mozilla/5.0 (compatible; research/1.0)'}
            try:
                resp = requests.get(url, headers=headers, timeout=30)
                if resp.status_code == 200:
                    with open(filepath, 'wb') as f:
                        f.write(resp.content)
                    filepaths.append(filepath)
                else:
                    print(f"    Failed: HTTP {resp.status_code}")
            except Exception as e:
                print(f"    Error: {e}")
            time.sleep(2)

        month += 1
        if month > 12:
            month = 1
            year += 1

    return filepaths


def load_and_clean(filepaths):
    """
    Load AEMO CSVs, resample from 5-min to 30-min, return clean DataFrame.

    Returns:
        DataFrame with columns: datetime, price ($/MWh), demand (MW)
    """
    dfs = []
    for fp in filepaths:
        try:
            df = pd.read_csv(fp)
            # If the value is not numeric (e.g., "N/A", "--", "abc") → it becomes NaN because of errors='coerce'
            # RRP: Regional Reference Price
            df = df[pd.to_numeric(df['RRP'], errors='coerce').notna()]
            dfs.append(df)
        except Exception as e:
            print(f"  Warning: could not read {fp}: {e}")
    
    if not dfs:
        return pd.DataFrame()

    combined = pd.concat(dfs, ignore_index=True)
    combined['datetime'] = pd.to_datetime(combined['SETTLEMENTDATE'])
    combined['price'] = combined['RRP'].astype(float)
    combined['demand'] = combined['TOTALDEMAND'].astype(float)
    combined = combined.sort_values('datetime').reset_index(drop=True)

    # Shift timestamp to start of interval
    # AEMO’s SETTLEMENTDATE marks the end of the 5‑minute dispatch interval.
    # For example:
    # - A row with 00:10 represents 00:05 → 00:10
    # To make the data align with the start of each interval, you shift it back:
    combined['datetime'] = combined['datetime'] - pd.Timedelta(minutes=5)

    # Resample 5-min -> 30-min (NEM settlement = average of six dispatch prices)
    combined = combined.set_index('datetime')
    resampled = combined[['price', 'demand']].resample('30min').mean()
    resampled = resampled.dropna().reset_index()

    return resampled


def extract_day(df, date_str):
    """Extract 48 half-hourly prices for a single day"""
    date = pd.to_datetime(date_str)
    
    # [date,date+1)
    day_data = df[(df['datetime'] >= date) & 
                  (df['datetime'] < date + pd.Timedelta(days=1))]
    if len(day_data) < 40:
        return None
    return day_data['price'].values

def find_interesting_days(df):
    """Find days with different price characteristics."""
    df = df.copy()
    df['date'] = df['datetime'].dt.date

    daily = df.groupby('date').agg(
        mean_price=('price', 'mean'),
        max_price=('price', 'max'),
        spread=('price', lambda x: x.max() - x.min())
    )
    counts = df.groupby('date').size()
    complete = counts[counts == 48].index
    daily = daily.loc[daily.index.isin(complete)]

    results = {}

    median_spread = daily['spread'].median()
    results['typical'] = str((daily['spread'] - median_spread).abs().idxmin())
    results['high_spread'] = str(daily['spread'].idxmax())
    results['spike'] = str(daily['max_price'].idxmax())
    results['low_avg'] = str(daily['mean_price'].idxmin())

    return results


def load_day_prices(csv_path):
    """Load a single-day price CSV (48 rows, column 'price_mwh)"""
    df = pd.read_csv(csv_path)
    if 'price_mwh' in df.columns:
        return df['price_mwh'].values.astype(float)
    elif 'price' in df.columns:
        return df['price'].values.astype(float)
    return df.iloc[:, 0].values.astype(float) # fall back to the first column