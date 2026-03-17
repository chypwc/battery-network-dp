import numpy as np
from src.dp.battery import Battery
from src.dp.prices import load_day_prices
from src.opendss.profiles import generate_load_profile, generate_solar_profile
from src.opendss.feeders import FEEDER_32
from src.opendss import network
from src.integration.feedback import run_feedback_loop, print_iteration_summary
from src.integration import timeseries

prices = load_day_prices('data/aemo/prices_typical_2024-06-28.csv')
load_profile = generate_load_profile()
solar_profile = generate_solar_profile()
dss_file = FEEDER_32['dss_file']

# ============================================================
# Full sensitivity: dispatch limit × battery capacity
# ============================================================
dispatch_limits = [30, 50, 80, 100]
capacities = [200, 300, 400]
all_results = []

for limit in dispatch_limits:
    for cap in capacities:
        battery = Battery(kwh_rated=cap, kw_rated=100)
        initial_soc = cap / 2

        print(f"\n{'='*70}")
        print(f"  ±{limit} kW dispatch, {cap} kWh capacity")
        print(f"{'='*70}")

        fb = run_feedback_loop(
            battery=battery,
            prices=prices,
            load_profile=load_profile,
            solar_profile=solar_profile,
            feeder_config=FEEDER_32,
            dss_file=dss_file,
            dispatch_limit=limit,
            initial_soc=initial_soc,
            max_iterations=5,
        )

        # Final network check
        df_batt = timeseries.run(
            fb['dispatch'], load_profile, solar_profile,
            FEEDER_32, dss_file, battery_enabled=True, battery=battery)
        s = timeseries.summarise(df_batt, f"±{limit}kW {cap}kWh")

        all_results.append({
            'limit': limit,
            'capacity': cap,
            'revenue': fb['iterations'][-1]['revenue'],
            'violations': fb['iterations'][-1]['violations'],
            'losses': s['losses_kwh'],
            'peak_tx': s['peak_tx'],
            'v_min': s['v_min'],
            'v_max': s['v_max'],
        })

# ============================================================
# Baseline (no battery) for reference
# ============================================================
df_base = timeseries.run(np.zeros(48), load_profile, solar_profile,
                         FEEDER_32, dss_file, battery_enabled=False)
s_base = timeseries.summarise(df_base, "No Battery")

# ============================================================
# Summary table
# ============================================================
print(f"\n{'='*90}")
print(f"  FULL SENSITIVITY: Dispatch Limit × Battery Capacity")
print(f"{'='*90}")
print(f"  {'Limit':>6} {'Cap':>6} {'Revenue':>10} {'Violations':>11} {'Fixed':>6} "
      f"{'Losses':>8} {'PeakTx':>7} {'V_min':>7} {'V_max':>7}")
print(f"  {'-'*6} {'-'*6} {'-'*10} {'-'*11} {'-'*6} "
      f"{'-'*8} {'-'*7} {'-'*7} {'-'*7}")

print(f"  {'base':>6} {'---':>6} {'---':>10} {s_base['violations']:>11} "
      f"{'---':>6} {s_base['losses_kwh']:>7.1f} {s_base['peak_tx']:>6.1f}% "
      f"{s_base['v_min']:>7.4f} {s_base['v_max']:>7.4f}")

for r in all_results:
    fixed = 11 - r['violations']
    print(f"  ±{r['limit']:<4} {r['capacity']:>4}kW ${r['revenue']:>9.2f} "
          f"{r['violations']:>11} {fixed:>5}/11 "
          f"{r['losses']:>7.1f} {r['peak_tx']:>6.1f}% "
          f"{r['v_min']:>7.4f} {r['v_max']:>7.4f}")

# ============================================================
# Revenue vs violations trade-off
# ============================================================
print(f"\n{'='*90}")
print(f"  KEY FINDINGS")
print(f"{'='*90}")

feasible = [r for r in all_results if r['violations'] == 0]
if feasible:
    cheapest = min(feasible, key=lambda r: r['capacity'])
    print(f"  Minimum feasible configuration: ±{cheapest['limit']}kW / {cheapest['capacity']}kWh")
    print(f"    Revenue: ${cheapest['revenue']:.2f}/day (${cheapest['revenue']*365:,.0f}/year)")
    print(f"    Violations: 0")

best_revenue = max(all_results, key=lambda r: r['revenue'])
print(f"\n  Highest revenue: ±{best_revenue['limit']}kW / {best_revenue['capacity']}kWh")
print(f"    Revenue: ${best_revenue['revenue']:.2f}/day (${best_revenue['revenue']*365:,.0f}/year)")
print(f"    Violations: {best_revenue['violations']}")