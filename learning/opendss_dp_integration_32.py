"""
Layer 1 + Layer 2 Integration: 32-House Extended Feeder
========================================================
Same workflow as the 10-house version, but with:
  - 32 houses across 8 nodes (4 per branch × 2 branches)
  - Houses distributed at 50/100/150/200m from junction
  - 20 houses with 6.6 kW solar (62.5% penetration, 132 kW total)
  - ~100 kW peak load
  - Battery at Node A4 (end of Branch A, worst voltage point)

Monitors voltage at every node along the feeder to show
the voltage gradient from transformer to end-of-line.
"""

import opendssdirect as dss
import numpy as np
import pandas as pd
import math
import os


# ============================================================
# Load and solar profiles
# ============================================================

def generate_load_profile():
    """Normalised 24-hour residential load profile (48 half-hour values)."""
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
    """Normalised 24-hour solar profile for Canberra winter (June)."""
    T = 48
    solar = np.zeros(T)
    for i in range(T):
        hour = i / 2
        if 7 <= hour <= 17:
            solar[i] = max(0, np.sin((hour - 7) / 10 * np.pi)) * 0.75
    return solar


# ============================================================
# OpenDSS interface
# ============================================================

# All load names and their peak kW (from the DSS file)
LOAD_NAMES = {
    # Branch A
    'House_A1a': 3.2, 'House_A1b': 2.8, 'House_A1c': 3.5, 'House_A1d': 2.5,
    'House_A2a': 3.0, 'House_A2b': 3.3, 'House_A2c': 2.6, 'House_A2d': 3.1,
    'House_A3a': 2.7, 'House_A3b': 3.4, 'House_A3c': 3.0, 'House_A3d': 2.9,
    'House_A4a': 3.1, 'House_A4b': 2.9, 'House_A4c': 3.3, 'House_A4d': 2.7,
    # Branch B
    'House_B1a': 3.2, 'House_B1b': 2.8, 'House_B1c': 3.5, 'House_B1d': 2.5,
    'House_B2a': 3.0, 'House_B2b': 3.3, 'House_B2c': 2.6, 'House_B2d': 3.1,
    'House_B3a': 2.7, 'House_B3b': 3.4, 'House_B3c': 3.0, 'House_B3d': 2.9,
    'House_B4a': 3.1, 'House_B4b': 2.9, 'House_B4c': 3.3, 'House_B4d': 2.7,
}

# All PV generator names (6.6 kW each)
PV_NAMES = [
    'PV_A1a', 'PV_A1b',
    'PV_A2a', 'PV_A2b', 'PV_A2c',
    'PV_A3a', 'PV_A3b',
    'PV_A4a', 'PV_A4b', 'PV_A4c',
    'PV_B1a', 'PV_B1b',
    'PV_B2a', 'PV_B2b', 'PV_B2c',
    'PV_B3a', 'PV_B3b',
    'PV_B4a', 'PV_B4b', 'PV_B4c',
]

# Bus names to monitor along each branch (ordered by distance)
BRANCH_A_BUSES = ['lv_bus', 'junction', 'bra1', 'bra2', 'bra3', 'bra4']
BRANCH_B_BUSES = ['lv_bus', 'junction', 'brb1', 'brb2', 'brb3', 'brb4']
DISTANCES = [0, 150, 200, 250, 300, 350]  # metres from transformer


def load_circuit(dss_file):
    path = os.path.abspath(dss_file)
    dss.Text.Command(f'Redirect "{path}"')
    total_load = sum(LOAD_NAMES.values())
    total_solar = len(PV_NAMES) * 6.6
    print(f"Loaded: {path}")
    print(f"  Buses: {dss.Circuit.NumBuses()}, Elements: {dss.Circuit.NumCktElements()}")
    print(f"  Houses: {len(LOAD_NAMES)}, Peak load: {total_load:.0f} kW")
    print(f"  PV systems: {len(PV_NAMES)}, Solar capacity: {total_solar:.0f} kW")


def set_all_loads(multiplier):
    for name, peak_kw in LOAD_NAMES.items():
        dss.Text.Command(f'Load.{name}.kW={peak_kw * multiplier}')


def set_all_solar(multiplier):
    for name in PV_NAMES:
        if multiplier <= 0.001:
            dss.Text.Command(f'Generator.{name}.enabled=no')
        else:
            dss.Text.Command(f'Generator.{name}.enabled=yes')
            dss.Text.Command(f'Generator.{name}.kW={6.6 * multiplier}')


