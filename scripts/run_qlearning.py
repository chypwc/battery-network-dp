import numpy as np
from src.dp.battery import Battery
from src.dp.solver import DPSolver
from src.dp.prices import load_day_prices
from src.opendss.profiles import generate_load_profile, generate_solar_profile
from src.opendss.feeders import FEEDER_32
from src.integration import timeseries
from src.rl.environment import CommunityBatteryEnv
from src.rl.q_learning import train, train_two_phase
from src.rl.utils import initialise_q_from_dp_value, extract_dispatch, print_training_summary

# ---- Setup ----
prices = load_day_prices('data/aemo/prices_typical_2024-06-28.csv')
load_profile = generate_load_profile()
solar_profile = generate_solar_profile()
dss_file = FEEDER_32['dss_file']

# Q-learning hyperparameters
n_soc_bins = 80
n_actions = 21
n_phase1 = 50000
n_phase2 = 50000
epsilon_start = 0.3
epsilon_end = 0.005
phase2_penalty = 5.0

# ---- Sensitivity grid ----
dispatch_limits = [50, 80, 100]
capacities = [200, 300, 400]
all_results = []

for limit in dispatch_limits:
    for cap in capacities:
        
        if limit == 80:
            n_actions = 33
            n_soc_bins = 80
            phase2_penalty = 5.0
            # n_phase1 = 50000      
            n_phase2 = 80000
            epsilon_start = 0.3
            epsilon_end = 0.001
        elif limit == 100:
            n_actions = 33
            n_soc_bins = 120 if cap >= 400 else 100
            phase2_penalty = 10.0
            # n_phase1 = 50000
            n_phase2 = 100000
            epsilon_start = 0.3
            epsilon_end = 0.001

        print(f"\n{'='*70}")
        print(f"  ±{limit} kW dispatch, {cap} kWh capacity")
        print(f"{'='*70}")

        battery = Battery(kwh_rated=cap, kw_rated=100)
        initial_soc = cap / 2

        # ---- DP ----
        print(f"\n  --- DP Solver ---")
        solver = DPSolver(battery, dispatch_limit=limit, n_soc=81, n_actions=n_actions)
        dp_result = solver.solve(prices, initial_soc=initial_soc)
        dp_dispatch = dp_result['dispatch']
        print(f"  Revenue: ${dp_result['total_revenue']:.2f}")

        df_dp = timeseries.run(dp_dispatch, load_profile, solar_profile,
                               FEEDER_32, dss_file, battery_enabled=True, battery=battery)
        s_dp = timeseries.summarise(df_dp, f"DP ±{limit}kW {cap}kWh")

        # ---- Q-Learning (two-phase) ----
        print(f"\n  --- Q-Learning (two-phase, warm-started from DP) ---")

        env_phase1 = CommunityBatteryEnv(prices, load_profile, solar_profile,
                                          dispatch_limit=limit,
                                          violation_penalty=0.0,
                                          battery_kwh=cap,
                                          n_actions=n_actions,
                                          skip_network=True)

        env_phase2 = CommunityBatteryEnv(prices, load_profile, solar_profile,
                                          dispatch_limit=limit,
                                          violation_penalty=phase2_penalty,
                                          battery_kwh=cap,
                                          n_actions=n_actions,
                                          skip_network=False)


        Q, history = train_two_phase(
            env_phase1, env_phase2,
            dp_result=dp_result,
            n_phase1=n_phase1, n_phase2=n_phase2,
            n_soc_bins=n_soc_bins,
            epsilon_start=epsilon_start, epsilon_end=epsilon_end,
            save_dir='data/q_tables',
            label=f"{limit}kW_{cap}kWh")

        print(f"\n  Phase 2 training summary:")
        print_training_summary(history[-n_phase2:])

        # Extract RL dispatch
        rl_dispatch = extract_dispatch(Q, env_phase2, n_soc_bins)
        rl_revenue = sum(float(battery.reward(rl_dispatch[t], prices[t], 0.5))
                         for t in range(48))

        # RL network check
        df_rl = timeseries.run(rl_dispatch, load_profile, solar_profile,
                               FEEDER_32, dss_file, battery_enabled=True, battery=battery)
        s_rl = timeseries.summarise(df_rl, f"RL ±{limit}kW {cap}kWh")

        all_results.append({
            'limit': limit,
            'capacity': cap,
            'dp_revenue': dp_result['total_revenue'],
            'dp_violations': s_dp['violations'],
            'dp_losses': s_dp['losses_kwh'],
            'dp_peak_tx': s_dp['peak_tx'],
            'dp_v_min': s_dp['v_min'],
            'dp_v_max': s_dp['v_max'],
            'rl_revenue': rl_revenue,
            'rl_violations': s_rl['violations'],
            'rl_losses': s_rl['losses_kwh'],
            'rl_peak_tx': s_rl['peak_tx'],
            'rl_v_min': s_rl['v_min'],
            'rl_v_max': s_rl['v_max'],
            'dp_dispatch': dp_dispatch.copy(),
            'rl_dispatch': rl_dispatch.copy(),
        })

