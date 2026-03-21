"""
Full-year dispatch analysis: PyPSA and DP for every day of 2024.

For each of the 366 complete days in 2024:
  1. Run PyPSA LP → get continuous optimal dispatch → check OpenDSS violations
  2. Run DP solver → get discrete optimal dispatch → check OpenDSS violations

This produces the complete (revenue, violations) dataset for both methods,
replacing the weighted 5-day approximation with actual results.

RL is NOT run here (would take ~30 hours). Instead, the RL/DP ratio from
the 5 representative days is applied to estimate network-safe annual revenue.

Output: data/pypsa/annual_dispatch_results.csv
    Columns: date, pypsa_revenue, pypsa_violations, pypsa_v_min, pypsa_v_max,
             dp_revenue, dp_violations, dp_v_min, dp_v_max, spread, max_price

Usage:
    python run_annual_dispatch.py          # run full analysis (~36 min)
    python run_annual_dispatch.py --cached # analyse saved results only
"""

import sys
import os
import logging
import warnings
import time

import numpy as np
import pandas as pd

logging.getLogger("pypsa").setLevel(logging.ERROR)
logging.getLogger("linopy").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", category=FutureWarning)

from src.dp.battery import Battery
from src.dp.solver import DPSolver
from src.dp.prices import load_and_clean, extract_day
from src.opendss.profiles import generate_load_profile, generate_solar_profile
from src.opendss.feeders import FEEDER_32
from src.integration import timeseries
from src.pypsa.dispatch import optimise_day as pypsa_optimise_day


# ============================================================
# Configuration
# ============================================================

DISPATCH_LIMIT = 100
CAPACITY = 200
INITIAL_SOC = 100
N_ACTIONS = 33
OUTPUT_CSV = "data/pypsa/annual_dispatch_results.csv"

# Shared setup
load_profile = generate_load_profile()
solar_profile = generate_solar_profile()
dss_file = FEEDER_32['dss_file']
battery = Battery(kwh_rated=CAPACITY, kw_rated=100)
dp_solver = DPSolver(battery, dispatch_limit=DISPATCH_LIMIT, n_soc=81, n_actions=N_ACTIONS)


def process_day(prices, date_str):
    """
    Run PyPSA and DP on one day, check both dispatches through OpenDSS.

    Returns dict with revenues and violations for both methods.
    """
    # ---- PyPSA ----
    pypsa_result = pypsa_optimise_day(
        prices, capacity_kwh=CAPACITY, power_kw=DISPATCH_LIMIT)
    pypsa_dispatch = pypsa_result['dispatch_kw']

    df_pypsa = timeseries.run(
        pypsa_dispatch, load_profile, solar_profile,
        FEEDER_32, dss_file, battery_enabled=True, battery=battery)
    s_pypsa = timeseries.summarise(df_pypsa, f"PyPSA {date_str}")

    # ---- DP ----
    dp_result = dp_solver.solve(prices, initial_soc=INITIAL_SOC)
    dp_dispatch = dp_result['dispatch']

    df_dp = timeseries.run(
        dp_dispatch, load_profile, solar_profile,
        FEEDER_32, dss_file, battery_enabled=True, battery=battery)
    s_dp = timeseries.summarise(df_dp, f"DP {date_str}")

    return {
        'date': date_str,
        'pypsa_revenue': pypsa_result['revenue'],
        'pypsa_violations': s_pypsa['violations'],
        'pypsa_v_min': s_pypsa['v_min'],
        'pypsa_v_max': s_pypsa['v_max'],
        'dp_revenue': dp_result['total_revenue'],
        'dp_violations': s_dp['violations'],
        'dp_v_min': s_dp['v_min'],
        'dp_v_max': s_dp['v_max'],
        'spread': prices.max() - prices.min(),
        'max_price': prices.max(),
        'mean_price': prices.mean(),
    }