def set_battery(action_kw):
    if action_kw > 0.1:
        dss.Text.Command('Storage.CommunityBatt.State=CHARGING')
        dss.Text.Command(f'Storage.CommunityBatt.kW={action_kw}')
    elif action_kw < -0.1:
        dss.Text.Command('Storage.CommunityBatt.State=DISCHARGING')
        dss.Text.Command(f'Storage.CommunityBatt.kW={abs(action_kw)}')
    else:
        dss.Text.Command('Storage.CommunityBatt.State=IDLING')


def disable_battery():
    dss.Text.Command('Storage.CommunityBatt.enabled=no')


def enable_battery():
    dss.Text.Command('Storage.CommunityBatt.enabled=yes')


def get_bus_voltage_pu(bus_name):
    """Get average per-unit voltage at a bus (across all phases)."""
    HV_BASE_LN = 11.0 / math.sqrt(3)
    LV_BASE_LN = 0.4 / math.sqrt(3)

    dss.Circuit.SetActiveBus(bus_name)
    v_actual = dss.Bus.VMagAngle()
    n_phases = dss.Bus.NumNodes()
    mags_v = [v_actual[2 * i] for i in range(n_phases)]

    avg_v = sum(mags_v) / len(mags_v) if mags_v else 0
    kv_base = HV_BASE_LN if avg_v > 1000 else LV_BASE_LN

    mags_pu = [v / (kv_base * 1000) for v in mags_v]
    return mags_pu


def solve_and_read():
    """Solve and extract results for all monitored buses."""
    dss.Text.Command('Solve')

    # Voltage at every bus along both branches
    branch_a_v = {}
    branch_b_v = {}
    all_lv_pu = []

    for bus_name in BRANCH_A_BUSES:
        pu = get_bus_voltage_pu(bus_name)
        branch_a_v[bus_name] = np.mean(pu) if pu else 0
        if pu and pu[0] < 2.0:
            all_lv_pu.extend(pu)

    for bus_name in BRANCH_B_BUSES:
        if bus_name in branch_a_v:  # skip lv_bus and junction (already read)
            branch_b_v[bus_name] = branch_a_v[bus_name]
            continue
        pu = get_bus_voltage_pu(bus_name)
        branch_b_v[bus_name] = np.mean(pu) if pu else 0
        if pu and pu[0] < 2.0:
            all_lv_pu.extend(pu)

    # Losses
    losses = dss.Circuit.Losses()
    p_loss_kw = losses[0] / 1000

    # Transformer loading
    dss.Circuit.SetActiveElement('Transformer.Tx1')
    powers = dss.CktElement.Powers()
    p_tx = abs(powers[0]) + abs(powers[2]) + abs(powers[4])
    q_tx = abs(powers[1]) + abs(powers[3]) + abs(powers[5])
    s_tx = math.sqrt(p_tx**2 + q_tx**2)
    tx_loading = s_tx / 200 * 100

    v_min = min(all_lv_pu) if all_lv_pu else 1.0
    v_max = max(all_lv_pu) if all_lv_pu else 1.0
    violation = 'HIGH' if v_max > 1.10 else ('LOW' if v_min < 0.94 else 'OK')

    return {
        'branch_a_v': branch_a_v,
        'branch_b_v': branch_b_v,
        'p_loss_kw': p_loss_kw,
        'tx_loading_pct': tx_loading,
        'tx_kva': s_tx,
        'v_min': v_min,
        'v_max': v_max,
        'violation': violation,
    }


# ============================================================
# Time-series simulation
# ============================================================

