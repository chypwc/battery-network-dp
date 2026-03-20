"""
Compare Branch A (with battery) vs Branch B (without battery) voltages.

Loads saved Q-tables from data/q_tables/ and runs the extracted dispatch
through OpenDSS using timeseries.run(), recording per-bus voltages.

Usage:
    python run_branch_comparison.py
"""

import os
import numpy as np
from src.dp.battery import Battery
from src.dp.solver import DPSolver
from src.dp.prices import load_day_prices
from src.opendss.profiles import generate_load_profile, generate_solar_profile
from src.opendss.feeders import FEEDER_32
from src.integration.timeseries import run, summarise
from src.rl.environment import CommunityBatteryEnv
from src.rl.utils import load_q_table, extract_dispatch


# ============================================================
# Setup
# ============================================================

prices = load_day_prices('data/aemo/prices_typical_2024-06-28.csv')
load_profile = generate_load_profile()
solar_profile = generate_solar_profile()
dss_file = FEEDER_32['dss_file']
q_table_dir = 'data/q_tables'

# End-of-branch buses for comparison
A4_BUS = 'bra4'
B4_BUS = 'brb4'


def run_and_extract(dispatch, battery, label):
    """Run dispatch through OpenDSS and extract A4/B4 voltages."""
    df = run(dispatch, load_profile, solar_profile,
             FEEDER_32, dss_file,
             battery_enabled=(battery is not None),
             battery=battery)

    summary = summarise(df, label)

    # Extract per-bus min-phase voltages from the DataFrame
    # timeseries.run() stores bus voltages as v_{busname} columns (averages)
    v_a4 = df[f'v_{A4_BUS}'].values if f'v_{A4_BUS}' in df.columns else np.ones(48)
    v_b4 = df[f'v_{B4_BUS}'].values if f'v_{B4_BUS}' in df.columns else np.ones(48)

    return {
        'df': df,
        'summary': summary,
        'v_a4': v_a4,
        'v_b4': v_b4,
        'v_min': df['v_min'].values,
        'v_max': df['v_max'].values,
        'violations': summary['violations'],
        'losses_kwh': summary['losses_kwh'],
    }


