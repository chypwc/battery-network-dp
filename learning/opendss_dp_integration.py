"""
Layer 1 + Layer 2 Integration: DP Dispatch → OpenDSS Network Verification
==========================================================================
This script takes the optimal dispatch schedule from the DP solver
and runs it through the OpenDSS feeder model, checking at every
half-hour time step whether the network remains feasible.

Workflow:
    1. Load the OpenDSS feeder model (act_suburb_feeder.dss)
    2. Load the DP dispatch schedule (dp_dispatch_typical_2024-06-28.csv)
    3. For each half-hour t = 0..47:
        a. Set house load level (from load profile)
        b. Set solar output level (from solar profile)
        c. Set battery charge/discharge (from DP dispatch)
        d. Solve power flow
        e. Record: bus voltages, line currents, losses, Tx loading
    4. Report: voltage violations, maximum loading, total losses
    5. Compare: with battery vs without battery (same load/solar)

Requires: pip install opendssdirect.py numpy pandas
"""

import opendssdirect as dss
import numpy as np
import pandas as pd
import math
import os


# ============================================================
# Synthetic load and solar profiles for one day
# ============================================================
# In the full project, replace these with real Ausgrid/BOM data.
# For now, use realistic shapes based on typical ACT patterns.

def generate_load_profile():
    """
    Generate a normalised 24-hour residential load profile (48 half-hour values).

    Returns multipliers 0.0–1.0, where 1.0 = peak load (the kW in the DSS file).

    Typical ACT pattern:
        - Overnight (00:00–06:00): 0.3–0.4 (fridge, standby)
        - Morning (06:00–09:00): 0.7–0.9 (cooking, hot water)
        - Midday (09:00–15:00): 0.3–0.5 (most people at work)
        - Evening peak (17:00–21:00): 0.8–1.0 (cooking, heating, TV)
        - Late night (21:00–24:00): 0.4–0.5
    """
    T = 48
    load = np.zeros(T)
    for i in range(T):
        hour = i / 2
        if hour < 6:
            load[i] = 0.35
        elif hour < 9:
            load[i] = 0.80
        elif hour < 15:
            load[i] = 0.40
        elif hour < 17:
            load[i] = 0.60
        elif hour < 21:
            load[i] = 0.95
        else:
            load[i] = 0.45
    return load


def generate_solar_profile():
    """
    Generate a normalised 24-hour solar generation profile (48 half-hour values).

    Returns multipliers 0.0–1.0, where 1.0 = rated PV output (5 kW per system).

    Typical clear winter day in Canberra (June):
        - Sunrise ~07:00, sunset ~17:00
        - Peak solar ~12:00
        - Shorter and lower than summer
    """
    T = 48
    solar = np.zeros(T)
    for i in range(T):
        hour = i / 2
        if 7 <= hour <= 17:
            # Bell curve peaking at noon
            solar[i] = max(0, np.sin((hour - 7) / 10 * np.pi))
            # Winter reduction factor (shorter days, lower sun angle)
            solar[i] *= 0.75
    return solar


# ============================================================
# OpenDSS interface functions
# ============================================================

def load_circuit(dss_file):
    """Load the DSS file."""
    path = os.path.abspath(dss_file)
    dss.Text.Command(f'Redirect "{path}"')
    print(f"Loaded: {path}")
    print(f"  Buses: {dss.Circuit.NumBuses()}, Elements: {dss.Circuit.NumCktElements()}")


def set_all_loads(multiplier):
    """
    Scale all house loads by a multiplier (0.0–1.0).

    Each load's kW in the DSS file is the peak value.
    multiplier × peak = actual load at this time step.
    """
    load_names = [
        'House_A1', 'House_A2', 'House_A3', 'House_A4', 'House_A5',
        'House_B1', 'House_B2', 'House_B3', 'House_B4', 'House_B5',
    ]
    # Peak kW values from the DSS file
    peak_kw = {
        'House_A1': 3.0, 'House_A2': 2.5, 'House_A3': 3.5,
        'House_A4': 2.0, 'House_A5': 2.8,
        'House_B1': 3.0, 'House_B2': 2.5, 'House_B3': 3.5,
        'House_B4': 2.0, 'House_B5': 2.8,
    }
    for name in load_names:
        kw = peak_kw[name] * multiplier
        dss.Text.Command(f'Load.{name}.kW={kw}')


