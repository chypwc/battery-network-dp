"""
Pure DP and RL dispatch on representative days for annual revenue validation.

Runs the DP solver (unconstrained, no feedback) and two-phase Q-learning
(network-safe) on 5 days selected from the PyPSA full-year analysis.
Results are weighted by bucket frequency to estimate annual revenue
at three levels:

    PyPSA  ≥  DP  ≥  RL
    (continuous,   (discrete,      (discrete,
     unconstrained) unconstrained)  network-safe)

Representative days (from PyPSA annual analysis):
    Low:       2024-02-24  (51 days like this,  PyPSA A$4.75)
    Typical:   2024-09-27  (227 days like this, PyPSA A$28.25)
    High:      2024-06-25  (52 days like this,  PyPSA A$61.33)
    Very high: 2024-05-03  (26 days like this,  PyPSA A$269.85)
    Spike:     2024-02-29  (10 days like this,  PyPSA A$1593.72)

Battery: ±100kW / 200kWh (GenCost 2hr spec, matches PyPSA analysis)

Usage:
    python run_representative_days.py
"""

import numpy as np
from src.dp.battery import Battery
from src.dp.solver import DPSolver
from src.dp.prices import load_day_prices
from src.opendss.profiles import generate_load_profile, generate_solar_profile
from src.opendss.feeders import FEEDER_32
from src.integration import timeseries
from src.rl.environment import CommunityBatteryEnv
from src.rl.q_learning import train_two_phase
from src.rl.utils import extract_dispatch, print_training_summary


# ============================================================
# Configuration — matches PyPSA analysis exactly
# ============================================================

DISPATCH_LIMIT = 100   # kW
CAPACITY = 200         # kWh
INITIAL_SOC = 100      # kWh (50%)

# Representative days: (label, date, csv_path, bucket_days, pypsa_revenue)
REPRESENTATIVE_DAYS = [
    ("low",       "2024-02-24", "data/aemo/prices_low_2024-02-24.csv",       51,    4.75),
    ("typical",   "2024-09-27", "data/aemo/prices_typical_2024-09-27.csv",  227,   28.25),
    ("high",      "2024-06-25", "data/aemo/prices_high_2024-06-25.csv",      52,   61.33),
    ("very_high", "2024-05-03", "data/aemo/prices_very_high_2024-05-03.csv", 26,  269.85),
    ("spike",     "2024-02-29", "data/aemo/prices_spike_2024-02-29.csv",     10, 1593.72),
]

# Q-learning hyperparameters — tuned for ±100kW config
N_SOC_BINS = 100
N_ACTIONS = 33
N_PHASE1 = 50000
N_PHASE2 = 100000
# PHASE2_PENALTY = 10.0
EPSILON_START = 0.3
EPSILON_END = 0.001


# ============================================================
# Shared setup
# ============================================================

load_profile = generate_load_profile()
solar_profile = generate_solar_profile()
dss_file = FEEDER_32['dss_file']
battery = Battery(kwh_rated=CAPACITY, kw_rated=100)

def get_phase2_penalty(prices):
    """
    Scale the violation penalty to the day's price level.

    The penalty must be large enough that no single violation is
    worth the revenue gained. A violation occurs when the battery
    dispatches too aggressively during a high-price period, so
    the temptation is proportional to the peak price.

    Rule: penalty = 10% of daily price spread, minimum A$5.
    This ensures:
      - Low day (spread A$126):   penalty ≈ A$12.6
      - Typical day (spread A$213): penalty ≈ A$21.3
      - High day (spread A$270):  penalty ≈ A$27.0
      - Very high (spread A$4977): penalty ≈ A$497.7
      - Spike (spread A$13292):   penalty ≈ A$1329.2

    At each violated period, the agent loses this amount — more than
    it could gain from one period of aggressive dispatch.
    """
    spread = prices.max() - prices.min()
    return max(5.0, spread * 0.10)