def print_voltage_comparison(baseline, dp_result, rl_result, config_label):
    """Print side-by-side voltage comparison for A4 vs B4."""

    print(f"\n{'='*100}")
    print(f"  BRANCH COMPARISON: {config_label}")
    print(f"  A4 = end of Branch A (with battery), B4 = end of Branch B (no battery)")
    print(f"{'='*100}")
    print(f"  {'t':<4} {'Time':<6}  {'---Baseline---':^16}  "
          f"{'------DP-------':^16}  {'------RL-------':^16}  "
          f"{'--Improvement--':^16}")
    print(f"  {'':4} {'':6}  {'A4':>7} {'B4':>7}  "
          f"{'A4':>7} {'B4':>7}  {'A4':>7} {'B4':>7}  "
          f"{'A4':>7} {'B4':>7}")
    print(f"  {'--':<4} {'-----':<6}  {'-'*7} {'-'*7}  "
          f"{'-'*7} {'-'*7}  {'-'*7} {'-'*7}  "
          f"{'-'*7} {'-'*7}")

    for t in range(48):
        h = int(t / 2)
        m = int((t / 2 - h) * 60)

        ba4 = baseline['v_a4'][t]
        bb4 = baseline['v_b4'][t]
        da4 = dp_result['v_a4'][t]
        db4 = dp_result['v_b4'][t]
        ra4 = rl_result['v_a4'][t]
        rb4 = rl_result['v_b4'][t]

        imp_a4 = ra4 - ba4
        imp_b4 = rb4 - bb4

        base_flag = '*' if ba4 < 0.94 or bb4 < 0.94 else ' '
        dp_flag = '*' if da4 < 0.94 or db4 < 0.94 else ' '
        rl_flag = '*' if ra4 < 0.94 or rb4 < 0.94 else ' '

        print(f"  {t:<4} {h:02d}:{m:02d} {base_flag}"
              f" {ba4:>7.4f} {bb4:>7.4f} {dp_flag}"
              f" {da4:>7.4f} {db4:>7.4f} {rl_flag}"
              f" {ra4:>7.4f} {rb4:>7.4f} "
              f" {imp_a4:>+7.4f} {imp_b4:>+7.4f}")

    print(f"\n  * = at least one bus below 0.94 pu")

    # Summary
    base_a4_viol = sum(1 for v in baseline['v_a4'] if v < 0.94)
    base_b4_viol = sum(1 for v in baseline['v_b4'] if v < 0.94)
    dp_a4_viol = sum(1 for v in dp_result['v_a4'] if v < 0.94)
    dp_b4_viol = sum(1 for v in dp_result['v_b4'] if v < 0.94)
    rl_a4_viol = sum(1 for v in rl_result['v_a4'] if v < 0.94)
    rl_b4_viol = sum(1 for v in rl_result['v_b4'] if v < 0.94)

    print(f"\n  {'Metric':<30} {'Baseline':>10} {'DP':>10} {'RL':>10}")
    print(f"  {'-'*30} {'-'*10} {'-'*10} {'-'*10}")
    print(f"  {'A4 violations (V<0.94)':<30} {base_a4_viol:>10} {dp_a4_viol:>10} {rl_a4_viol:>10}")
    print(f"  {'B4 violations (V<0.94)':<30} {base_b4_viol:>10} {dp_b4_viol:>10} {rl_b4_viol:>10}")
    print(f"  {'A4 min voltage (pu)':<30} {min(baseline['v_a4']):>10.4f} "
          f"{min(dp_result['v_a4']):>10.4f} {min(rl_result['v_a4']):>10.4f}")
    print(f"  {'B4 min voltage (pu)':<30} {min(baseline['v_b4']):>10.4f} "
          f"{min(dp_result['v_b4']):>10.4f} {min(rl_result['v_b4']):>10.4f}")
    print(f"  {'A4 avg voltage (pu)':<30} {np.mean(baseline['v_a4']):>10.4f} "
          f"{np.mean(dp_result['v_a4']):>10.4f} {np.mean(rl_result['v_a4']):>10.4f}")
    print(f"  {'B4 avg voltage (pu)':<30} {np.mean(baseline['v_b4']):>10.4f} "
          f"{np.mean(dp_result['v_b4']):>10.4f} {np.mean(rl_result['v_b4']):>10.4f}")
    print(f"  {'Total losses (kWh)':<30} {baseline['losses_kwh']:>10.1f} "
          f"{dp_result['losses_kwh']:>10.1f} {rl_result['losses_kwh']:>10.1f}")

    # Battery effect on Branch B
    print(f"\n  Battery effect on Branch B (no battery on this branch):")
    b4_improvement = np.mean(rl_result['v_b4']) - np.mean(baseline['v_b4'])
    b4_viol_reduction = base_b4_viol - rl_b4_viol
    print(f"    Avg voltage lift at B4:  {b4_improvement:+.4f} pu")
    print(f"    Violations eliminated:   {b4_viol_reduction} of {base_b4_viol}")
    if base_b4_viol > 0 and rl_b4_viol > 0:
        print(f"    → Battery on Branch A provides partial but insufficient support to Branch B")
    elif base_b4_viol > 0 and rl_b4_viol == 0:
        print(f"    → Battery on Branch A fully protects Branch B through junction voltage rise")
    else:
        print(f"    → Branch B has no baseline violations")


# ============================================================
# Configurations to compare
# ============================================================

configs = [
    {'limit': 50, 'capacity': 200},
    {'limit': 80, 'capacity': 200},
    {'limit': 80, 'capacity': 400},
    {'limit': 100, 'capacity': 400},
]


# ============================================================
# Run baseline (no battery)
# ============================================================

