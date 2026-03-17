import opendssdirect as dss
import math
import csv
import numpy as np
import os

# Voltage base constants (for per-unit conversion)
HV_BASE_LN = 11.0 / math.sqrt(3)    # 6.351 kv
LV_BASE_LN = 0.4 / math.sqrt(3)     # 230.9 V

# Australian voltage limits
V_MIN_PU = 0.94
V_MAX_PU = 1.10

# ============================================================
# Circuit loading
# ============================================================
def load_circuit(dss_file):
    """Load and compile a DSS file."""
    path = os.path.abspath(dss_file)
    if not os.path.exists(path):
        raise FileNotFoundError(f"DSS file not found: {path}")
    dss.Text.Command(f'Redirect "{path}"')
    return {
        'path': path,
        'buses': dss.Circuit.NumBuses(),
        'elements': dss.Circuit.NumCktElements(),
    }


def solve():
    """Run power flow and return convergence status"""
    dss.Text.Command('Solve')
    return dss.Solution.Converged()


# ============================================================
# Element control
# ============================================================ 
def set_battery_capacity(kwh_rated, kwh_stored=None):
    """Update battery capacity without editing the DSS file."""
    if kwh_stored is None:
        kwh_stored = kwh_rated / 2
    dss.Text.Command(f'Storage.CommunityBatt.kWhRated={kwh_rated}')
    dss.Text.Command(f'Storage.CommunityBatt.kWhStored={kwh_stored}')

    
def set_loads(load_names,  multiplier):
    """
    Scale all loads by a multiplier (0-1).
    Load changes throughout the day 
    — at 3am it might be 35% of peak, at 6pm it's 95% of peak. 

    Args:
        load_names: dict of {name: peak_kw}
        peak_kw: (unused, included in load_names)
        multiplier: 0.0-1.0
    """
    for name, peak in load_names.items():
        dss.Text.Command(f'Load.{name}.kW={peak * multiplier}')


def set_solar(pv_names, rated_kw, multiplier):
    """
    Scale all PV generators by a multiplier (0-1).
    PV output varies from 0 (night) to 0.75 (midday winter). 
    At each time step we set every Generator element to 6.6 × multiplier. 
    We also need to disable generators at night (multiplier ≈ 0) 
    because OpenDSS generators with kW=0 can cause convergence issues.

    Args:
        pv_names: list of generator names
        rated_kw: rated power per system (e.g. 6.6)
        multiplier: 0.0 (night) to 1.0 (full sun)
    """
    for name in pv_names:
        if multiplier <= 0.001:
            dss.Text.Command(f'Generator.{name}.enabled=no')
        else:
            dss.Text.Command(f'Generator.{name}.enabled=yes')
            dss.Text.Command(f'Generator.{name}.kW={rated_kw * multiplier}')


def set_battery(action_kw):
    """
    Set battery state from DP action value.

    DP convention: positive = charge, negative = discharge
    OpenDSS convention: State=CHARGING/DISCHARGING with positive kW
    """
    if action_kw > 0.1:
        dss.Text.Command('Storage.CommunityBatt.State=CHARGING')
        dss.Text.Command(f'Storage.CommunityBatt.kW={action_kw}')
    elif action_kw < -0.1:
        dss.Text.Command('Storage.CommunityBatt.State=DISCHARGING')
        dss.Text.Command(f'Storage.CommunityBatt.kW={abs(action_kw)}')
    else:
        dss.Text.Command('Storage.CommunityBatt.State=IDLING')


def enable_battery():
    dss.Text.Command('Storage.CommunityBatt.enabled=yes')


def disable_battery():
    dss.Text.Command('Storage.CommunityBatt.enabled=no')


# ============================================================
# Result extraction
# ============================================================

