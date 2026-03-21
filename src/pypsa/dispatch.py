"""
Battery dispatch optimisation using PyPSA LOPF.

Solves the same arbitrage problem as our DP solver:
maximise revenue subject to SoC constraints.
Uses HiGHS LP solver via PyPSA's optimize() method.
"""

import numpy as np
import pandas as pd 
from src.pypsa.network import build_battery_network
import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="pypsa")


def optimise_day(
        prices: np.ndarray,
        capacity_kwh: float = 200.0,
        power_kw: float = 100.0,
        efficiency: float = 0.95,
        initial_soc_kwh: float | None = None,
        degradation: float = 0.02,
        solver_name: str = "highs",
) -> dict:
    """
    Optimise battery dispatch for a single day (48 half-hour periods).

    Args:
        prices: 48-element array of spot prices (A$/MWh).
        capacity_kwh: battery energy capacity (kWh).
        power_kw: max charge/discharge power (kW).
        efficiency: one-way efficiency.
        initial_soc_kwh: starting SoC (kWh). Defaults to capacity/2.
        degradation: cost per kWh throughput (A$/kWh). Applied to both
                     charge and discharge. Default 0.02 matches Battery class.
        solver_name: LP solver to use.

    Returns:
        dict with keys:
            revenue: total daily revenue (A$)
            dispatch_kw: 48-element array of net power (+ = discharge)
            soc_kwh: 48-element array of SoC after each period
            prices: the input prices (for reference)
            status: solver status string
    """
    n = build_battery_network(
        prices=prices,
        capacity_kwh=capacity_kwh,
        power_kw=power_kw,
        efficiency=efficiency,
        initial_soc_kwh=initial_soc_kwh,
        degradation=degradation,
    )
    # Build the optimisation model 
    m = n.optimize.create_model()

    # Add minimum SoC constraint
    # PyPSA's StorageUnit doesn't natively support state_of_charge_min.
    # We add it manually as a linear constraint on the SoC variable.
    # The SoC variable is in MWh (PyPSA internal units)
    min_soc_mwh = (capacity_kwh * 0.1) / 1000  # 10% of capacity in MWh
    sus = m.variables["StorageUnit-state_of_charge"]
    m.add_constraints(sus >= min_soc_mwh, name="StorageUnit-minimum_soc")

    # Run the optimisation
    # PyPSA translates the network into an LP and calls HiGHS
    # The LP has ~200 variables (48 charge + 48 discharge + 48 SoC + 48 grid)
    # and ~300 constraints. 
    status = n.optimize.solve_model(
        solver_name=solver_name,
        solver_options={"output_flag": False},
    )

    # Extract results from the sovled network
    # storage_units_t contains time series for each StorageUnit.
    #   p_dispatch: power flowing OUT of battery to bus (kW, >= 0)
    #   p_store:    power flowing INTO battery from bus (kW, >= 0)
    #   state_of_charge: SoC at end of each snapshot (kWh)
    p_dispatch = n.storage_units_t.p_dispatch["battery"].values * 1000  # kW
    p_store = n.storage_units_t.p_store["battery"].values * 1000        # kW
    soc = n.storage_units_t.state_of_charge["battery"].values * 1000    # kW

    # Net power: positive = discharging (injecting to grid)
    #            negative = charging (absorbing from grid)
    # Net power > 0 --> positive revenue
    net_kw = p_dispatch - p_store

    # Revenue calculation:
    # When discharging: battery sells power at spot price → positive revenue
    # When charging:    battery buys power at spot price → negative revenue
    # price is in A$/MWh = A$ per 1000 kWh.
    # net_kw is in kW. dt = 0.5 h. Energy = net_kw × dt in kWh.
    # revenue = energy_kWh × (price_A$/MWh / 1000)
    #         = net_kw × 0.5 × price / 1000
    dt = 0.5  # hours per snapshot
    revenue_per_step = net_kw * prices * dt / 1000

    # Degradation cost: applied to ALL throughput (charge + discharge)
    throughput_kwh = (p_dispatch + p_store) * dt  # kWh per step
    degradation_cost = throughput_kwh.sum() * degradation  # A$

    total_revenue = revenue_per_step.sum() - degradation_cost

    return {
        "revenue": total_revenue,
        "dispatch_kw": net_kw,
        "soc_kwh": soc,
        "prices": prices,
        "status": status,
    }


def optimise_year(
        daily_prices: list[np.ndarray],
        dates: list[str],
        capacity_kwh: float = 200.0,
        power_kw: float = 100.0,
        efficiency: float = 0.95,
        initial_soc_kwh: float | None = None,
        degradation: float = 0.02,
        solver_name: str = "highs",
) -> pd.DataFrame:
    """
    Optimise battery dispatch for every day in a year.

    Args:
        daily_prices: list of 48-element price arrays, one per day.
        dates: list of date strings (YYYY-MM-DD), same length.
        capacity_kwh, power_kw, efficiency, initial_soc_kwh: battery params.
        degradation: cost per kWh throughput (A$/kWh). 
        solver_name: LP solver.

    Returns:
        DataFrame with columns: date, revenue, spread, min_price, max_price
    """
    results = []
    num_days = len(daily_prices)
    for i, (prices, date) in enumerate(zip(daily_prices, dates)):
        if len(prices) < 48:
            # Skip incomplete days (< 48 half-hours)
            continue

        # Truncate to exactly 48 if there are extras
        prices_48 = prices[:48]

        try:
            result = optimise_day(
                prices=prices_48,
                capacity_kwh=capacity_kwh,
                power_kw=power_kw,
                efficiency=efficiency,
                initial_soc_kwh=initial_soc_kwh,
                solver_name=solver_name,
                degradation=degradatio
            )
            results.append({
                "date": date,
                "revenue": result["revenue"],
                "spread": prices_48.max() - prices_48.min(),
                "min_price": prices_48.min(),
                "max_price": prices_48.max(),
                "mean_price": prices_48.mean(),
            })
        except Exception as e:
            print(f"    Warning: failed for {date}: {e}")
            continue


        # Progress update every 50 days
        if (i+1) % 50 == 0:
            print(f"    Processed {i+1}/{num_days} days...")

    return pd.DataFrame(results)