def run_day(label, date, csv_path, bucket_days, pypsa_revenue):
    """
    Run pure DP (unconstrained) and RL (network-safe) on one day.

    Pure DP: solves backward induction for optimal dispatch.
    No feedback loop, no OpenDSS — same problem as PyPSA but with
    discrete actions. Revenue should be close to PyPSA.

    RL: two-phase Q-learning. Phase 1 learns arbitrage (no network).
    Phase 2 adds OpenDSS voltage penalties. The converged policy
    avoids all violations while maximising revenue.
    """
    print(f"\n{'='*80}")
    print(f"  {label.upper()} DAY: {date}")
    print(f"  Bucket: {bucket_days} days/year  |  PyPSA: A${pypsa_revenue:.2f}")
    print(f"{'='*80}")

    prices = load_day_prices(csv_path)
    print(f"  Prices: A${prices.min():.0f} to A${prices.max():.0f}/MWh "
          f"(spread A${prices.max() - prices.min():.0f})")

    # Scale penalty to price level
    penalty = get_phase2_penalty(prices)
    print(f"  Phase 2 penalty: A${penalty:.1f} per violation")

    # ---- Pure DP (unconstrained) ----
    print(f"\n  --- Pure DP (no network, discrete actions) ---")

    solver = DPSolver(battery, dispatch_limit=DISPATCH_LIMIT,
                      n_soc=81, n_actions=N_ACTIONS)
    dp_result = solver.solve(prices, initial_soc=INITIAL_SOC)
    dp_dispatch = dp_result['dispatch']
    dp_revenue = dp_result['total_revenue']

    # Run OpenDSS to count violations (for reporting only)
    df_dp = timeseries.run(
        dp_dispatch, load_profile, solar_profile,
        FEEDER_32, dss_file, battery_enabled=True, battery=battery)
    s_dp = timeseries.summarise(df_dp, f"DP {label}")

    print(f"  Revenue: A${dp_revenue:.2f}  |  Violations: {s_dp['violations']}  |  "
          f"V range: [{s_dp['v_min']:.4f}, {s_dp['v_max']:.4f}]")

    # ---- RL two-phase Q-learning ----
    print(f"\n  --- Q-Learning Two-Phase (warm-started from DP) ---")

    env_phase1 = CommunityBatteryEnv(
        prices, load_profile, solar_profile,
        dispatch_limit=DISPATCH_LIMIT,
        violation_penalty=0.0,
        battery_kwh=CAPACITY,
        n_actions=N_ACTIONS,
        skip_network=True)

    env_phase2 = CommunityBatteryEnv(
        prices, load_profile, solar_profile,
        dispatch_limit=DISPATCH_LIMIT,
        violation_penalty=penalty,
        battery_kwh=CAPACITY,
        n_actions=N_ACTIONS,
        skip_network=False)

    Q, history = train_two_phase(
        env_phase1, env_phase2,
        dp_result=dp_result,
        n_phase1=N_PHASE1, n_phase2=N_PHASE2,
        n_soc_bins=N_SOC_BINS,
        epsilon_start=EPSILON_START, epsilon_end=EPSILON_END,
        save_dir='data/q_tables',
        label=f"repr_{label}_{DISPATCH_LIMIT}kW_{CAPACITY}kWh")

    print(f"\n  Phase 2 training (last 10k episodes):")
    print_training_summary(history[-10000:])

    # Extract RL dispatch and compute revenue
    rl_dispatch = extract_dispatch(Q, env_phase2, N_SOC_BINS)
    rl_revenue = sum(float(battery.reward(rl_dispatch[t], prices[t], 0.5))
                     for t in range(48))

    df_rl = timeseries.run(
        rl_dispatch, load_profile, solar_profile,
        FEEDER_32, dss_file, battery_enabled=True, battery=battery)
    s_rl = timeseries.summarise(df_rl, f"RL {label}")

    print(f"  Revenue: A${rl_revenue:.2f}  |  Violations: {s_rl['violations']}  |  "
          f"V range: [{s_rl['v_min']:.4f}, {s_rl['v_max']:.4f}]")

    return {
        'label': label,
        'date': date,
        'bucket_days': bucket_days,
        'prices': prices,
        'pypsa_revenue': pypsa_revenue,
        'dp_revenue': dp_revenue,
        'dp_violations': s_dp['violations'],
        'dp_v_min': s_dp['v_min'],
        'dp_v_max': s_dp['v_max'],
        'dp_losses': s_dp['losses_kwh'],
        'dp_dispatch': dp_dispatch.copy(),
        'rl_revenue': rl_revenue,
        'rl_violations': s_rl['violations'],
        'rl_v_min': s_rl['v_min'],
        'rl_v_max': s_rl['v_max'],
        'rl_losses': s_rl['losses_kwh'],
        'rl_dispatch': rl_dispatch.copy(),
    }