def set_all_solar(multiplier):
    """Scale all PV generators by a multiplier (0.0–1.0)."""
    pv_names = ['PV_A1', 'PV_A2', 'PV_A3', 'PV_B1', 'PV_B2', 'PV_B3']
    for name in pv_names:
        if multiplier <= 0.001:
            dss.Text.Command(f'Generator.{name}.enabled=no')
        else:
            dss.Text.Command(f'Generator.{name}.enabled=yes')
            kw = 5.0 * multiplier
            dss.Text.Command(f'Generator.{name}.kW={kw}')


def set_battery(action_kw):
    """
    Set battery state from DP dispatch value.

    Args:
        action_kw: from DP convention
            positive = charging (battery absorbs power)
            negative = discharging (battery injects power)
            zero = idle
    """
    if action_kw > 0.1:
        dss.Text.Command('Storage.CommunityBatt.State=CHARGING')
        dss.Text.Command(f'Storage.CommunityBatt.kW={action_kw}')
    elif action_kw < -0.1:
        dss.Text.Command('Storage.CommunityBatt.State=DISCHARGING')
        dss.Text.Command(f'Storage.CommunityBatt.kW={abs(action_kw)}')
    else:
        dss.Text.Command('Storage.CommunityBatt.State=IDLING')


def disable_battery():
    """Disable battery for the 'no battery' baseline scenario."""
    dss.Text.Command('Storage.CommunityBatt.enabled=no')


def enable_battery():
    """Re-enable battery."""
    dss.Text.Command('Storage.CommunityBatt.enabled=yes')


def solve_and_read():
    """
    Solve power flow and extract key results for this time step.

    Returns:
        dict with voltages, losses, transformer loading
    """
    dss.Text.Command('Solve')

    # --- Bus voltages (LV only) ---
    HV_BASE_LN = 11.0 / math.sqrt(3)
    LV_BASE_LN = 0.4 / math.sqrt(3)

    bus_voltages = {}
    for name in dss.Circuit.AllBusNames():
        dss.Circuit.SetActiveBus(name)
        v_actual = dss.Bus.VMagAngle()
        n_phases = dss.Bus.NumNodes()
        mags_v = [v_actual[2 * i] for i in range(n_phases)]

        avg_v = sum(mags_v) / len(mags_v) if mags_v else 0
        kv_base = HV_BASE_LN if avg_v > 1000 else LV_BASE_LN
        mags_pu = [v / (kv_base * 1000) for v in mags_v]

        bus_voltages[name] = {
            'v_pu': mags_pu,
            'v_volts': mags_v,
        }

    # --- Total losses ---
    losses = dss.Circuit.Losses()
    p_loss_kw = losses[0] / 1000
    q_loss_kvar = losses[1] / 1000

    # --- Transformer loading ---
    dss.Circuit.SetActiveElement('Transformer.Tx1')
    powers = dss.CktElement.Powers()
    p_tx = abs(powers[0]) + abs(powers[2]) + abs(powers[4])
    q_tx = abs(powers[1]) + abs(powers[3]) + abs(powers[5])
    s_tx = math.sqrt(p_tx**2 + q_tx**2)
    tx_loading = s_tx / 200 * 100  # 200 kVA rated

    return {
        'bus_voltages': bus_voltages,
        'p_loss_kw': p_loss_kw,
        'q_loss_kvar': q_loss_kvar,
        'tx_loading_pct': tx_loading,
        'tx_kva': s_tx,
    }


# ============================================================
# Main time-series simulation
# ============================================================

