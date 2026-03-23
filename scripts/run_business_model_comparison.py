"""
Compare battery dispatch under two business models:

Model A: Wholesale spot arbitrage — battery trades at NEM spot price
Model B: Behind-the-meter retail arbitrage — battery arbitrages ActewAGL TOU rates

Includes OpenDSS voltage violation check for both dispatch strategies.

"""

import os
import numpy as np
from src.dp.battery import Battery
from src.dp.solver import DPSolver
from src.dp.prices import load_day_prices, build_tou_profile
from src.opendss.profiles import generate_load_profile, generate_solar_profile
from src.opendss.feeders import FEEDER_32
from src.integration.timeseries import run, summarise
from src.rl.utils import load_q_table, extract_dispatch
from src.rl.environment import CommunityBatteryEnv


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
    {'limit': 80, 'capacity': 200, 'n_actions': 33},
    {'limit': 80, 'capacity': 400, 'n_actions': 33},
    {'limit': 100, 'capacity': 400, 'n_actions': 33},
]


# ============================================================
# Price profile comparison
# ============================================================

print("=" * 90)
print("  PRICE PROFILE COMPARISON: NEM Spot vs ActewAGL Retail TOU")
print("=" * 90)
print(f"  {'t':<4} {'Time':<6} {'Spot (A$/MWh)':>14} {'TOU (A$/MWh)':>14} {'TOU Period':<14}")
print(f"  {'--':<4} {'-----':<6} {'-'*14} {'-'*14} {'-'*14}")

for t in range(48):
    h = int(t / 2)
    m = int((t / 2 - h) * 60)

    if (t >= 14 and t < 18) or (t >= 34 and t < 42):
        period = "Peak"
    elif t >= 22 and t < 30:
        period = "Solar soak"
    else:
        period = "Shoulder"

    print(f"  {t:<4} {h:02d}:{m:02d}  {spot_prices[t]:>14.1f} {tou_prices[t]:>14.1f} {period:<14}")

print(f"\n  Spot: min={min(spot_prices):.1f}, max={max(spot_prices):.1f}, "
      f"spread={max(spot_prices)-min(spot_prices):.1f} A$/MWh")
print(f"  TOU:  min={min(tou_prices):.1f}, max={max(tou_prices):.1f}, "
      f"spread={max(tou_prices)-min(tou_prices):.1f} A$/MWh")


# ============================================================
# Run DP and check violations for each configuration
# ============================================================

print(f"\n{'=' * 90}")
print(f"  DP REVENUE AND VIOLATION COMPARISON: Spot vs TOU")
print(f"{'=' * 90}")

all_results = []

for cfg in configs:
    limit = cfg['limit']
    cap = cfg['capacity']
    n_act = cfg['n_actions']
    label = f"±{limit}kW / {cap}kWh"

    print(f"\n  --- {label} ---")

    battery = Battery(kwh_rated=cap, kw_rated=100)
    solver = DPSolver(battery, dispatch_limit=limit, n_soc=81, n_actions=n_act)

    # ---- Spot DP ----
    result_spot = solver.solve(spot_prices, initial_soc=cap / 2)
    df_spot = run(result_spot['dispatch'], load_profile, solar_profile,
                  FEEDER_32, dss_file, battery_enabled=True, battery=battery)
    spot_summary = summarise(df_spot, f"Spot DP {label}")

    # ---- TOU DP ----
    result_tou = solver.solve(tou_prices, initial_soc=cap / 2)
    df_tou = run(result_tou['dispatch'], load_profile, solar_profile,
                 FEEDER_32, dss_file, battery_enabled=True, battery=battery)
    tou_summary = summarise(df_tou, f"TOU DP {label}")

    # ---- RL dispatch: spot-trained Q-table (Model A) ----
    q_file_spot = os.path.join(q_table_dir, f"Q_phase2_{limit}kW_{cap}kWh.npz")
    rl_spot_rev = None
    rl_spot_viol = None
    rl_spot_summary = None

    if os.path.exists(q_file_spot):
        Q_spot, meta = load_q_table(q_file_spot)
        env_spot = CommunityBatteryEnv(spot_prices, load_profile, solar_profile,
                                       dispatch_limit=limit,
                                       violation_penalty=0,
                                       battery_kwh=cap,
                                       n_actions=Q_spot.shape[2])
        rl_spot_dispatch = extract_dispatch(Q_spot, env_spot, Q_spot.shape[0])
        rl_spot_rev = sum(float(battery.reward(rl_spot_dispatch[t], spot_prices[t], 0.5))
                          for t in range(48))
        df_rl_spot = run(rl_spot_dispatch, load_profile, solar_profile,
                         FEEDER_32, dss_file, battery_enabled=True, battery=battery)
        rl_spot_summary = summarise(df_rl_spot, f"RL spot-trained {label}")
        rl_spot_viol = rl_spot_summary['violations']
    else:
        print(f"    Spot Q-table not found: {q_file_spot}")

    # ---- RL dispatch: TOU-trained Q-table (Model B) ----
    q_file_tou = os.path.join(q_table_dir, f"Q_phase2_tou_{limit}kW_{cap}kWh.npz")
    rl_tou_rev = None
    rl_tou_viol = None
    rl_tou_summary = None

    if os.path.exists(q_file_tou):
        Q_tou, meta = load_q_table(q_file_tou)
        env_tou = CommunityBatteryEnv(tou_prices, load_profile, solar_profile,
                                      dispatch_limit=limit,
                                      violation_penalty=0,
                                      battery_kwh=cap,
                                      n_actions=Q_tou.shape[2])
        rl_tou_dispatch = extract_dispatch(Q_tou, env_tou, Q_tou.shape[0])
        rl_tou_rev = sum(float(battery.reward(rl_tou_dispatch[t], tou_prices[t], 0.5))
                         for t in range(48))
        df_rl_tou = run(rl_tou_dispatch, load_profile, solar_profile,
                        FEEDER_32, dss_file, battery_enabled=True, battery=battery)
        rl_tou_summary = summarise(df_rl_tou, f"RL TOU-trained {label}")
        rl_tou_viol = rl_tou_summary['violations']
    else:
        print(f"    TOU Q-table not found: {q_file_tou}")

    # Print per-config comparison
    print(f"\n    {'Method':<25} {'Revenue':>10} {'Violations':>12} {'V_min':>8} {'Losses':>10}")
    print(f"    {'-'*25} {'-'*10} {'-'*12} {'-'*8} {'-'*10}")
    print(f"    {'Spot DP':<25} A${result_spot['total_revenue']:>8.2f} "
          f"{spot_summary['violations']:>12} {spot_summary['v_min']:>8.4f} "
          f"{spot_summary['losses_kwh']:>8.1f}")
    print(f"    {'TOU DP':<25} A${result_tou['total_revenue']:>8.2f} "
          f"{tou_summary['violations']:>12} {tou_summary['v_min']:>8.4f} "
          f"{tou_summary['losses_kwh']:>8.1f}")

    if rl_spot_rev is not None:
        print(f"    {'RL spot-trained':<25} A${rl_spot_rev:>8.2f} "
              f"{rl_spot_viol:>12} {rl_spot_summary['v_min']:>8.4f} "
              f"{rl_spot_summary['losses_kwh']:>8.1f}")
    if rl_tou_rev is not None:
        print(f"    {'RL TOU-trained':<25} A${rl_tou_rev:>8.2f} "
              f"{rl_tou_viol:>12} {rl_tou_summary['v_min']:>8.4f} "
              f"{rl_tou_summary['losses_kwh']:>8.1f}")

    all_results.append({
        'label': label,
        'limit': limit,
        'capacity': cap,
        'spot_dp_rev': result_spot['total_revenue'],
        'spot_dp_viol': spot_summary['violations'],
        'spot_dp_losses': spot_summary['losses_kwh'],
        'tou_dp_rev': result_tou['total_revenue'],
        'tou_dp_viol': tou_summary['violations'],
        'tou_dp_losses': tou_summary['losses_kwh'],
        'rl_spot_rev': rl_spot_rev,
        'rl_spot_viol': rl_spot_viol,
        'rl_tou_rev': rl_tou_rev,
        'rl_tou_viol': rl_tou_viol,
    })


