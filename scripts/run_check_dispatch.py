"""
Check dispatch profiles, violations, and revenue from saved Q-tables.

Loads spot-trained and TOU-trained Q-tables, extracts dispatch, runs
through OpenDSS, and compares against baseline (no battery) and DP.

Outputs are printed to stdout AND saved to docs/dispatch_results.md.

"""

import os
import sys
import numpy as np
from datetime import datetime
from src.dp.battery import Battery
from src.dp.solver import DPSolver
from src.dp.prices import load_day_prices, build_tou_profile
from src.opendss.profiles import generate_load_profile, generate_solar_profile
from src.opendss.feeders import FEEDER_32
from src.integration import timeseries
from src.rl.environment import CommunityBatteryEnv
from src.rl.utils import load_q_table, extract_dispatch


# ============================================================
# Dual-output: print to stdout and write to file
# ============================================================

OUTPUT_FILE = 'docs/dispatch_results.md'
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
_outfile = open(OUTPUT_FILE, 'w')


def log(msg=''):
    """Print to stdout and append to output file."""
    print(msg)
    _outfile.write(msg + '\n')


log(f"# Dispatch Results")
log(f"")
log(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
log(f"")
log(f"Spot prices: AEMO NSW1 typical day (2024-06-28)")
log(f"TOU prices: ActewAGL Home Daytime Economy (from 1 July 2025, GST excl.)")
log(f"")

# ============================================================
# Setup
# ============================================================

spot_prices = load_day_prices('data/aemo/prices_typical_2024-06-28.csv')
tou_prices = build_tou_profile()
load_profile = generate_load_profile()
solar_profile = generate_solar_profile()
dss_file = FEEDER_32['dss_file']
q_table_dir = 'data/q_tables'

configs = [
    {'limit': 50, 'capacity': 200, 'n_actions': 21},
    {'limit': 50, 'capacity': 300, 'n_actions': 21},
    {'limit': 50, 'capacity': 400, 'n_actions': 21},
    {'limit': 80, 'capacity': 200, 'n_actions': 33},
    {'limit': 80, 'capacity': 300, 'n_actions': 33},
    {'limit': 80, 'capacity': 400, 'n_actions': 33},
    {'limit': 100, 'capacity': 200, 'n_actions': 33},
    {'limit': 100, 'capacity': 300, 'n_actions': 33},
    {'limit': 100, 'capacity': 400, 'n_actions': 33},
]


def tou_period_label(t):
    """Return the TOU period name for a given time step."""
    if (t >= 14 and t < 18) or (t >= 34 and t < 42):
        return "Peak"
    elif t >= 22 and t < 30:
        return "Solar"
    else:
        return "Shld"


def load_rl_dispatch(q_file, prices, battery, limit):
    """Load Q-table and extract dispatch. Returns (dispatch, revenue) or None."""
    if not os.path.exists(q_file):
        return None

    Q, meta = load_q_table(q_file)
    env = CommunityBatteryEnv(prices, load_profile, solar_profile,
                              dispatch_limit=limit,
                              violation_penalty=0,
                              battery_kwh=battery.kwh_rated,
                              n_actions=Q.shape[2])
    dispatch = extract_dispatch(Q, env, Q.shape[0])
    revenue = sum(float(battery.reward(dispatch[t], prices[t], 0.5))
                  for t in range(48))
    return {'dispatch': dispatch, 'revenue': revenue, 'q_file': q_file}


def compute_soc_trajectory(dispatch, battery):
    """Compute SoC trajectory from dispatch."""
    soc = np.zeros(49)
    soc[0] = battery.kwh_rated / 2
    for t in range(48):
        soc[t + 1] = float(battery.next_soc(soc[t], dispatch[t], 0.5))
        soc[t + 1] = max(battery.soc_min, min(battery.soc_max, soc[t + 1]))
    return soc


def print_dispatch_profile(label, prices, dispatch, soc, df, summary,
                           revenue, price_type='spot'):
    """Print the dispatch profile with SoC and violations."""
    log(f"\n  {label}")
    log(f"  Revenue: A${revenue:.2f}/day  |  Violations: {summary['violations']}  |  "
          f"V_min: {summary['v_min']:.4f}  |  Losses: {summary['losses_kwh']:.1f} kWh")

    header = (f"\n  {'t':<4} {'Time':<6} {'Price':>7} {'kW':>7} {'SoC':>7} "
              f"{'V_min':>7} {'Viol':>5}")
    sep = (f"  {'--':<4} {'-----':<6} {'-'*7} {'-'*7} {'-'*7} "
           f"{'-'*7} {'-'*5}")
    if price_type == 'tou':
        header += f" {'Period':<6}"
        sep += f" {'-'*6}"
    log(header)
    log(sep)

    for t in range(48):
        h = int(t / 2)
        m = int((t / 2 - h) * 60)
        kw_str = f"{dispatch[t]:+.0f}" if abs(dispatch[t]) > 0.1 else "0"
        viol_mark = "*" if df['violation'].iloc[t] != 'OK' else " "

        line = (f"  {t:<4} {h:02d}:{m:02d}  {prices[t]:>7.1f} {kw_str:>7} "
                f"{soc[t]:>7.1f} {df['v_min'].iloc[t]:>7.4f} {viol_mark:>5}")
        if price_type == 'tou':
            line += f" {tou_period_label(t):<6}"
        log(line)

    log(f"  {'END':<4} {'':6} {'':>7} {'':>7} {soc[48]:>7.1f}")


# ============================================================
# Baseline
# ============================================================

log("=" * 90)
log("  Running baseline (no battery)...")
log("=" * 90)

df_base = timeseries.run(np.zeros(48), load_profile, solar_profile,
                         FEEDER_32, dss_file, battery_enabled=False)
s_base = timeseries.summarise(df_base, "Baseline (no battery)")


# ============================================================
# Process each configuration
# ============================================================

all_results = []

for cfg in configs:
    limit = cfg['limit']
    cap = cfg['capacity']
    n_act = cfg['n_actions']
    label = f"±{limit}kW / {cap}kWh"

    log(f"\n{'='*90}")
    log(f"  CONFIGURATION: {label}")
    log(f"{'='*90}")

    battery = Battery(kwh_rated=cap, kw_rated=100)
    solver = DPSolver(battery, dispatch_limit=limit, n_soc=81, n_actions=n_act)

    # ---- Spot DP ----
    dp_spot = solver.solve(spot_prices, initial_soc=cap / 2)
    df_dp_spot = timeseries.run(dp_spot['dispatch'], load_profile, solar_profile,
                                FEEDER_32, dss_file, battery_enabled=True, battery=battery)
    s_dp_spot = timeseries.summarise(df_dp_spot, f"Spot DP {label}")

    # ---- TOU DP ----
    dp_tou = solver.solve(tou_prices, initial_soc=cap / 2)
    df_dp_tou = timeseries.run(dp_tou['dispatch'], load_profile, solar_profile,
                               FEEDER_32, dss_file, battery_enabled=True, battery=battery)
    s_dp_tou = timeseries.summarise(df_dp_tou, f"TOU DP {label}")

    # ---- Spot RL ----
    rl_spot = load_rl_dispatch(
        os.path.join(q_table_dir, f"Q_phase2_{limit}kW_{cap}kWh.npz"),
        spot_prices, battery, limit)

    rl_spot_summary = None
    if rl_spot:
        df_rl_spot = timeseries.run(rl_spot['dispatch'], load_profile, solar_profile,
                                    FEEDER_32, dss_file, battery_enabled=True, battery=battery)
        rl_spot_summary = timeseries.summarise(df_rl_spot, f"Spot RL {label}")

    # ---- TOU RL ----
    rl_tou = load_rl_dispatch(
        os.path.join(q_table_dir, f"Q_phase2_tou_{limit}kW_{cap}kWh.npz"),
        tou_prices, battery, limit)

    rl_tou_summary = None
    if rl_tou:
        df_rl_tou = timeseries.run(rl_tou['dispatch'], load_profile, solar_profile,
                                   FEEDER_32, dss_file, battery_enabled=True, battery=battery)
        rl_tou_summary = timeseries.summarise(df_rl_tou, f"TOU RL {label}")

    # ---- Comparison table ----
    log(f"\n  {'Method':<20} {'Revenue':>10} {'Viol':>6} {'V_min':>8} "
          f"{'V_max':>8} {'Losses':>8} {'PkTx':>6}")
    log(f"  {'-'*20} {'-'*10} {'-'*6} {'-'*8} "
          f"{'-'*8} {'-'*8} {'-'*6}")
    log(f"  {'Baseline':<20} {'—':>10} {s_base['violations']:>6} "
          f"{s_base['v_min']:>8.4f} {s_base['v_max']:>8.4f} "
          f"{s_base['losses_kwh']:>7.1f} {s_base['peak_tx']:>5.1f}%")
    log(f"  {'Spot DP':<20} A${dp_spot['total_revenue']:>8.2f} "
          f"{s_dp_spot['violations']:>6} {s_dp_spot['v_min']:>8.4f} "
          f"{s_dp_spot['v_max']:>8.4f} {s_dp_spot['losses_kwh']:>7.1f} "
          f"{s_dp_spot['peak_tx']:>5.1f}%")

    if rl_spot:
        log(f"  {'Spot RL':<20} A${rl_spot['revenue']:>8.2f} "
              f"{rl_spot_summary['violations']:>6} {rl_spot_summary['v_min']:>8.4f} "
              f"{rl_spot_summary['v_max']:>8.4f} {rl_spot_summary['losses_kwh']:>7.1f} "
              f"{rl_spot_summary['peak_tx']:>5.1f}%")

    log(f"  {'TOU DP':<20} A${dp_tou['total_revenue']:>8.2f} "
          f"{s_dp_tou['violations']:>6} {s_dp_tou['v_min']:>8.4f} "
          f"{s_dp_tou['v_max']:>8.4f} {s_dp_tou['losses_kwh']:>7.1f} "
          f"{s_dp_tou['peak_tx']:>5.1f}%")

    if rl_tou:
        log(f"  {'TOU RL':<20} A${rl_tou['revenue']:>8.2f} "
              f"{rl_tou_summary['violations']:>6} {rl_tou_summary['v_min']:>8.4f} "
              f"{rl_tou_summary['v_max']:>8.4f} {rl_tou_summary['losses_kwh']:>7.1f} "
              f"{rl_tou_summary['peak_tx']:>5.1f}%")

    # ---- Dispatch profiles (only for configs with violations or interesting differences) ----
    show_profiles = (
        s_dp_spot['violations'] > 0 or
        s_dp_tou['violations'] > 0 or
        (rl_spot and rl_spot_summary['violations'] > 0) or
        (rl_tou and rl_tou_summary['violations'] > 0)
    )

    if show_profiles:
        # Spot DP dispatch profile
        soc_dp_spot = compute_soc_trajectory(dp_spot['dispatch'], battery)
        print_dispatch_profile(
            f"Spot DP — {label}", spot_prices, dp_spot['dispatch'],
            soc_dp_spot, df_dp_spot, s_dp_spot, dp_spot['total_revenue'], 'spot')

        # Spot RL dispatch profile
        if rl_spot:
            soc_rl_spot = compute_soc_trajectory(rl_spot['dispatch'], battery)
            print_dispatch_profile(
                f"Spot RL — {label}", spot_prices, rl_spot['dispatch'],
                soc_rl_spot, df_rl_spot, rl_spot_summary, rl_spot['revenue'], 'spot')

        # TOU DP dispatch profile
        soc_dp_tou = compute_soc_trajectory(dp_tou['dispatch'], battery)
        print_dispatch_profile(
            f"TOU DP — {label}", tou_prices, dp_tou['dispatch'],
            soc_dp_tou, df_dp_tou, s_dp_tou, dp_tou['total_revenue'], 'tou')

        # TOU RL dispatch profile
        if rl_tou:
            soc_rl_tou = compute_soc_trajectory(rl_tou['dispatch'], battery)
            print_dispatch_profile(
                f"TOU RL — {label}", tou_prices, rl_tou['dispatch'],
                soc_rl_tou, df_rl_tou, rl_tou_summary, rl_tou['revenue'], 'tou')

    # Store results
    all_results.append({
        'label': label,
        'limit': limit,
        'capacity': cap,
        'spot_dp_rev': dp_spot['total_revenue'],
        'spot_dp_viol': s_dp_spot['violations'],
        'tou_dp_rev': dp_tou['total_revenue'],
        'tou_dp_viol': s_dp_tou['violations'],
        'spot_rl_rev': rl_spot['revenue'] if rl_spot else None,
        'spot_rl_viol': rl_spot_summary['violations'] if rl_spot_summary else None,
        'tou_rl_rev': rl_tou['revenue'] if rl_tou else None,
        'tou_rl_viol': rl_tou_summary['violations'] if rl_tou_summary else None,
    })


# ============================================================
# Grand summary
# ============================================================

log(f"\n{'='*90}")
log(f"  GRAND SUMMARY: All Configurations")
log(f"{'='*90}")
log(f"\n  Baseline: {s_base['violations']} violations, "
      f"V_min={s_base['v_min']:.4f}, losses={s_base['losses_kwh']:.1f} kWh\n")

log(f"  {'Config':<18} {'Spot DP':>9} {'Viol':>5} {'Spot RL':>9} {'Viol':>5} "
      f"{'TOU DP':>9} {'Viol':>5} {'TOU RL':>9} {'Viol':>5}")
log(f"  {'-'*18} {'-'*9} {'-'*5} {'-'*9} {'-'*5} "
      f"{'-'*9} {'-'*5} {'-'*9} {'-'*5}")

for r in all_results:
    s_rl = f"${r['spot_rl_rev']:.2f}" if r['spot_rl_rev'] is not None else "N/A"
    s_rv = f"{r['spot_rl_viol']}" if r['spot_rl_viol'] is not None else "N/A"
    t_rl = f"${r['tou_rl_rev']:.2f}" if r['tou_rl_rev'] is not None else "N/A"
    t_rv = f"{r['tou_rl_viol']}" if r['tou_rl_viol'] is not None else "N/A"

    log(f"  {r['label']:<18} ${r['spot_dp_rev']:>7.2f} {r['spot_dp_viol']:>5} "
          f"{s_rl:>9} {s_rv:>5} "
          f"${r['tou_dp_rev']:>7.2f} {r['tou_dp_viol']:>5} "
          f"{t_rl:>9} {t_rv:>5}")


# ============================================================
# Annual revenue (violation-free only)
# ============================================================

log(f"\n{'='*90}")
log(f"  ANNUAL REVENUE — VIOLATION-FREE DISPATCHES ONLY (A$/year)")
log(f"{'='*90}")
log(f"\n  {'Config':<18} {'Spot RL':>12} {'TOU RL':>12} {'TOU Advantage':>14}")
log(f"  {'-'*18} {'-'*12} {'-'*12} {'-'*14}")

for r in all_results:
    # Only show if RL achieves 0 violations
    spot_ok = r['spot_rl_viol'] == 0 if r['spot_rl_viol'] is not None else False
    tou_ok = r['tou_rl_viol'] == 0 if r['tou_rl_viol'] is not None else False

    spot_annual = r['spot_rl_rev'] * 365 if spot_ok else 0
    tou_annual = r['tou_rl_rev'] * 365 if tou_ok else 0

    spot_str = f"A${spot_annual:>10,.0f}" if spot_ok else f"{'has viol':>12}"
    tou_str = f"A${tou_annual:>10,.0f}" if tou_ok else f"{'has viol':>12}"

    if spot_ok and tou_ok:
        adv = tou_annual - spot_annual
        adv_str = f"A${adv:>+12,.0f}"
    else:
        adv_str = f"{'—':>14}"

    log(f"  {r['label']:<18} {spot_str} {tou_str} {adv_str}")

log(f"""
  Only dispatches with 0 voltage violations are included.
  Spot RL: Q-tables from data/q_tables/Q_phase2_{{limit}}kW_{{cap}}kWh.npz
  TOU RL:  Q-tables from data/q_tables/Q_phase2_tou_{{limit}}kW_{{cap}}kWh.npz
  TOU annual revenue is guaranteed daily (fixed retail rates).
  Spot annual revenue assumes the same typical day repeated 365 times.
""")

# Close output file
_outfile.close()
print(f"\nResults saved to {OUTPUT_FILE}")