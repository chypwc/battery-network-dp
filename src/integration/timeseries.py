
import numpy as np
import pandas as pd
from src.opendss import network

def run(dispatch, load_profile, solar_profile, feeder_config, dss_file, 
        battery_enabled=True, monitor_buses=None, battery=None):
    """
    Run 48-step time-series power flow.

    Args:
        dispatch: array of 48 battery actions (kW, DP convention)
        load_profile: array of 48 load multipliers (0-1)
        solar_profile: array of 48 solar multipliers (0-1)
        feeder_config: dict with load_names, pv_names, pv_rated_kw
        dss_file: path to DSS file
        battery_enabled: whether battery is active
        monitor_buses: list of bus names to track (None = all)

    Returns:
        DataFrame with time-series results
    """
    T = len(dispatch)
    network.load_circuit(dss_file)

    if battery_enabled:
        network.enable_battery()
        if battery:
            network.set_battery_capacity(battery.kwh_rated)
    else:
        network.disable_battery()
    
    records = []

    for t in range(T):
        hour = t / 2
        h = int(hour)
        m = int( (hour - h) * 60)

        # Set operating conditions
        network.set_loads(feeder_config['load_names'], load_profile[t])
        network.set_solar(feeder_config['pv_names'],
                          feeder_config['pv_rated_kw'], solar_profile[t])
        if battery_enabled:
            network.set_battery(dispatch[t])
        
        # Solve and read
        r = network.solve_and_read(monitor_buses)

        # Extract bus voltages as averages
        bus_v = {}
        for name, pu_list in r['bus_voltages'].items():
            bus_v[name] = np.mean(pu_list) if pu_list else 0
        
        records.append({
            'time': f"{h:02d}:{m:02d}",
            'hour': hour,
            'load_mult': load_profile[t],
            'solar_mult': solar_profile[t],
            'batt_kw': dispatch[t],
            'v_min': r['v_min'],
            'v_max': r['v_max'],
            'loss_kw': r['p_loss_kw'],
            'tx_loading': r['tx_loading_pct'],
            'violation': r['violation'],
            **{f'v_{k}': v for k, v in bus_v.items()},
        })

    return pd.DataFrame(records)


def summarise(df, label=""):
    """Print summary statistics for a time-series run."""
    violations = df[df['violation'] != 'OK']
    print(f"\n  Summary ({label}):")
    print(f"    Voltage range:      {df['v_min'].min():.4f} – {df['v_max'].max():.4f} pu")
    print(f"    Voltage violations: {len(violations)} of {len(df)} periods")
    if len(violations) > 0:
        print(f"    Violation times:    {', '.join(violations['time'].values)}")
    print(f"    Total losses:       {df['loss_kw'].sum() * 0.5:.2f} kWh")
    print(f"    Peak Tx loading:    {df['tx_loading'].max():.1f}%")
    print(f"    Avg Tx loading:     {df['tx_loading'].mean():.1f}%")
    return {
        'v_min': df['v_min'].min(),
        'v_max': df['v_max'].max(),
        'violations': len(violations),
        'losses_kwh': df['loss_kw'].sum() * 0.5,
        'peak_tx': df['tx_loading'].max(),
    }


def compare(df_baseline, df_battery):
    """Print comparison table between two scenarios."""
    s1 = summarise(df_baseline, "No Battery")
    s2 = summarise(df_battery, "DP Battery")

    print(f"\n  {'Metric':<30} {'No Battery':>15} {'DP Battery':>15} {'Change':>15}")
    print(f"  {'-'*30} {'-'*15} {'-'*15} {'-'*15}")
    print(f"  {'Losses (kWh)':<30} {s1['losses_kwh']:>15.2f} {s2['losses_kwh']:>15.2f} "
          f"{s2['losses_kwh']-s1['losses_kwh']:>+14.2f}")
    print(f"  {'Peak Tx (%)':<30} {s1['peak_tx']:>14.1f}% {s2['peak_tx']:>14.1f}% "
          f"{s2['peak_tx']-s1['peak_tx']:>+14.1f}%")
    print(f"  {'Voltage min (pu)':<30} {s1['v_min']:>15.4f} {s2['v_min']:>15.4f}")
    print(f"  {'Voltage max (pu)':<30} {s1['v_max']:>15.4f} {s2['v_max']:>15.4f}")
    print(f"  {'Violations':<30} {s1['violations']:>15} {s2['violations']:>15}")