def run_timeseries(dispatch, load_profile, solar_profile, label, battery_enabled=True):
    """
    Run 48-step time-series power flow with given profiles.

    Args:
        dispatch: array of 48 battery actions (kW), DP convention
                  (positive=charge, negative=discharge). Use zeros for no-battery case.
        load_profile: array of 48 load multipliers (0–1)
        solar_profile: array of 48 solar multipliers (0–1)
        label: scenario name for printing
        battery_enabled: whether the battery element is active

    Returns:
        DataFrame with time-series results
    """
    T = len(dispatch)
    assert T == 48, f"Expected 48 periods, got {T}"

    print(f"\n{'#'*75}")
    print(f"# TIME-SERIES: {label}")
    print(f"{'#'*75}")

    if battery_enabled:
        enable_battery()
    else:
        disable_battery()

    # Storage for results at each time step
    records = []

    for t in range(T):
        hour = t / 2
        h = int(hour)
        m = int((hour - h) * 60)
        time_str = f"{h:02d}:{m:02d}"

        # Set operating conditions for this time step
        set_all_loads(load_profile[t])
        set_all_solar(solar_profile[t])
        if battery_enabled:
            set_battery(dispatch[t])

        # Solve and read results
        r = solve_and_read()

        # Extract Branch A end voltage (most stressed bus)
        bra_pu = r['bus_voltages'].get('bra', {}).get('v_pu', [0, 0, 0])
        brb_pu = r['bus_voltages'].get('brb', {}).get('v_pu', [0, 0, 0])

        # Check for voltage violations (AS 61000.3.100: 0.94–1.10 pu)
        all_lv_pu = []
        for bname, bdata in r['bus_voltages'].items():
            if bdata['v_pu'] and bdata['v_pu'][0] < 2.0:  # LV bus
                all_lv_pu.extend(bdata['v_pu'])

        v_min = min(all_lv_pu) if all_lv_pu else 1.0
        v_max = max(all_lv_pu) if all_lv_pu else 1.0
        violation = 'HIGH' if v_max > 1.10 else ('LOW' if v_min < 0.94 else 'OK')

        records.append({
            'time': time_str,
            'hour': hour,
            'load_mult': load_profile[t],
            'solar_mult': solar_profile[t],
            'batt_kw': dispatch[t],
            'brA_v_pu': np.mean(bra_pu) if bra_pu else 0,
            'brB_v_pu': np.mean(brb_pu) if brb_pu else 0,
            'v_min_pu': v_min,
            'v_max_pu': v_max,
            'loss_kw': r['p_loss_kw'],
            'tx_loading': r['tx_loading_pct'],
            'violation': violation,
        })

    df = pd.DataFrame(records)

    # ---- Print time-series table ----
    print(f"\n  {'Time':<6} {'Load':>5} {'Solar':>6} {'Batt':>7} "
          f"{'brA pu':>7} {'brB pu':>7} {'V_min':>6} {'V_max':>6} "
          f"{'Loss':>6} {'TxLoad':>7} {'Status'}")
    print(f"  {'-'*6} {'-'*5} {'-'*6} {'-'*7} "
          f"{'-'*7} {'-'*7} {'-'*6} {'-'*6} "
          f"{'-'*6} {'-'*7} {'-'*6}")

    for _, row in df.iterrows():
        batt_str = f"{row['batt_kw']:+.0f}" if abs(row['batt_kw']) > 0.1 else "0"
        flag = ' ⚠️' if row['violation'] != 'OK' else ''
        print(f"  {row['time']:<6} {row['load_mult']:>5.2f} {row['solar_mult']:>6.2f} "
              f"{batt_str:>7} {row['brA_v_pu']:>7.4f} {row['brB_v_pu']:>7.4f} "
              f"{row['v_min_pu']:>6.4f} {row['v_max_pu']:>6.4f} "
              f"{row['loss_kw']:>6.3f} {row['tx_loading']:>6.1f}% "
              f"{row['violation']}{flag}")

    # ---- Summary statistics ----
    violations = df[df['violation'] != 'OK']
    print(f"\n  Summary:")
    print(f"    Voltage range:     {df['v_min_pu'].min():.4f} – {df['v_max_pu'].max():.4f} pu")
    print(f"    Voltage violations: {len(violations)} of {T} periods")
    if len(violations) > 0:
        print(f"    Violation times:   {', '.join(violations['time'].values)}")
    print(f"    Total losses:      {df['loss_kw'].sum() * 0.5:.2f} kWh "
          f"(avg {df['loss_kw'].mean():.3f} kW)")
    print(f"    Peak Tx loading:   {df['tx_loading'].max():.1f}%")
    print(f"    Avg Tx loading:    {df['tx_loading'].mean():.1f}%")

    return df


