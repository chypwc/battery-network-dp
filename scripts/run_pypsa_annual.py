"""
Full-year battery dispatch optimisation using PyPSA.

Runs PyPSA LOPF for every day of 2024 using AEMO NSW1 spot prices,
producing annual revenue statistics for the NPV model.

Usage:
    python run_pypsa_annual.py          # run optimisation + analysis
    python run_pypsa_annual.py --cached  # skip optimisation, analyse saved results
"""

import logging
import warnings
import time
import sys
import os

import numpy as np
import pandas as pd 

logging.getLogger("pypsa").setLevel(logging.ERROR)
logging.getLogger("linopy").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", category=FutureWarning)

from src.dp.prices import load_and_clean, extract_day, build_tou_profile
from src.pypsa.dispatch import optimise_day, optimise_year
from src.pypsa.analysis import (
    load_annual_results,
    compute_statistics,
    seasonal_breakdown,
    monthly_breakdown,
    revenue_distribution_buckets,
    top_spike_days,
)

AEMO_DIR = "data/aemo"
OUTPUT_CSV = "data/pypsa/annual_revenue.csv"

# Battery configuration — matches GenCost 2hr spec
CAPACITY_KWH = 200
POWER_KW = 100
EFFICIENCY = 0.95
DEGRADATION = 0.02

def run_optimisation():
    """Run PyPSA LOPF for every complete day in 2024."""
    print("=" * 70)
    print("  PyPSA Full-Year Battery Dispatch Optimisation")
    print("=" * 70)

    # Load and clean ARMO price data
    filepaths = [
        os.path.join(AEMO_DIR, f"PRICE_AND_DEMAND_2024{m:02d}_NSW1.csv")
        for m in range(1, 13)
    ]
    print(f"\nLoading {len(filepaths)} monthly AEMO price files...")
    df = load_and_clean(filepaths)
    print(f"  {len(df)} half-hourly records")
    print(f"  {df['datetime'].min()} to {df['datetime'].max()}")

    # Find complete days (exactly 48 half-hours)
    df["date"] = df["datetime"].dt.date
    counts = df.groupby("date").size()
    complete_days = sorted(counts[counts == 48].index)
    print(f"  {len(complete_days)} complete days")

    # Extract daily price arrays
    daily_prices = []
    dates = []
    for date in complete_days:
        prices = extract_day(df, str(date))
        if prices is not None and len(prices) == 48:
            daily_prices.append(prices)
            dates.append(date)

    print(f"\nOptimising {len(dates)} days "
          f"(±{POWER_KW}kW / {CAPACITY_KWH}kWh, "
          f"η={EFFICIENCY}, deg=A${DEGRADATION}/kWh)...")
    
    t0 = time.time()
    results = optimise_year(
        daily_prices=daily_prices,
        dates=dates,
        capacity_kwh=CAPACITY_KWH,
        power_kw=POWER_KW,
        efficiency=EFFICIENCY,
        degradation=DEGRADATION,
    )
    elapsed = time.time() - t0
    print(f"  Completed in {elapsed:.1f}s ({elapsed/len(dates)*1000:.0f}ms per day)")

    # Save results
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    results.to_csv(OUTPUT_CSV, index=False)
    print(f"  Saved to {OUTPUT_CSV}")

    return results


