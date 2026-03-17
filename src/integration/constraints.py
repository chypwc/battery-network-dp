"""
Network constraint generation from OpenDSS violations.

Analyses time-series results to produce constraints for the DP solver:
    - min_discharge[t]: minimum discharge power at undervoltage periods
    - max_charge[t]: maximum charge power at overvoltage periods
    - min_soc[t]: minimum SoC to ensure energy for future discharge


Think about the violations:

06:00: undervoltage, battery is idle. 
    The battery has energy (SoC=100) but the DP chose not to discharge 
    because the price ($101/MWh) wasn't high enough. We need to force discharge here.

19:30–20:30: undervoltage, battery is empty. 
    The DP emptied the battery by 19:00 chasing revenue. 
    We need to force the DP to save energy for these periods.

Three constraint arrays, each length T=48:

min_discharge[t]: 
    At undervoltage periods, force the battery to discharge. 
    Set to -20 kW (negative = discharge in DP convention). 
    The value -20 is a moderate amount — enough to support voltage without being too aggressive. 
    At non-violation periods, leave at 0 (no constraint).

max_charge[t]: 
    At overvoltage periods, limit charging. 
    Not needed for our case (no overvoltage violations) but include for completeness.

min_soc[t]: 
    For the 19:30-20:30 violations, the battery needs energy at those times. Work backward:
    Battery must discharge 20 kW x 0.5 hours = 10 kWh per period
    Three violation periods (19:30, 20:00, 20:30) need 30 kWh total
    Plus the 20 kWh reserve = 50 kWh minimum SoC at 19:30
    Propagate this backward: set min_soc at earlier periods so the DP doesn't deplete too early
"""

import numpy as np
from src.opendss import network


def check_network(dispatch, load_profile, solar_profile, feeder_config, dss_file, 
                  battery=None):
    """
    Run OpenDSS for each time step and return violation data.

    Returns:
        list of dicts, one per time step, with v_min, v_max, violation flags
    """
    network.load_circuit(dss_file)
    network.enable_battery()
    if battery:
        network.set_battery_capacity(battery.kwh_rated)

    T = len(dispatch)
    results = []

    for t in range(T):
        network.set_loads(feeder_config['load_names'], load_profile[t])
        network.set_solar(feeder_config['pv_names'],
                          feeder_config['pv_rated_kw'],
                          solar_profile[t])
        network.set_battery(dispatch[t])

        r = network.solve_and_read()

        results.append({
            't': t,
            'hour': t / 2,
            'dispatch': dispatch[t],
            'v_min': r['v_min'],
            'v_max': r['v_max'],
            'undervoltage': r['v_min'] < network.V_MIN_PU,
            'overvoltage': r['v_max'] > network.V_MAX_PU,
        })

    return results


def find_minimum_discharge(t, load_profile, solar_profile, feeder_config, dss_file, battery=None):
    """
    Binary search for minimum discharge power that fixes undervoltage at period t.
    
    Tests discharge levels from low to high, returns the first one
    that brings V_min above 0.94 pu.
    
    Returns:
        minimum discharge power (kW), or max tested if none sufficient
    """
    test_powers = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    
    for power in test_powers:
        network.load_circuit(dss_file)
        network.enable_battery()
        if battery:
            network.set_battery_capacity(battery.kwh_rated)
        network.set_loads(feeder_config['load_names'], load_profile[t])
        network.set_solar(feeder_config['pv_names'],
                          feeder_config['pv_rated_kw'],
                          solar_profile[t])
        network.set_battery(-power)  # negative = discharge in DP convention
        r = network.solve_and_read()
        
        if r['v_min'] >= network.V_MIN_PU:
            return power
    
    return test_powers[-1]  # max power if nothing works


def generate_constraints(network_results, battery, dt=0.5,
                         load_profile=None, solar_profile=None,
                         feeder_config=None, dss_file=None):
    T = len(network_results)
    min_discharge = np.zeros(T)
    max_charge = np.full(T, battery.kw_rated)
    min_soc = np.full(T, battery.soc_min)

    undervoltage_periods = []
    overvoltage_periods = []

    # First pass: identify violations and find minimum power needed
    for r in network_results:
        t = r['t']
        if r['undervoltage']:
            undervoltage_periods.append(t)

            # Find minimum discharge that fixes this period
            if load_profile is not None and dss_file is not None:
                min_power = find_minimum_discharge(
                    t, load_profile, solar_profile,
                    feeder_config, dss_file, battery)
                min_discharge[t] = -min_power
            else:
                min_discharge[t] = -50  # fallback

        if r['overvoltage']:
            overvoltage_periods.append(t)
            max_charge[t] = 30

    if undervoltage_periods:
        # Calculate energy budget with per-period power
        usable_kwh = battery.soc_max - battery.soc_min

        # Energy needed for each violation period (now varies per period)
        period_energies = []
        for t in undervoltage_periods:
            energy = abs(min_discharge[t]) * dt / battery.eta_d
            period_energies.append((t, energy))

        # Sort by time (latest first) for priority
        total_energy = sum(e for _, e in period_energies)

        if total_energy > usable_kwh:
            # Can't cover all — prioritise latest periods (evening peak)
            cumulative = 0
            priority_periods = []
            for t, energy in reversed(period_energies):
                if cumulative + energy <= usable_kwh:
                    priority_periods.append(t)
                    cumulative += energy
                else:
                    min_discharge[t] = 0  # drop this period
            priority_periods.sort()
        else:
            priority_periods = undervoltage_periods

        # Set min_soc at first priority period
        if priority_periods:
            first_priority = min(priority_periods)
            energy_needed = sum(
                abs(min_discharge[t]) * dt / battery.eta_d
                for t in priority_periods
            ) + battery.soc_min
            energy_needed = min(energy_needed, battery.soc_max)
            min_soc[first_priority] = energy_needed

            for t in range(first_priority - 1, -1, -1):
                min_soc[t] = min(energy_needed, battery.soc_max * 0.5)

    return {
        'min_discharge': min_discharge,
        'max_charge': max_charge,
        'min_soc': min_soc,
        'undervoltage_periods': undervoltage_periods,
        'overvoltage_periods': overvoltage_periods,
    }