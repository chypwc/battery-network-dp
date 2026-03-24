from src.dp.prices import download_prices, load_and_clean, find_interesting_days, extract_day
import pandas as pd
import numpy as np
import os


def main():
    # --- Download 5 years ---
    start_year = 2018
    start_month = 1
    end_year = 2023
    end_month = 12

    print(f"=== Downloading AEMO NSW1 price data ({start_year}-{end_year}) ===\n")
    filepaths = download_prices(start_year, start_month, end_year, end_month)
    if not filepaths:
        print("No files downloaded.")
        return

    # --- Clean and resample ---
    print("\nProcessing...")
    df = load_and_clean(filepaths)
    print(f"  {len(df)} half-hourly records")
    print(f"  {df['datetime'].min()} to {df['datetime'].max()}")
    print(f"  Price: ${df['price'].min():.0f} to ${df['price'].max():.0f}/MWh "
          f"(mean ${df['price'].mean():.0f})")

    # --- Save full 5-year cleaned data ---
    clean_file_full = f'data/aemo/nem_prices_NSW1_{start_year}_{end_year}_clean.csv'
    df.to_csv(clean_file_full, index=False)
    print(f"\n  Saved full dataset: {clean_file_full}")

    # --- Also save 2024-only (for backward compatibility) ---
    df_2024 = df[df['datetime'].dt.year == 2024].copy()
    clean_file_2024 = 'data/aemo/nem_prices_NSW1_2024_clean.csv'
    df_2024.to_csv(clean_file_2024, index=False)
    print(f"  Saved 2024 dataset: {clean_file_2024}")

    # --- Annual distribution comparison ---
    print("\n=== Annual Price Distributions ===\n")
    print(f"  {'Year':>6s}  {'Days':>5s}  {'Mean':>8s}  {'Median':>8s}  "
          f"{'Std':>8s}  {'P10':>8s}  {'P90':>8s}  {'Max':>8s}  "
          f"{'Neg%':>6s}  {'Spike%':>7s}")

    df['date'] = df['datetime'].dt.date
    df['year'] = df['datetime'].dt.year

    for year in range(start_year, end_year + 1):
        year_mask = df['year'] == year
        year_prices = df[year_mask]['price']
        n_days = df[year_mask].groupby('date').size()
        n_complete = (n_days == 48).sum()

        neg_pct = (year_prices < 0).mean() * 100
        spike_pct = (year_prices > 300).mean() * 100

        print(f"  {year:>6d}  {n_complete:5d}  "
              f"${year_prices.mean():>7.1f}  ${year_prices.median():>7.1f}  "
              f"${year_prices.std():>7.1f}  ${year_prices.quantile(0.10):>7.1f}  "
              f"${year_prices.quantile(0.90):>7.1f}  "
              f"${year_prices.max():>7.0f}  "
              f"{neg_pct:>5.1f}%  {spike_pct:>6.2f}%")

    # --- Daily spread comparison ---
    print("\n=== Daily Spread Distributions ===\n")
    print(f"  {'Year':>6s}  {'Days':>5s}  {'Mean Spread':>12s}  "
          f"{'Median Spread':>14s}  {'Max Spread':>11s}  "
          f"{'Days>$500':>10s}  {'Days>$1000':>11s}")

    daily = df.groupby(['year', 'date']).agg(
        spread=('price', lambda x: x.max() - x.min()),
        n_periods=('price', 'size')
    ).reset_index()
    daily = daily[daily['n_periods'] == 48]

    for year in range(start_year, end_year + 1):
        year_daily = daily[daily['year'] == year]
        spreads = year_daily['spread']
        n_500 = (spreads > 500).sum()
        n_1000 = (spreads > 1000).sum()

        print(f"  {year:>6d}  {len(year_daily):5d}  "
              f"${spreads.mean():>11.1f}  ${spreads.median():>13.1f}  "
              f"${spreads.max():>10.0f}  "
              f"{n_500:>10d}  {n_1000:>11d}")

    # --- Regime stationarity check ---
    # Compute (log spread, log mean) features per day and compare across years
    print("\n=== Regime Feature Distributions (log spread, log mean) ===\n")

    daily_features = df.groupby(['year', 'date']).agg(
        mean_price=('price', 'mean'),
        spread=('price', lambda x: x.max() - x.min()),
        n_periods=('price', 'size')
    ).reset_index()
    daily_features = daily_features[daily_features['n_periods'] == 48]

    shift = 0
    if daily_features['mean_price'].min() <= 0:
        shift = abs(daily_features['mean_price'].min()) + 1

    daily_features['log_spread'] = np.log1p(daily_features['spread'])
    daily_features['log_mean'] = np.log1p(daily_features['mean_price'] + shift)

    print(f"  {'Year':>6s}  {'log_spread mean':>15s}  {'log_spread std':>15s}  "
          f"{'log_mean mean':>14s}  {'log_mean std':>13s}")

    for year in range(start_year, end_year + 1):
        ym = daily_features[daily_features['year'] == year]
        print(f"  {year:>6d}  {ym['log_spread'].mean():>15.3f}  "
              f"{ym['log_spread'].std():>15.3f}  "
              f"{ym['log_mean'].mean():>14.3f}  "
              f"{ym['log_mean'].std():>13.3f}")

    # --- Find and export interesting days (2024 only) ---
    # print("\n=== Interesting Days (2024) ===\n")
    # days = find_interesting_days(df_2024)
    # for label, date in days.items():
    #     prices = extract_day(df_2024, date)
    #     if prices is not None:
    #         filename = f'data/aemo/prices_{label}_{date}.csv'
    #         pd.DataFrame({'price_mwh': prices}).to_csv(filename, index=False)
    #         print(f"  {label:<15} {date}  "
    #               f"${prices.min():.0f} to ${prices.max():.0f}/MWh → {filename}")


if __name__ == '__main__':
    main()
