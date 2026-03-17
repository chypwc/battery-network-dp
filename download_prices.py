from src.dp.prices import download_prices, load_and_clean, find_interesting_days, extract_day
import pandas as pd
import os

def main():
    start_year = 2024
    start_month = 1
    end_year = 2024
    end_month = 12
    filepaths = download_prices(start_year, start_month, end_year, end_month)

    if not filepaths:
        print("No files downloaded.")
        return
    
    # Clean and resample
    print("\nProcessing...")
    df = load_and_clean(filepaths)
    print(f"  {len(df)} half-hourly records")
    print(f"  {df['datetime'].min()} to {df['datetime'].max()}")
    print(f"  Price: ${df['price'].min():.0f} to ${df['price'].max():.0f}/MWh "
          f"(mean ${df['price'].mean():.0f})")

    # Save cleaned data
    clean_file = 'data/aemo/nem_prices_NSW1_clean.csv'
    df.to_csv(clean_file, index=False)

    # Find and export interesting days
    days = find_interesting_days(df)
    print("\nInteresting days:")
    for label, date in days.items():
        prices = extract_day(df, date)
        if prices is not None:
            filename = f'data/aemo/prices_{label}_{date}.csv'
            pd.DataFrame({'price_mwh': prices}).to_csv(filename, index=False)
            print(f"  {label:<15} {date}  ${prices.min():.0f} to ${prices.max():.0f}/MWh → {filename}")


if __name__ == '__main__':
    main()