def run_timeseries(dispatch, load_profile, solar_profile, label, battery_enabled=True):
    T = len(dispatch)

    print(f"\n{'#'*80}")
    print(f"# TIME-SERIES: {label}")
    print(f"{'#'*80}")

    if battery_enabled:
        enable_battery()
    else:
        disable_battery()

    records = []

    for t in range(T):
        hour = t / 2
        h = int(hour)
        m = int((hour - h) * 60)
        time_str = f"{h:02d}:{m:02d}"

        set_all_loads(load_profile[t])
        set_all_solar(solar_profile[t])
        if battery_enabled:
            set_battery(dispatch[t])

        r = solve_and_read()

        records.append({
            'time': time_str,
            'hour': hour,
            'load_mult': load_profile[t],
            'solar_mult': solar_profile[t],
            'batt_kw': dispatch[t],
            # Branch A node voltages
            'a1_pu': r['branch_a_v'].get('bra1', 0),
            'a2_pu': r['branch_a_v'].get('bra2', 0),
            'a3_pu': r['branch_a_v'].get('bra3', 0),
            'a4_pu': r['branch_a_v'].get('bra4', 0),
            # Branch B end voltage (for comparison)
            'b4_pu': r['branch_b_v'].get('brb4', 0),
            'v_min': r['v_min'],
            'v_max': r['v_max'],
            'loss_kw': r['p_loss_kw'],
            'tx_loading': r['tx_loading_pct'],
            'violation': r['violation'],
        })

    df = pd.DataFrame(records)

    # ---- Print time-series table ----
    # Show voltage gradient along Branch A and end of Branch B
    print(f"\n  {'Time':<6} {'Load':>5} {'Solar':>6} {'Batt':>7} "
          f"{'A1':>7} {'A2':>7} {'A3':>7} {'A4':>7} {'B4':>7} "
          f"{'Loss':>6} {'TxLd':>5} {'St'}")
    print(f"  {'-'*6} {'-'*5} {'-'*6} {'-'*7} "
          f"{'-'*7} {'-'*7} {'-'*7} {'-'*7} {'-'*7} "
          f"{'-'*6} {'-'*5} {'-'*3}")

    for _, row in df.iterrows():
        batt_str = f"{row['batt_kw']:+.0f}" if abs(row['batt_kw']) > 0.1 else "0"
        flag = ' ⚠️' if row['violation'] != 'OK' else ''
        print(f"  {row['time']:<6} {row['load_mult']:>5.2f} {row['solar_mult']:>6.2f} "
              f"{batt_str:>7} "
              f"{row['a1_pu']:>7.4f} {row['a2_pu']:>7.4f} "
              f"{row['a3_pu']:>7.4f} {row['a4_pu']:>7.4f} "
              f"{row['b4_pu']:>7.4f} "
              f"{row['loss_kw']:>6.2f} {row['tx_loading']:>4.1f}% "
              f"{row['violation']}{flag}")

    # ---- Summary ----
    violations = df[df['violation'] != 'OK']
    print(f"\n  Summary:")
    print(f"    Voltage range:      {df['v_min'].min():.4f} – {df['v_max'].max():.4f} pu")
    print(f"    Voltage violations: {len(violations)} of {T} periods")
    if len(violations) > 0:
        print(f"    Violation times:    {', '.join(violations['time'].values)}")
        for _, row in violations.iterrows():
            print(f"      {row['time']}: V_min={row['v_min']:.4f}, "
                  f"V_max={row['v_max']:.4f}, Battery={row['batt_kw']:+.0f} kW")
    print(f"    Total losses:       {df['loss_kw'].sum() * 0.5:.2f} kWh "
          f"(avg {df['loss_kw'].mean():.3f} kW)")
    print(f"    Peak Tx loading:    {df['tx_loading'].max():.1f}%")
    print(f"    Avg Tx loading:     {df['tx_loading'].mean():.1f}%")

    return df


def load_dp_dispatch(csv_path, kw_rated=100):
    """Load DP dispatch CSV and convert to DP convention (kW)."""
    df = pd.read_csv(csv_path, header=None)
    multipliers = df.iloc[:, 0].values.astype(float)
    dispatch = -multipliers * kw_rated
    return dispatch