# ============================================================
# Summary table
# ============================================================

print(f"\n{'=' * 90}")
print(f"  SUMMARY: Revenue and Violations across Business Models")
print(f"{'=' * 90}")
print(f"\n  {'Config':<18} {'Spot DP':>9} {'Viol':>5} {'TOU DP':>9} {'Viol':>5} "
      f"{'RL Spot':>9} {'Viol':>5} {'RL TOU':>9} {'Viol':>5}")
print(f"  {'-'*18} {'-'*9} {'-'*5} {'-'*9} {'-'*5} "
      f"{'-'*9} {'-'*5} {'-'*9} {'-'*5}")

for r in all_results:
    rl_s = f"${r['rl_spot_rev']:.2f}" if r['rl_spot_rev'] is not None else "N/A"
    rl_sv = f"{r['rl_spot_viol']}" if r['rl_spot_viol'] is not None else "N/A"
    rl_t = f"${r['rl_tou_rev']:.2f}" if r['rl_tou_rev'] is not None else "N/A"
    rl_tv = f"{r['rl_tou_viol']}" if r['rl_tou_viol'] is not None else "N/A"

    print(f"  {r['label']:<18} ${r['spot_dp_rev']:>7.2f} {r['spot_dp_viol']:>5} "
          f"${r['tou_dp_rev']:>7.2f} {r['tou_dp_viol']:>5} "
          f"{rl_s:>9} {rl_sv:>5} {rl_t:>9} {rl_tv:>5}")


# ============================================================
# Annual revenue comparison
# ============================================================

print(f"\n{'=' * 90}")
print(f"  ANNUAL REVENUE ESTIMATES (A$/year)")
print(f"{'=' * 90}")
print(f"\n  {'Config':<18} {'Spot DP':>12} {'TOU DP':>12} {'RL Spot':>12} {'RL TOU':>12}")
print(f"  {'-'*18} {'-'*12} {'-'*12} {'-'*12} {'-'*12}")

for r in all_results:
    spot_a = r['spot_dp_rev'] * 365
    tou_a = r['tou_dp_rev'] * 365
    rl_spot_a = r['rl_spot_rev'] * 365 if r['rl_spot_rev'] else 0
    rl_tou_a = r['rl_tou_rev'] * 365 if r['rl_tou_rev'] else 0

    print(f"  {r['label']:<18} A${spot_a:>10,.0f} A${tou_a:>10,.0f} "
          f"A${rl_spot_a:>10,.0f} A${rl_tou_a:>10,.0f}")

print(f"""
  Columns:
    Spot DP  = DP at NEM spot prices (Model A, may have violations)
    TOU DP   = DP at ActewAGL TOU rates (Model B, may have violations)
    RL Spot  = RL trained on spot prices (Model A, 0 violations)
    RL TOU   = RL trained on TOU prices (Model B, 0 violations)

  Each RL agent is trained on its own price signal and verified against
  OpenDSS for network feasibility. RL Spot uses Q_phase2_{{limit}}kW_{{cap}}kWh.npz,
  RL TOU uses Q_phase2_tou_{{limit}}kW_{{cap}}kWh.npz.
""")