# ---- Baseline ----
df_base = timeseries.run(np.zeros(48), load_profile, solar_profile,
                         FEEDER_32, dss_file, battery_enabled=False)
s_base = timeseries.summarise(df_base, "No Battery")

# ============================================================
# Summary Tables
# ============================================================

print(f"\n{'='*90}")
print(f"  DP vs Q-LEARNING: HEAD-TO-HEAD COMPARISON")
print(f"{'='*90}")
print(f"  {'Config':<15} {'DP Rev':>8} {'DP Viol':>8} {'DP Loss':>8} "
      f"{'RL Rev':>8} {'RL Viol':>8} {'RL Loss':>8}")
print(f"  {'-'*15} {'-'*8} {'-'*8} {'-'*8} "
      f"{'-'*8} {'-'*8} {'-'*8}")
print(f"  {'baseline':<15} {'---':>8} {s_base['violations']:>8} "
      f"{s_base['losses_kwh']:>7.1f} {'---':>8} {s_base['violations']:>8} "
      f"{s_base['losses_kwh']:>7.1f}")

for r in all_results:
    config = f"±{r['limit']}kW/{r['capacity']}"
    print(f"  {config:<15} ${r['dp_revenue']:>7.2f} {r['dp_violations']:>8} "
          f"{r['dp_losses']:>7.1f} "
          f"${r['rl_revenue']:>7.2f} {r['rl_violations']:>8} "
          f"{r['rl_losses']:>7.1f}")

# ---- Improvement Table ----
print(f"\n{'='*90}")
print(f"  RL IMPROVEMENT OVER DP")
print(f"{'='*90}")
print(f"  {'Config':<15} {'Rev Gap':>10} {'Viol Δ':>8} {'Loss Δ':>10} {'Assessment'}")
print(f"  {'-'*15} {'-'*10} {'-'*8} {'-'*10} {'-'*20}")

for r in all_results:
    config = f"±{r['limit']}kW/{r['capacity']}"
    rev_gap = r['rl_revenue'] - r['dp_revenue']
    viol_diff = r['rl_violations'] - r['dp_violations']
    loss_diff = r['rl_losses'] - r['dp_losses']

    if r['rl_violations'] == 0 and r['dp_violations'] > 0:
        assessment = "✅ RL fixes violations"
    elif r['rl_violations'] == 0 and r['dp_violations'] == 0:
        if abs(rev_gap) < 1:
            assessment = "🟰 Both optimal"
        else:
            assessment = "⚠️  RL feasible, less revenue"
    elif r['rl_violations'] < r['dp_violations']:
        assessment = "📉 RL fewer violations"
    else:
        assessment = "❌ No improvement"

    print(f"  {config:<15} ${rev_gap:>+9.2f} {viol_diff:>+8} "
          f"{loss_diff:>+9.1f} {assessment}")

# ---- Key Findings ----
print(f"\n{'='*90}")
print(f"  KEY FINDINGS")
print(f"{'='*90}")

dp_feasible = [r for r in all_results if r['dp_violations'] == 0]
rl_feasible = [r for r in all_results if r['rl_violations'] == 0]

if dp_feasible:
    dp_min = min(dp_feasible, key=lambda r: (r['capacity'], r['limit']))
    print(f"  DP minimum feasible:  ±{dp_min['limit']}kW / {dp_min['capacity']}kWh "
          f"(${dp_min['dp_revenue']:.2f}/day)")