def load_dp_dispatch(csv_path, kw_rated=100):
    """
    Load DP dispatch from exported CSV and convert to DP convention.

    The CSV from export_dispatch_for_opendss() contains OpenDSS multipliers:
        positive = discharging, negative = charging
        normalised to [-1, 1]

    Convert back to DP convention:
        positive = charging, negative = discharging
        in kW

    Args:
        csv_path: path to dp_dispatch_*.csv
        kw_rated: battery rated power (kW)

    Returns:
        numpy array of 48 actions in kW (DP convention)
    """
    df = pd.read_csv(csv_path, header=None)
    multipliers = df.iloc[:, 0].values.astype(float)

    # Reverse the sign convention: OpenDSS → DP
    # OpenDSS: positive = discharge, DP: positive = charge
    dispatch = -multipliers * kw_rated

    return dispatch


def main():
    """Run time-series comparison: with DP-optimised battery vs without battery."""

    # ---- Configuration ----
    dss_file = 'suburb_feeder.dss'
    dispatch_file = 'dp_dispatch_typical_2024-06-28.csv'

    if not os.path.exists(dispatch_file):
        # Try in aemo_data directory
        alt_path = os.path.join('aemo_data', dispatch_file)
        if os.path.exists(alt_path):
            dispatch_file = alt_path
        else:
            print(f"Dispatch file not found: {dispatch_file}")
            print(f"Run dp_battery_optimiser.py first.")
            return

    # ---- Load profiles ----
    load_profile = generate_load_profile()
    solar_profile = generate_solar_profile()

    print(f"Load profile:  peak at {load_profile.argmax() / 2:.1f}h, "
          f"range {load_profile.min():.2f}–{load_profile.max():.2f}")
    print(f"Solar profile: peak at {solar_profile.argmax() / 2:.1f}h, "
          f"range {solar_profile.min():.2f}–{solar_profile.max():.2f}")

    # ---- Load DP dispatch ----
    dispatch = load_dp_dispatch(dispatch_file)
    print(f"\nDP dispatch loaded from: {dispatch_file}")
    print(f"  Max charge:    {dispatch.max():+.0f} kW")
    print(f"  Max discharge: {dispatch.min():+.0f} kW")
    charge_periods = sum(1 for d in dispatch if d > 0.1)
    discharge_periods = sum(1 for d in dispatch if d < -0.1)
    idle_periods = sum(1 for d in dispatch if abs(d) <= 0.1)
    print(f"  Charging: {charge_periods}, Discharging: {discharge_periods}, Idle: {idle_periods}")

    # ---- Scenario 1: No battery (baseline) ----
    load_circuit(dss_file)
    no_batt_dispatch = np.zeros(48)
    df_no_batt = run_timeseries(
        dispatch=no_batt_dispatch,
        load_profile=load_profile,
        solar_profile=solar_profile,
        label="NO BATTERY (baseline)",
        battery_enabled=False,
    )

    # ---- Scenario 2: DP-optimised battery ----
    load_circuit(dss_file)
    df_with_batt = run_timeseries(
        dispatch=dispatch,
        load_profile=load_profile,
        solar_profile=solar_profile,
        label="DP-OPTIMISED BATTERY",
        battery_enabled=True,
    )

    # ============================================================
    # Comparison
    # ============================================================
    print(f"\n{'='*75}")
    print(f"  COMPARISON: No Battery vs DP-Optimised Battery")
    print(f"{'='*75}")

    print(f"\n  {'Metric':<30} {'No Battery':>15} {'DP Battery':>15} {'Improvement':>15}")
    print(f"  {'-'*30} {'-'*15} {'-'*15} {'-'*15}")

    # Total energy losses over the day (kW × 0.5h = kWh)
    loss_no = df_no_batt['loss_kw'].sum() * 0.5
    loss_dp = df_with_batt['loss_kw'].sum() * 0.5
    loss_diff = loss_no - loss_dp
    print(f"  {'Total losses (kWh)':<30} {loss_no:>15.2f} {loss_dp:>15.2f} "
          f"{loss_diff:>+14.2f} kWh")

    # Peak transformer loading
    tx_no = df_no_batt['tx_loading'].max()
    tx_dp = df_with_batt['tx_loading'].max()
    print(f"  {'Peak Tx loading (%)':<30} {tx_no:>14.1f}% {tx_dp:>14.1f}% "
          f"{tx_no - tx_dp:>+14.1f}%")

    # Average transformer loading
    tx_avg_no = df_no_batt['tx_loading'].mean()
    tx_avg_dp = df_with_batt['tx_loading'].mean()
    print(f"  {'Avg Tx loading (%)':<30} {tx_avg_no:>14.1f}% {tx_avg_dp:>14.1f}% "
          f"{tx_avg_no - tx_avg_dp:>+14.1f}%")

    # Voltage range
    vmin_no = df_no_batt['v_min_pu'].min()
    vmax_no = df_no_batt['v_max_pu'].max()
    vmin_dp = df_with_batt['v_min_pu'].min()
    vmax_dp = df_with_batt['v_max_pu'].max()
    print(f"  {'Voltage min (pu)':<30} {vmin_no:>15.4f} {vmin_dp:>15.4f}")
    print(f"  {'Voltage max (pu)':<30} {vmax_no:>15.4f} {vmax_dp:>15.4f}")
    spread_no = vmax_no - vmin_no
    spread_dp = vmax_dp - vmin_dp
    print(f"  {'Voltage spread (pu)':<30} {spread_no:>15.4f} {spread_dp:>15.4f} "
          f"{spread_no - spread_dp:>+14.4f}")

    # Violation count
    viol_no = len(df_no_batt[df_no_batt['violation'] != 'OK'])
    viol_dp = len(df_with_batt[df_with_batt['violation'] != 'OK'])
    print(f"  {'Voltage violations':<30} {viol_no:>15} {viol_dp:>15}")

    # ---- Branch A vs Branch B comparison ----
    print(f"\n  Branch A (with battery) vs Branch B (without) — DP scenario:")
    print(f"  {'Time':<6} {'brA (pu)':>9} {'brB (pu)':>9} {'Diff':>9} {'Battery':>10}")
    print(f"  {'-'*6} {'-'*9} {'-'*9} {'-'*9} {'-'*10}")
    for _, row in df_with_batt.iterrows():
        if abs(row['batt_kw']) > 0.1:
            batt_str = f"{row['batt_kw']:+.0f} kW"
            diff = row['brA_v_pu'] - row['brB_v_pu']
            print(f"  {row['time']:<6} {row['brA_v_pu']:>9.4f} {row['brB_v_pu']:>9.4f} "
                  f"{diff:>+9.4f} {batt_str:>10}")

    # ---- Network feasibility verdict ----
    print(f"\n{'='*75}")
    print(f"  NETWORK FEASIBILITY VERDICT")
    print(f"{'='*75}")
    if viol_dp == 0:
        print(f"  ✅ DP dispatch is NETWORK-FEASIBLE.")
        print(f"     All voltages within 0.94–1.10 pu at all time steps.")
        print(f"     No re-optimisation needed.")
    else:
        print(f"  ⚠️  DP dispatch causes {viol_dp} VOLTAGE VIOLATIONS.")
        print(f"     Violating periods:")
        for _, row in df_with_batt[df_with_batt['violation'] != 'OK'].iterrows():
            print(f"       {row['time']}: V_min={row['v_min_pu']:.4f}, "
                  f"V_max={row['v_max_pu']:.4f}, Battery={row['batt_kw']:+.0f} kW")
        print(f"     → Re-run DP with constrained dispatch at these time steps.")


if __name__ == '__main__':
    main()