def run_full_year():
    """Run PyPSA + DP + OpenDSS for every complete day of 2024."""
    print("=" * 90)
    print("  Full-Year Dispatch Analysis: PyPSA + DP (366 days)")
    print(f"  Battery: ±{DISPATCH_LIMIT}kW / {CAPACITY}kWh")
    print("=" * 90)

    # Load AEMO prices
    filepaths = [
        f'data/aemo/PRICE_AND_DEMAND_2024{m:02d}_NSW1.csv'
        for m in range(1, 13)
    ]
    print("\n  Loading AEMO price data...")
    df = load_and_clean(filepaths)
    df['date'] = df['datetime'].dt.date
    counts = df.groupby('date').size()
    complete_days = sorted(counts[counts == 48].index)
    print(f"  {len(complete_days)} complete days")

    # Process each day
    results = []
    t0 = time.time()

    for i, date in enumerate(complete_days):
        prices = extract_day(df, str(date))
        if prices is None or len(prices) < 48:
            continue

        try:
            r = process_day(prices[:48], str(date))
            results.append(r)
        except Exception as e:
            print(f"    WARNING: failed for {date}: {e}")
            continue

        if (i + 1) % 25 == 0:
            elapsed = time.time() - t0
            rate = elapsed / (i + 1)
            remaining = rate * (len(complete_days) - i - 1)
            print(f"    {i+1}/{len(complete_days)} days  "
                  f"({elapsed:.0f}s elapsed, ~{remaining:.0f}s remaining)  "
                  f"last: {date} PyPSA=A${r['pypsa_revenue']:.1f} "
                  f"DP=A${r['dp_revenue']:.1f}")

    elapsed = time.time() - t0
    print(f"\n  Completed {len(results)} days in {elapsed:.0f}s "
          f"({elapsed/len(results):.1f}s per day)")

    # Save
    rdf = pd.DataFrame(results)
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    rdf.to_csv(OUTPUT_CSV, index=False)
    print(f"  Saved to {OUTPUT_CSV}")

    return rdf