def get_bus_voltage_pu(bus_name):
    """
    Get per-unit voltage magnitudes at a bus (all phases).

    Handles CalcVoltageBases failure by detecting HV vs LV from
    actual voltage magnitude.
    """
    dss.Circuit.SetActiveBus(bus_name)
    v_actual = dss.Bus.VMagAngle()
    n_phases = dss.Bus.NumNodes()
    mags_v = [v_actual[2 * i] for i in range(n_phases)]

    avg_v = sum(mags_v) / len(mags_v) if mags_v else 0
    kv_base = HV_BASE_LN if avg_v > 1000 else LV_BASE_LN
    mags_pu = [v / (kv_base * 1000) for v in mags_v]

    return mags_pu


def get_all_bus_voltages():
    """Read voltage at every bus. Returns dict of {name: [pu_per_phase]}."""
    result = {}
    for name in dss.Circuit.AllBusNames():
        result[name] = get_bus_voltage_pu(name)
    return result


def get_total_losses():
    """Return (P_loss_kW, Q_loss_kVAR) for the entire circuit."""
    losses = dss.Circuit.Losses()
    return losses[0] / 1000, losses[1] / 1000


def get_transformer_loading(rated_kva=200):
    """
    Return transformer loading as percentage of rated kVA.
    
    A transformer does not “consume” power. 
    It simply transfers electrical power from one side to the other (minus small losses). 
    What matters for loading is current, and current depends on both real and reactive components.
    So:
    - Apparent power = total current × voltage
    - Transformer loading = S / rated_kVA
    """
    dss.Circuit.SetActiveElement('Transformer.Tx1')
    powers = dss.CktElement.Powers()
    p_total = abs(powers[0]) + abs(powers[2]) + abs(powers[4])
    q_total = abs(powers[1]) + abs(powers[3]) + abs(powers[5])
    s_total = math.sqrt(p_total**2 + q_total**2)
    return s_total / rated_kva * 100, s_total



def solve_and_read(monitor_buses=None):
    """
    Solve power flow and return key network metrics.

    Args:
        monitor_buses: list of bus names to read voltages at
                       (None = read all buses)

    Returns:
        dict with bus_voltages, losses, tx_loading, v_min, v_max, violation
    """
    solve()

    if monitor_buses:
        bus_voltages = {name: get_bus_voltage_pu(name) for name in monitor_buses}
    else:
        bus_voltages = get_all_bus_voltages()

    p_loss, q_loss = get_total_losses()
    tx_pct, tx_kva = get_transformer_loading()

    # Find min/max across all LV buses
    all_lv_pu = []
    for name, pu_list in bus_voltages.items():
        if pu_list and pu_list[0] < 2.0: # LV bus
            all_lv_pu.extend(pu_list)
        
    v_min = min(all_lv_pu) if all_lv_pu else 1.0
    v_max = max(all_lv_pu) if all_lv_pu else 1.0

    violation = 'OK'
    if v_max > V_MAX_PU:
        violation = 'HIGH'
    elif v_min < V_MIN_PU:
        violation = 'LOW'
    
    return {
        'bus_voltages': bus_voltages,
        'p_loss_kw': p_loss,
        'q_loss_kvar': q_loss,
        'tx_loading_pct': tx_pct,
        'tx_kva': tx_kva,   # apparent power S
        'v_min': v_min,
        'v_max': v_max,
        'violation': violation,
    }


# ============================================================
# Dispatch export (DP → OpenDSS Loadshape)
# ============================================================

def export_dispatch_csv(dispatch, kw_rated, filename):
    """
    Write DP dispatch as OpenDSS Loadshape multipliers.

    DP:     positive = charge,    negative = discharge
    OpenDSS: positive = discharge, negative = charge

    Multiplier = -action / kw_rated  (range [-1, 1])
    """
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        for action in dispatch:
            mult = -action / kw_rated
            writer.writerow([f"{mult:.4f}"])


def load_dispatch_csv(filename, kw_rated):
    """
    Load OpenDSS dispatch CSV and convert to DP convention (kW).

    Returns:
        numpy array of actions in kW (positive = charge, negative = discharge)
    """
    import pandas as pd
    df = pd.read_csv(filename, header=None)
    multipliers = df.iloc[:, 0].values.astype(float)
    return -multipliers * kw_rated