print("=" * 100)
print("  Running baseline (no battery)...")
print("=" * 100)
baseline = run_and_extract(np.zeros(48), battery=None, label="Baseline")
print(f"  Baseline: {baseline['violations']} violation periods, "
      f"{baseline['losses_kwh']:.1f} kWh losses")


# ============================================================
# Run each configuration
# ============================================================

cross_config_results = []

for cfg in configs:
    limit = cfg['limit']
    cap = cfg['capacity']
    label = f"±{limit}kW / {cap}kWh"

    print(f"\n{'='*100}")
    print(f"  Processing {label}")
    print(f"{'='*100}")

    battery = Battery(kwh_rated=cap, kw_rated=100)

    # ---- DP dispatch ----
    n_actions = 33 if limit >= 80 else 21
    solver = DPSolver(battery, dispatch_limit=limit, n_soc=81, n_actions=n_actions)
    dp_result_solver = solver.solve(prices, initial_soc=cap / 2)
    print(f"  DP revenue: ${dp_result_solver['total_revenue']:.2f}")

    dp_voltages = run_and_extract(dp_result_solver['dispatch'], battery, f"DP {label}")
    print(f"  DP: {dp_voltages['violations']} violation periods")

    # ---- RL dispatch (from saved Q-table) ----
    q_file = os.path.join(q_table_dir, f"Q_phase2_{limit}kW_{cap}kWh.npz")

    if os.path.exists(q_file):
        Q, meta = load_q_table(q_file)
        n_soc_bins = Q.shape[0]

        env = CommunityBatteryEnv(prices, load_profile, solar_profile,
                                  dispatch_limit=limit,
                                  violation_penalty=0,
                                  battery_kwh=cap,
                                  n_actions=Q.shape[2])

        rl_dispatch = extract_dispatch(Q, env, n_soc_bins)
        rl_revenue = sum(float(battery.reward(rl_dispatch[t], prices[t], 0.5))
                         for t in range(48))
        print(f"  RL revenue: ${rl_revenue:.2f}")

        rl_voltages = run_and_extract(rl_dispatch, battery, f"RL {label}")
        print(f"  RL: {rl_voltages['violations']} violation periods")
    else:
        print(f"  Q-table not found: {q_file}")
        print(f"  Using DP dispatch as RL placeholder")
        rl_voltages = dp_voltages

    # ---- Print comparison ----
    print_voltage_comparison(baseline, dp_voltages, rl_voltages, label)

    cross_config_results.append({
        'label': label,
        'rl_a4_viol': sum(1 for v in rl_voltages['v_a4'] if v < 0.94),
        'rl_b4_viol': sum(1 for v in rl_voltages['v_b4'] if v < 0.94),
    })


# ============================================================
# Cross-configuration summary
# ============================================================

base_a4_viol = sum(1 for v in baseline['v_a4'] if v < 0.94)
base_b4_viol = sum(1 for v in baseline['v_b4'] if v < 0.94)

print(f"\n{'='*100}")
print(f"  CROSS-CONFIGURATION SUMMARY: Branch A vs Branch B")
print(f"{'='*100}")
print(f"\n  Baseline: A4 has {base_a4_viol} violations, "
      f"B4 has {base_b4_viol} violations")
print(f"  (A4 and B4 are symmetric — identical violations without battery)\n")
print(f"  {'Config':<20} {'A4 Viol':>8} {'B4 Viol':>8} {'A4 fixed':>9} {'B4 fixed':>9}")
print(f"  {'-'*20} {'-'*8} {'-'*8} {'-'*9} {'-'*9}")

for r in cross_config_results:
    a4_fixed = f"{base_a4_viol - r['rl_a4_viol']}/{base_a4_viol}"
    b4_fixed = f"{base_b4_viol - r['rl_b4_viol']}/{base_b4_viol}"
    print(f"  {r['label']:<20} {r['rl_a4_viol']:>8} {r['rl_b4_viol']:>8} "
          f"{a4_fixed:>9} {b4_fixed:>9}")