"""
|Bucket | Days | Weight |Date |PyPSA Revenue |Spread | 
|Low | 51 | 13.9% |2024-02-24 | A$4.75 |A$126/MWh|
|Typical|227 | 62.0%|2024-09-27|A$28.25|A$213/MWh|
|High|5214.2%|2024-06-25|A$61.33|A$270/MWh|
|Very high|267.1%|2024-05-03|A$269.85|A$4,977/MWh|
|Spike|10|2.7%|2024-02-29|A$1,593.72|A$13,292/MWh|
"""
from src.dp.prices import load_and_clean, extract_day
import pandas as pd

def main():

    filepaths = [f'data/aemo/PRICE_AND_DEMAND_2024{m:02d}_NSW1.csv' for m in range(1,13)]
    df = load_and_clean(filepaths)

    days = {
        'low':       '2024-02-24',
        'typical':   '2024-09-27',
        'high':      '2024-06-25',
        'very_high': '2024-05-03',
        'spike':     '2024-02-29',
    }

    for label, date in days.items():
        prices = extract_day(df, date)
        if prices is not None:
            filename = f'data/aemo/prices_{label}_{date}.csv'
            pd.DataFrame({'price_mwh': prices}).to_csv(filename, index=False)
            print(f'  {label:<12} {date}  A${prices.min():.0f} to A${prices.max():.0f}/MWh  ({len(prices)} periods) → {filename}')
        else:
            print(f'  {label:<12} {date}  FAILED — incomplete day')


if __name__ == "__main__":
    main()