def main():
    dss_file = 'suburb_feeder_32.dss'
    dispatch_file = 'dp_dispatch_typical_2024-06-28.csv'

    if not os.path.exists(dispatch_file):
        print(f"Dispatch file not found: {dispatch_file}")
        print(f"Run dp_battery_optimiser.py first.")
        return

    load_profile = generate_load_profile()
    solar_profile = generate_solar_profile()
    dispatch = load_dp_dispatch(dispatch_file, kw_rated=100)

    total_peak = sum(LOAD_NAMES.values())
    total_solar = len(PV_NAMES) * 6.6

    print(f"Load profile:  peak at {load_profile.argmax() / 2:.1f}h, "
          f"range {load_profile.min():.2f}–{load_profile.max():.2f}")
    print(f"  Total peak load: {total_peak:.0f} kW × {load_profile.max():.2f} = "
          f"{total_peak * load_profile.max():.0f} kW")
    print(f"Solar profile: peak at {solar_profile.argmax() / 2:.1f}h, "
          f"range {solar_profile.min():.2f}–{solar_profile.max():.2f}")
    print(f"  Total solar capacity: {total_solar:.0f} kW × {solar_profile.max():.2f} = "
          f"{total_solar * solar_profile.max():.0f} kW")
    print(f"\nDP dispatch: max charge {dispatch.max():+.0f} kW, "
          f"max discharge {dispatch.min():+.0f} kW")

    # ---- Run both scenarios ----
    load_circuit(dss_file)
    df_no_batt = run_timeseries(
        np.zeros(48), load_profile, solar_profile,
        "NO BATTERY (baseline)", battery_enabled=False)

    load_circuit(dss_file)
    df_with_batt = run_timeseries(
        dispatch, load_profile, solar_profile,
        "DP-OPTIMISED BATTERY (50 kW dispatch limit)", battery_enabled=True)

    # ---- Comparison ----
    print(f"\n{'='*80}")
    print(f"  COMPARISON: No Battery vs DP-Optimised Battery (32-house feeder)")
    print(f"{'='*80}")

    print(f"\n  {'Metric':<35} {'No Battery':>15} {'DP Battery':>15} {'Change':>15}")
    print(f"  {'-'*35} {'-'*15} {'-'*15} {'-'*15}")

    loss_no = df_no_batt['loss_kw'].sum() * 0.5
    loss_dp = df_with_batt['loss_kw'].sum() * 0.5
    print(f"  {'Total losses (kWh)':<35} {loss_no:>15.2f} {loss_dp:>15.2f} "
          f"{loss_dp - loss_no:>+14.2f}")

    tx_no = df_no_batt['tx_loading'].max()
    tx_dp = df_with_batt['tx_loading'].max()
    print(f"  {'Peak Tx loading (%)':<35} {tx_no:>14.1f}% {tx_dp:>14.1f}% "
          f"{tx_dp - tx_no:>+14.1f}%")

    vmin_no = df_no_batt['v_min'].min()
    vmax_no = df_no_batt['v_max'].max()
    vmin_dp = df_with_batt['v_min'].min()
    vmax_dp = df_with_batt['v_max'].max()
    print(f"  {'Voltage min (pu)':<35} {vmin_no:>15.4f} {vmin_dp:>15.4f}")
    print(f"  {'Voltage max (pu)':<35} {vmax_no:>15.4f} {vmax_dp:>15.4f}")

    spread_no = vmax_no - vmin_no
    spread_dp = vmax_dp - vmin_dp
    print(f"  {'Voltage spread (pu)':<35} {spread_no:>15.4f} {spread_dp:>15.4f} "
          f"{spread_dp - spread_no:>+14.4f}")

    viol_no = len(df_no_batt[df_no_batt['violation'] != 'OK'])
    viol_dp = len(df_with_batt[df_with_batt['violation'] != 'OK'])
    print(f"  {'Voltage violations':<35} {viol_no:>15} {viol_dp:>15}")

    # ---- Voltage gradient along feeder at key time steps ----
    print(f"\n  Voltage gradient along Branch A at key moments:")
    print(f"  {'Time':<6} {'Batt':>7}  {'A1':>7} {'A2':>7} {'A3':>7} "
          f"{'A4':>7}  {'B4(ctrl)':>8}  {'A4-B4':>7}")
    print(f"  {'-'*6} {'-'*7}  {'-'*7} {'-'*7} {'-'*7} "
          f"{'-'*7}  {'-'*8}  {'-'*7}")

    for _, row in df_with_batt.iterrows():
        if abs(row['batt_kw']) > 0.1:
            batt_str = f"{row['batt_kw']:+.0f}"
            diff = row['a4_pu'] - row['b4_pu']
            print(f"  {row['time']:<6} {batt_str:>7}  {row['a1_pu']:>7.4f} "
                  f"{row['a2_pu']:>7.4f} {row['a3_pu']:>7.4f} "
                  f"{row['a4_pu']:>7.4f}  {row['b4_pu']:>8.4f}  {diff:>+7.4f}")

    # ---- Feasibility verdict ----
    print(f"\n{'='*80}")
    print(f"  NETWORK FEASIBILITY VERDICT")
    print(f"{'='*80}")
    if viol_dp == 0:
        margin = 1.10 - vmax_dp
        print(f"  ✅ DP dispatch is NETWORK-FEASIBLE.")
        print(f"     All voltages within 0.94–1.10 pu at all time steps.")
        print(f"     Margin to upper limit: {margin:.4f} pu ({margin * 230:.1f} V)")
    else:
        print(f"  ⚠️  DP dispatch causes {viol_dp} VOLTAGE VIOLATIONS.")
        print(f"     → Re-run DP with tighter dispatch constraints.")


if __name__ == '__main__':
    main()