def print_analysis(rdf):
    """Print comprehensive analysis of full-year results."""

    print(f"\n{'='*90}")
    print(f"  FULL-YEAR RESULTS: ±{DISPATCH_LIMIT}kW / {CAPACITY}kWh ({len(rdf)} days)")
    print(f"{'='*90}")

    # ---- Revenue summary ----
    print(f"\n  Revenue Summary:")
    print(f"  {'':>20} {'PyPSA':>12} {'DP':>12}")
    print(f"  {'-'*20} {'-'*12} {'-'*12}")
    print(f"  {'Annual total':>20} A${rdf['pypsa_revenue'].sum():>10,.0f} "
          f"A${rdf['dp_revenue'].sum():>10,.0f}")
    print(f"  {'Mean daily':>20} A${rdf['pypsa_revenue'].mean():>10.2f} "
          f"A${rdf['dp_revenue'].mean():>10.2f}")
    print(f"  {'Median daily':>20} A${rdf['pypsa_revenue'].median():>10.2f} "
          f"A${rdf['dp_revenue'].median():>10.2f}")
    print(f"  {'P10':>20} A${rdf['pypsa_revenue'].quantile(0.1):>10.2f} "
          f"A${rdf['dp_revenue'].quantile(0.1):>10.2f}")
    print(f"  {'P90':>20} A${rdf['pypsa_revenue'].quantile(0.9):>10.2f} "
          f"A${rdf['dp_revenue'].quantile(0.9):>10.2f}")

    # ---- Violation summary ----
    print(f"\n  Violation Summary:")
    print(f"  {'':>25} {'PyPSA':>10} {'DP':>10}")
    print(f"  {'-'*25} {'-'*10} {'-'*10}")
    print(f"  {'Total violations/year':>25} "
          f"{rdf['pypsa_violations'].sum():>10} "
          f"{rdf['dp_violations'].sum():>10}")
    print(f"  {'Days with violations':>25} "
          f"{(rdf['pypsa_violations'] > 0).sum():>10} "
          f"{(rdf['dp_violations'] > 0).sum():>10}")
    print(f"  {'Days without violations':>25} "
          f"{(rdf['pypsa_violations'] == 0).sum():>10} "
          f"{(rdf['dp_violations'] == 0).sum():>10}")
    print(f"  {'Mean violations/day':>25} "
          f"{rdf['pypsa_violations'].mean():>10.1f} "
          f"{rdf['dp_violations'].mean():>10.1f}")
    print(f"  {'Max violations/day':>25} "
          f"{rdf['pypsa_violations'].max():>10} "
          f"{rdf['dp_violations'].max():>10}")

    # ---- Violations by revenue bucket ----
    bins = [0, 10, 50, 100, 500, float('inf')]
    labels = ['low', 'typical', 'high', 'very_high', 'spike']
    rdf = rdf.copy()
    rdf['bucket'] = pd.cut(rdf['pypsa_revenue'], bins=bins, labels=labels, right=False)

    print(f"\n  Violations by Revenue Bucket:")
    print(f"  {'Bucket':>10} {'Days':>5} "
          f"{'PyPSA Viol':>10} {'PyPSA Mean':>10} "
          f"{'DP Viol':>8} {'DP Mean':>8}")
    print(f"  {'-'*10} {'-'*5} "
          f"{'-'*10} {'-'*10} "
          f"{'-'*8} {'-'*8}")

    for label in labels:
        subset = rdf[rdf['bucket'] == label]
        if len(subset) == 0:
            continue
        print(f"  {label:>10} {len(subset):>5} "
              f"{subset['pypsa_violations'].sum():>10} "
              f"{subset['pypsa_violations'].mean():>10.1f} "
              f"{subset['dp_violations'].sum():>8} "
              f"{subset['dp_violations'].mean():>8.1f}")

    print(f"  {'TOTAL':>10} {len(rdf):>5} "
          f"{rdf['pypsa_violations'].sum():>10} "
          f"{rdf['pypsa_violations'].mean():>10.1f} "
          f"{rdf['dp_violations'].sum():>8} "
          f"{rdf['dp_violations'].mean():>8.1f}")

    # ---- Monthly breakdown ----
    rdf['month'] = pd.to_datetime(rdf['date']).dt.month
    print(f"\n  Monthly Breakdown:")
    print(f"  {'Month':>5} {'Days':>5} "
          f"{'PyPSA Rev':>10} {'PyPSA Viol':>10} "
          f"{'DP Rev':>10} {'DP Viol':>8}")
    print(f"  {'-'*5} {'-'*5} "
          f"{'-'*10} {'-'*10} "
          f"{'-'*10} {'-'*8}")

    for m in range(1, 13):
        subset = rdf[rdf['month'] == m]
        if len(subset) == 0:
            continue
        print(f"  {m:>5} {len(subset):>5} "
              f"A${subset['pypsa_revenue'].sum():>8,.0f} "
              f"{subset['pypsa_violations'].sum():>10} "
              f"A${subset['dp_revenue'].sum():>8,.0f} "
              f"{subset['dp_violations'].sum():>8}")

    # ---- RL estimate from representative day ratios ----
    # RL/DP ratios from the 5 representative days
    rl_dp_ratios = {
        'low': 5.70 / 9.57,          # 0.596
        'typical': 30.59 / 32.87,     # 0.931
        'high': 66.04 / 69.24,        # 0.954
        'very_high': 276.66 / 279.90, # 0.988
        'spike': 1577.25 / 1588.45,   # 0.993
    }

    print(f"\n  Estimated Network-Safe (RL) Revenue:")
    print(f"  Using RL/DP ratios from representative days:")
    for label, ratio in rl_dp_ratios.items():
        print(f"    {label:>10}: RL/DP = {ratio:.3f}")

    rdf['rl_dp_ratio'] = rdf['bucket'].map(rl_dp_ratios).astype(float)
    rdf['rl_revenue_est'] = rdf['dp_revenue'] * rdf['rl_dp_ratio']

    rl_annual = rdf['rl_revenue_est'].sum()
    dp_annual = rdf['dp_revenue'].sum()
    pypsa_annual = rdf['pypsa_revenue'].sum()
    tou_annual = 81.56 * 365.25

    print(f"\n  {'Method':>35} {'Annual':>12} {'Daily':>10}")
    print(f"  {'-'*35} {'-'*12} {'-'*10}")
    print(f"  {'PyPSA (continuous, unconstrained)':>35} "
          f"A${pypsa_annual:>10,.0f} A${pypsa_annual/len(rdf):>8.2f}")
    print(f"  {'DP (discrete, unconstrained)':>35} "
          f"A${dp_annual:>10,.0f} A${dp_annual/len(rdf):>8.2f}")
    print(f"  {'RL estimated (network-safe)':>35} "
          f"A${rl_annual:>10,.0f} A${rl_annual/len(rdf):>8.2f}")
    print(f"  {'TOU (guaranteed)':>35} "
          f"A${tou_annual:>10,.0f} A${81.56:>8.2f}")

    print(f"\n  Network safety cost: A${dp_annual - rl_annual:,.0f}/year "
          f"({(1 - rl_annual/dp_annual)*100:.1f}% of DP revenue)")

    # ---- Days where PyPSA has 0 violations (already network-safe) ----
    zero_viol = rdf[rdf['pypsa_violations'] == 0]
    print(f"\n  Days with 0 PyPSA violations: {len(zero_viol)} / {len(rdf)}")
    if len(zero_viol) > 0:
        print(f"    Revenue on those days: A${zero_viol['pypsa_revenue'].sum():,.0f} "
              f"({zero_viol['pypsa_revenue'].sum()/pypsa_annual*100:.1f}% of annual)")

    # ---- Top 10 violation days ----
    print(f"\n  Top 10 Highest-Violation Days (PyPSA):")
    print(f"  {'Date':>12} {'Revenue':>10} {'Violations':>10} {'Max Price':>10}")
    top10 = rdf.nlargest(10, 'pypsa_violations')
    for _, row in top10.iterrows():
        print(f"  {row['date']:>12} A${row['pypsa_revenue']:>8.2f} "
              f"{row['pypsa_violations']:>10} A${row['max_price']:>8,.0f}")


def main():
    use_cached = "--cached" in sys.argv

    if use_cached and os.path.exists(OUTPUT_CSV):
        print(f"Loading cached results from {OUTPUT_CSV}")
        rdf = pd.read_csv(OUTPUT_CSV)
    else:
        rdf = run_full_year()

    print_analysis(rdf)


if __name__ == "__main__":
    main()