def print_dispatch_profile(r, prices):
    """Print side-by-side DP vs RL dispatch profile for one day."""
    label = r['label']
    dp_d = r['dp_dispatch']
    rl_d = r['rl_dispatch']

    # Compute SoC trajectories
    dp_soc = np.zeros(49)
    rl_soc = np.zeros(49)
    dp_soc[0] = INITIAL_SOC
    rl_soc[0] = INITIAL_SOC

    for t in range(48):
        dp_soc[t + 1] = float(battery.next_soc(dp_soc[t], dp_d[t], 0.5))
        dp_soc[t + 1] = max(battery.soc_min, min(battery.soc_max, dp_soc[t + 1]))
        rl_soc[t + 1] = float(battery.next_soc(rl_soc[t], rl_d[t], 0.5))
        rl_soc[t + 1] = max(battery.soc_min, min(battery.soc_max, rl_soc[t + 1]))

    print(f"\n{'='*90}")
    print(f"  DISPATCH PROFILE: {label.upper()} DAY ({r['date']})")
    print(f"  DP: A${r['dp_revenue']:.2f}/day, {r['dp_violations']} violations")
    print(f"  RL: A${r['rl_revenue']:.2f}/day, {r['rl_violations']} violations")
    print(f"{'='*90}")
    print(f"  {'t':<4} {'Time':<6} {'Price':>7}  {'DP kW':>7} {'DP SoC':>7}  "
          f"{'RL kW':>7} {'RL SoC':>7}  {'Diff':>6}")
    print(f"  {'--':<4} {'-----':<6} {'------':>7}  {'-'*7} {'-'*7}  "
          f"{'-'*7} {'-'*7}  {'-'*6}")

    for t in range(48):
        h = t // 2
        m = (t % 2) * 30
        dp_str = f"{dp_d[t]:+.0f}" if abs(dp_d[t]) > 0.1 else "0"
        rl_str = f"{rl_d[t]:+.0f}" if abs(rl_d[t]) > 0.1 else "0"
        diff = rl_d[t] - dp_d[t]
        diff_str = f"{diff:+.0f}" if abs(diff) > 0.1 else ""
        print(f"  {t:<4} {h:02d}:{m:02d}  ${prices[t]:>6.1f}  {dp_str:>7} {dp_soc[t]:>7.1f}  "
              f"{rl_str:>7} {rl_soc[t]:>7.1f}  {diff_str:>6}")

    print(f"  {'END':<4} {'':6} {'':>7}  {'':>7} {dp_soc[48]:>7.1f}  "
          f"{'':>7} {rl_soc[48]:>7.1f}")
    print(f"  Revenue gap: A${r['dp_revenue'] - r['rl_revenue']:.2f}/day "
          f"({(1 - r['rl_revenue']/r['dp_revenue'])*100:.1f}% cost of network safety)")