def print_analysis(df):
    """Print comprehensive analysis of annual results."""
    stats = compute_statistics(df)

    print("\n" + "=" * 70)
    print("  Annual Revenue Statistics — Spot Arbitrage (±100kW / 200kWh)")
    print("=" * 70)

    print(f"\n  {'Days analysed':>30}: {stats['num_days']}")
    print(f"  {'Annual total':>30}: A${stats['annual_total']:>10,.0f}")
    print(f"  {'Mean daily':>30}: A${stats['mean_daily']:>10.2f}")
    print(f"  {'Median daily':>30}: A${stats['median_daily']:>10.2f}")
    print(f"  {'Std dev':>30}: A${stats['std_daily']:>10.2f}")
    print(f"  {'P10':>30}: A${stats['p10']:>10.2f}")
    print(f"  {'P90':>30}: A${stats['p90']:>10.2f}")
    print(f"  {'Min':>30}: A${stats['min_daily']:>10.2f}")
    print(f"  {'Max':>30}: A${stats['max_daily']:>10.2f}")
    print(f"  {'Spike days (> A$500)':>30}: {stats['num_spike_days']}")

    # Spike day impact
    print(f"\n  Spike Day Impact:")
    print(f"  {'':>20} {'Annual':>10} {'Mean daily':>12}")
    print(f"  {'Full year':>20} A${stats['annual_total']:>9,.0f} A${stats['mean_daily']:>10.2f}")
    for n in [5, 10, 20]:
        key_a = f"annual_excl_top{n}"
        key_m = f"mean_excl_top{n}"
        print(f"  {'Excl top ' + str(n) + ' days':>20} A${stats[key_a]:>9,.0f} A${stats[key_m]:>10.2f}")

    # Comparison with single-day estimate
    single_day = 36.30
    tou_daily = 81.56
    print(f"\n  Comparison with Single-Day Estimates:")
    print(f"  {'Our typical day (Jun 28)':>30}: A${single_day:.2f}/day → A${single_day * 365:>10,.0f}/year")
    print(f"  {'PyPSA median day':>30}: A${stats['median_daily']:.2f}/day → A${stats['median_daily'] * 365:>10,.0f}/year")
    print(f"  {'PyPSA mean (incl spikes)':>30}: A${stats['mean_daily']:.2f}/day → A${stats['annual_total']:>10,.0f}/year")
    print(f"  {'PyPSA conservative (excl top 20)':>30}: A${stats['mean_excl_top20']:.2f}/day → A${stats['annual_excl_top20']:>10,.0f}/year")
    print(f"  {'TOU fixed (every day)':>30}: A${tou_daily:.2f}/day → A${tou_daily * 365.25:>10,.0f}/year")

    # Revenue distribution
    print(f"\n  Revenue Distribution:")
    buckets = revenue_distribution_buckets(df)
    for _, row in buckets.iterrows():
        bar = "█" * int(row["pct"] / 2)
        print(f"  {row['bucket']:>12}: {row['days']:>4} days ({row['pct']:>5.1f}%) {bar}")

    # Seasonal
    print(f"\n  Seasonal Breakdown (Australian seasons):")
    seasons = seasonal_breakdown(df)
    print(f"  {'Season':>8} {'Days':>5} {'Total':>10} {'Mean':>8} {'Median':>8}")
    for season, row in seasons.iterrows():
        print(f"  {season:>8} {row['days']:>5.0f} A${row['total']:>8,.0f} A${row['mean']:>6.1f} A${row['median']:>6.1f}")

    # Top spike days
    print(f"\n  Top 10 Revenue Days:")
    spikes = top_spike_days(df, 10)
    for _, row in spikes.iterrows():
        date_str = row["date"].strftime("%Y-%m-%d") if hasattr(row["date"], "strftime") else str(row["date"])
        print(f"  {date_str}  A${row['revenue']:>8,.2f}  (max price A${row['max_price']:>6,.0f}/MWh)")

    # TOU comparison
    print(f"\n  TOU vs Spot Comparison:")
    print(f"  {'':>30} {'Spot':>12} {'TOU':>12}")
    print(f"  {'Daily (median)':>30} A${stats['median_daily']:>10.2f} A${tou_daily:>10.2f}")
    print(f"  {'Daily (mean incl spikes)':>30} A${stats['mean_daily']:>10.2f} A${tou_daily:>10.2f}")
    print(f"  {'Annual':>30} A${stats['annual_total']:>10,.0f} A${tou_daily * 365.25:>10,.0f}")
    print(f"  {'Predictability':>30} {'High variance':>12} {'Fixed daily':>12}")


def main():
    use_cached = "--cached" in sys.argv

    if use_cached and os.path.exists(OUTPUT_CSV):
        print(f"Loading cached results from {OUTPUT_CSV}")
        df = load_annual_results(OUTPUT_CSV)
    else:
        results = run_optimisation()
        df = load_annual_results(OUTPUT_CSV)

    print_analysis(df)


if __name__ == "__main__":
    main()