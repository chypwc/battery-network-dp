"""
PyPSA single-bus network for battery arbitrage optimisation.

This module builds a minimal network:
    one bus, one grid generator, and one storage unit.
PyPSA's linear optimal power flow (LOPF) determines the 
revenue-maximising charge/discharge schedule - the same
problem ourt DP solver by backward induction.

OpenDSS network (physical):
    11kV Grid → Transformer → Trunk cable → Junction
                                              ├─ Branch A → 16 houses + solar + battery
                                              └─ Branch B → 16 houses + solar

PyPSA network (economic):
    [Grid price signal] ←→ [Bus] ←→ [Battery]
    
    That's it. One node, two components.

UNITS: PyPSA works in MW/MWh internally when marginal_cost is A$/MWh.
We convert kW→MW and kWh→MWh at the boundary so that AEMO prices
(A$/MWh) work correctly without scaling.
"""

import pypsa
import numpy as np
import pandas as pd 


def build_battery_network(
        prices: np.ndarray,
        capacity_kwh: float = 200.0,
        power_kw: float = 100.0,
        efficiency: float = 0.95,
        initial_soc_kwh: float | None = None,
        degradation: float = 0.02,
) -> pypsa.Network:
    """
    Build a single-bus network with a battery for arbitrage optimisation
    
    Args:
        prices: 48-element array of half-hourly spot prices (A$.MWh) 
        capacity_kwh: battery energy capacity in kWh.
        power_kw: max charge/discharge power in kW.
        efficiency: one-way charge/discharge efficiency.
                    Round-trip = efficiency^2 = 0.9025 for 0.95
        initial_soc_kwh: starting state of charge in kWh
                        Defaults to capacity_kwh / 2
        degradation: cost per kWh throughput (A$/kWh). Applied to both
                     charge and discharge. Default 0.02 matches Battery class.

    Returns:
        pypsa.Network configured and ready for n.optimize().
    """
    if initial_soc_kwh is None:
        initial_soc_kwh = capacity_kwh / 2

    # Convert to MW/MWh for PyPSA internal consistency
    capacity_mwh = capacity_kwh / 1000
    power_mw = power_kw / 1000
    initial_soc_mwh = initial_soc_kwh / 1000
    
    T = len(prices)
    snapshots = pd.RangeIndex(T) # 0,1,,… ,T-1

    n = pypsa.Network()
    n.set_snapshots(snapshots)

    # Each snapshot is a 30-min period = 0.5 hours
    # PyPSA computes energy as Energy = Power x snapshot_weighting
    # if a battery discharges at 100 kW for one 30‑minute interval
    # 100 kW x 0.5 h = 50 kwh per snapshot
    # PyPSA uses this weight to convert between power (kW, the decision variable)
    #  and energy (kWh, what affects the SoC).
    n.snapshot_weightings.loc[:] = 0.5

    # Single bus - the point where grid and battery connect
    # Adds a bus — a single connection point. In power systems, 
    # a "bus" is a node where components meet. In OpenDSS, we have many buses 
    # (sourcebus, lv_bus, junction, a1, a2, a3, a4, b1, b2, b3, b4). 
    # Here we have just one — it's the abstract point where the grid price 
    # and the battery meet. 
    # carrier="AC" is just a label (doesn't affect the optimisation).
    n.add("Bus", "bus", carrier="AC")  

    # Grid connection: unlimited import/export at spot price.
    # marginal_cost is a time series - one price per snapshot.
    # PyPSA minimises total system cost, so the battery will charge
    # when prices are low (cheap to buy) and discharge when prices
    # are high (displaces expensive grid power)
    # p_nom=1e6: the generator can produce up to 1,000,000 kW. 
    # This is deliberately huge — it means the grid can supply unlimited power. 
    # We're not modelling grid capacity limits, just the price at which power is available.
    # marginal_cost=prices: this is the spot price at each snapshot. 
    # It's a 48-element array like [60, 76, 75, 79, ..., 230, 228, ..., 73] in A$/MWh.

    # PyPSA's optimiser minimises total system cost. 
    # The cost of the grid generator at snapshot t is:
    # cost_t = marginal_cos_t × p_t × weight_t
    # where p_t​ is the grid power dispatched (kW) and weight is 0.5 (hours). 
    # When the battery charges (absorbs power from the grid), 
    #   the grid must produce more power → higher cost. 
    # When the battery discharges (injects power), 
    #   the grid produces less → lower cost. 
    # So minimising cost is equivalent to maximising arbitrage revenue.
    n.add(
        "Generator",
        "grid",
        bus="bus",
        p_nom=1e6,             # effectively unlimited (MW)
        marginal_cost=prices,   # A$/MWh, varies per snapshot
    )

    # Add load: represents the grid demand that the battery can displace.
    # Without this, the grid generator output can't decrease below zero,
    # so the battery has no incentive to discharge.
    # We set it larger than the battery's max power so that the generator
    # always has positive output even when the battery discharges fully.
    n.add(
        "Load",
        "grid_demand",
        bus="bus",
        p_set=power_mw * 2,  # constant load, always > battery max discharge
    )

    # Degradation cost: A$0.02/kWh = A$20/MWh
    # Applied to both charge and discharge throughput.
    # This discourages marginal trades — with A$20/MWh degradation
    # plus 5% efficiency loss, the battery needs ~A$50/MWh spread
    # to break even on a cycle.
    degradation_mwh = degradation * 1000  # A$/kWh → A$/MWh

    # Adds a storage unit named "battery" connected to the same bus.
    # Battery: PyPSA's StorageUnit handles charge/discharge
    # internally - no need for separate charge/discharge links
    # p_nom: power rating in kW (applies to both directions)
    # max_hours: energy capacity / power = hours at full power
    #   200 kWh / 100kW = 2.0 hrs
    # state_of _charge_initial: starting SoC in kWh
    # cyclic_state_of_charge: if True, forces end SoC = start SoC
    #   We set False.
    n.add(
        "StorageUnit",
        "battery",
        bus="bus",
        p_nom=power_mw,
        max_hours=capacity_mwh / power_mw,
        efficiency_store=efficiency,
        efficiency_dispatch=efficiency,
        cyclic_state_of_charge=False,
        state_of_charge_initial=initial_soc_mwh,
        marginal_cost=degradation_mwh,          # cost per MWh discharged
        marginal_cost_storage=degradation_mwh,   # cost per MWh charged
    )

    return n



if __name__ == "__main__":
    from src.pypsa.network import build_battery_network
    import numpy as np
    prices = np.random.uniform(50, 200, 48)
    n = build_battery_network(prices)
    print(f'Snapshots: {len(n.snapshots)}')
    print(f'Buses: {list(n.buses.index)}')
    print(f'Generators: {list(n.generators.index)}')
    print(f'StorageUnits: {list(n.storage_units.index)}')
    print(f'Battery p_nom: {n.storage_units.loc["battery", "p_nom"]} kW')
    print(f'Battery max_hours: {n.storage_units.loc["battery", "max_hours"]} h')
    
    



