# run_timeseries.py
import numpy as np
from src.dp.battery import Battery
from src.dp.solver import DPSolver
from src.dp.prices import load_day_prices
from src.opendss.profiles import generate_load_profile, generate_solar_profile
from src.opendss.feeders import FEEDER_32
from src.integration import timeseries

battery = Battery()
solver = DPSolver(battery, dispatch_limit=50, n_soc=81, n_actions=81)
prices = load_day_prices('data/aemo/prices_typical_2024-06-28.csv')

result = solver.solve(prices, initial_soc=100)
dispatch = result['dispatch']
print(f"DP revenue: ${result['total_revenue']:.2f}")

load_profile = generate_load_profile()
solar_profile = generate_solar_profile()
dss_file = FEEDER_32['dss_file']

# Baseline
df_base = timeseries.run(np.zeros(48), load_profile, solar_profile,
                         FEEDER_32, dss_file, battery_enabled=False)
# DP battery
df_batt = timeseries.run(dispatch, load_profile, solar_profile,
                         FEEDER_32, dss_file, battery_enabled=True)
# Compare
timeseries.compare(df_base, df_batt)