else:
    print(f"  DP: no fully feasible configuration in tested range")

if rl_feasible:
    rl_min = min(rl_feasible, key=lambda r: (r['capacity'], r['limit']))
    print(f"  RL minimum feasible:  ±{rl_min['limit']}kW / {rl_min['capacity']}kWh "
          f"(${rl_min['rl_revenue']:.2f}/day)")
else:
    print(f"  RL: no fully feasible configuration in tested range")

if dp_feasible and rl_feasible:
    dp_cap = min(r['capacity'] for r in dp_feasible)
    rl_cap = min(r['capacity'] for r in rl_feasible)
    if rl_cap < dp_cap:
        saving = dp_cap - rl_cap
        print(f"\n  Q-learning reduces minimum battery size by {saving} kWh "
              f"({saving/dp_cap*100:.0f}% smaller)")
    elif rl_cap == dp_cap:
        dp_r = dp_min['dp_revenue']
        rl_r = rl_min['rl_revenue']
        print(f"\n  Same minimum capacity. DP: ${dp_r:.2f}/day, RL: ${rl_r:.2f}/day")

# ---- Dispatch Profiles ----
for r in all_results:
    # Only show configs where DP and RL differ meaningfully
    if r['dp_violations'] == r['rl_violations'] and abs(r['dp_revenue'] - r['rl_revenue']) < 1:
        continue

    cap = r['capacity']
    limit = r['limit']
    dp_d = r['dp_dispatch']
    rl_d = r['rl_dispatch']

    battery = Battery(kwh_rated=cap, kw_rated=100)
    dp_soc = np.zeros(49)
    rl_soc = np.zeros(49)
    dp_soc[0] = cap / 2
    rl_soc[0] = cap / 2

    for t in range(48):
        dp_soc[t + 1] = float(battery.next_soc(dp_soc[t], dp_d[t], 0.5))
        dp_soc[t + 1] = max(battery.soc_min, min(battery.soc_max, dp_soc[t + 1]))
        rl_soc[t + 1] = float(battery.next_soc(rl_soc[t], rl_d[t], 0.5))
        rl_soc[t + 1] = max(battery.soc_min, min(battery.soc_max, rl_soc[t + 1]))

    print(f"\n{'='*90}")
    print(f"  DISPATCH PROFILE: ±{limit}kW / {cap}kWh")
    print(f"  DP: ${r['dp_revenue']:.2f}/day, {r['dp_violations']} violations")
    print(f"  RL: ${r['rl_revenue']:.2f}/day, {r['rl_violations']} violations")
    print(f"{'='*90}")
    print(f"  {'t':<4} {'Time':<6} {'Price':>7}  {'DP kW':>7} {'DP SoC':>7}  "
          f"{'RL kW':>7} {'RL SoC':>7}  {'Diff':>6}")
    print(f"  {'--':<4} {'-----':<6} {'------':>7}  {'-'*7} {'-'*7}  "
          f"{'-'*7} {'-'*7}  {'-'*6}")

    for t in range(48):
        h = int(t / 2)
        m = int((t / 2 - h) * 60)
        dp_str = f"{dp_d[t]:+.0f}" if abs(dp_d[t]) > 0.1 else "0"
        rl_str = f"{rl_d[t]:+.0f}" if abs(rl_d[t]) > 0.1 else "0"
        diff = rl_d[t] - dp_d[t]
        diff_str = f"{diff:+.0f}" if abs(diff) > 0.1 else ""
        print(f"  {t:<4} {h:02d}:{m:02d}  ${prices[t]:>6.1f}  {dp_str:>7} {dp_soc[t]:>7.1f}  "
              f"{rl_str:>7} {rl_soc[t]:>7.1f}  {diff_str:>6}")

    print(f"  {'END':<4} {'':6} {'':>7}  {'':>7} {dp_soc[48]:>7.1f}  "
          f"{'':>7} {rl_soc[48]:>7.1f}")
    print(f"\n  Revenue gap: ${r['dp_revenue'] - r['rl_revenue']:.2f}/day")