def main():
    print("=" * 80)
    print("  Representative Day Analysis: Pure DP + RL on 5 Price Regimes")
    print(f"  Battery: ±{DISPATCH_LIMIT}kW / {CAPACITY}kWh (GenCost 2hr spec)")
    print(f"  Solver hierarchy: PyPSA (continuous LP) ≥ DP (discrete) ≥ RL (network-safe)")
    print("=" * 80)

    # ---- Baseline (no battery) ----
    df_base = timeseries.run(
        np.zeros(48), load_profile, solar_profile,
        FEEDER_32, dss_file, battery_enabled=False)
    s_base = timeseries.summarise(df_base, "Baseline")
    print(f"\n  Baseline (no battery): {s_base['violations']} violations, "
          f"V range: [{s_base['v_min']:.4f}, {s_base['v_max']:.4f}]")

    # ---- Run all representative days ----
    results = []
    for label, date, csv_path, bucket_days, pypsa_rev in REPRESENTATIVE_DAYS:
        r = run_day(label, date, csv_path, bucket_days, pypsa_rev)
        results.append(r)

    # ============================================================
    # Summary Table
    # ============================================================
    print(f"\n{'='*100}")
    print(f"  SUMMARY: Three-Level Revenue Comparison (±{DISPATCH_LIMIT}kW / {CAPACITY}kWh)")
    print(f"{'='*100}")
    print(f"  {'Label':>10} {'Date':>12} {'Days':>5} "
          f"{'PyPSA':>9} {'DP':>9} {'DP Viol':>7} "
          f"{'RL':>9} {'RL Viol':>7} {'RL/PyPSA':>8}")
    print(f"  {'-'*10} {'-'*12} {'-'*5} "
          f"{'-'*9} {'-'*9} {'-'*7} "
          f"{'-'*9} {'-'*7} {'-'*8}")

    for r in results:
        ratio = r['rl_revenue'] / r['pypsa_revenue'] if r['pypsa_revenue'] > 0 else 0
        print(f"  {r['label']:>10} {r['date']:>12} {r['bucket_days']:>5} "
              f"A${r['pypsa_revenue']:>7.2f} A${r['dp_revenue']:>7.2f} {r['dp_violations']:>7} "
              f"A${r['rl_revenue']:>7.2f} {r['rl_violations']:>7} {ratio:>7.1%}")

    # ============================================================
    # Weighted Annual Revenue Estimates
    # ============================================================
    total_days = sum(r['bucket_days'] for r in results)
    pypsa_annual = sum(r['bucket_days'] * r['pypsa_revenue'] for r in results)
    dp_annual = sum(r['bucket_days'] * r['dp_revenue'] for r in results)
    rl_annual = sum(r['bucket_days'] * r['rl_revenue'] for r in results)

    print(f"\n{'='*100}")
    print(f"  WEIGHTED ANNUAL REVENUE ESTIMATES ({total_days} days)")
    print(f"{'='*100}")
    print(f"\n  {'Method':>30} {'Wtd Daily':>10} {'Annual':>12} {'vs PyPSA':>10}")
    print(f"  {'-'*30} {'-'*10} {'-'*12} {'-'*10}")
    print(f"  {'PyPSA (continuous LP)':>30} A${pypsa_annual/total_days:>8.2f} "
          f"A${pypsa_annual:>10,.0f} {'—':>10}")
    print(f"  {'DP (discrete, unconstrained)':>30} A${dp_annual/total_days:>8.2f} "
          f"A${dp_annual:>10,.0f} {dp_annual/pypsa_annual:>9.1%}")
    print(f"  {'RL (discrete, network-safe)':>30} A${rl_annual/total_days:>8.2f} "
          f"A${rl_annual:>10,.0f} {rl_annual/pypsa_annual:>9.1%}")

    # ---- Per-bucket breakdown ----
    print(f"\n  Per-Bucket Annual Contribution:")
    print(f"  {'Bucket':>10} {'Days':>5} "
          f"{'PyPSA':>10} {'DP':>10} {'RL':>10} {'RL/PyPSA':>8}")
    print(f"  {'-'*10} {'-'*5} {'-'*10} {'-'*10} {'-'*10} {'-'*8}")

    for r in results:
        pc = r['bucket_days'] * r['pypsa_revenue']
        dc = r['bucket_days'] * r['dp_revenue']
        rc = r['bucket_days'] * r['rl_revenue']
        ratio = rc / pc if pc > 0 else 0
        print(f"  {r['label']:>10} {r['bucket_days']:>5} "
              f"A${pc:>8,.0f} A${dc:>8,.0f} A${rc:>8,.0f} {ratio:>7.1%}")

    print(f"  {'TOTAL':>10} {total_days:>5} "
          f"A${pypsa_annual:>8,.0f} A${dp_annual:>8,.0f} A${rl_annual:>8,.0f} "
          f"{rl_annual/pypsa_annual:>7.1%}")

    # ---- TOU comparison ----
    tou_daily = 81.56
    tou_annual = tou_daily * 365.25

    print(f"\n{'='*100}")
    print(f"  SPOT vs TOU: ANNUAL REVENUE COMPARISON")
    print(f"{'='*100}")
    print(f"\n  {'Scenario':>35} {'Annual':>12} {'Daily':>10}")
    print(f"  {'-'*35} {'-'*12} {'-'*10}")
    print(f"  {'Spot — PyPSA full year (366 days)':>35} A${36190:>10,.0f} A${98.88:>8.2f}")
    print(f"  {'Spot — PyPSA weighted (5 days)':>35} A${pypsa_annual:>10,.0f} "
          f"A${pypsa_annual/total_days:>8.2f}")
    print(f"  {'Spot — DP weighted':>35} A${dp_annual:>10,.0f} "
          f"A${dp_annual/total_days:>8.2f}")
    print(f"  {'Spot — RL network-safe weighted':>35} A${rl_annual:>10,.0f} "
          f"A${rl_annual/total_days:>8.2f}")
    print(f"  {'TOU — guaranteed daily':>35} A${tou_annual:>10,.0f} A${tou_daily:>8.2f}")

    # ---- Violation summary ----
    print(f"\n  Violation Summary:")
    for r in results:
        status_dp = "✓" if r['dp_violations'] == 0 else f"✗ ({r['dp_violations']})"
        status_rl = "✓" if r['rl_violations'] == 0 else f"✗ ({r['rl_violations']})"
        print(f"    {r['label']:>10} ({r['date']}):  DP {status_dp:<8}  RL {status_rl:<8}")

    # ---- Revenue cost of network safety ----
    print(f"\n  Revenue Cost of Network Safety (DP → RL):")
    for r in results:
        gap = r['dp_revenue'] - r['rl_revenue']
        pct = gap / r['dp_revenue'] * 100 if r['dp_revenue'] > 0 else 0
        print(f"    {r['label']:>10}: A${gap:>+8.2f}/day ({pct:>+5.1f}%)")

    gap_annual = dp_annual - rl_annual
    pct_annual = gap_annual / dp_annual * 100 if dp_annual > 0 else 0
    print(f"    {'ANNUAL':>10}: A${gap_annual:>+8,.0f}/year ({pct_annual:>+5.1f}%)")

    # ============================================================
    # Dispatch Profiles — only for days with meaningful differences
    # ============================================================
    for r in results:
        # Show profile if DP has violations or revenue gap > A$1
        if r['dp_violations'] > 0 or abs(r['dp_revenue'] - r['rl_revenue']) > 1.0:
            print_dispatch_profile(r, r['prices'])


if __name__ == "__main__":
    main()