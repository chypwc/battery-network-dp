"""
Load and solar time-series profiles.

Synthetic profiles for testing. In production, replace with
real Ausgrid Solar Home data or BOM solar irradiance data.
"""

import numpy as np

def generate_load_profile(T=48):
    """
    Normalised 24-hour residential load profile.

    Returns multipliers 0-1, where 1.0 = peak load (kW in DSS file).
    Typical ACT winter pattern.
    
    Index 0 = 00:00, index 1 = 00:30, ..., index 34 = 17:00, ..., index 47 = 23:30.
    """
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


def generate_solar_profile(T=48, season='winter'):
    """
    Normalised 24-hour solar generation profile.

    Returns multipliers 0–1, where 1.0 = rated PV output.
    """
    solar = np.zeros(T)

    if season == 'winter':
        sunrise = 7.0
        sunset = 17.0
        peak_factor = 0.75
    else:  # summer
        sunrise = 6.0
        sunset = 20.5
        peak_factor = 0.95

    daylight_hours = sunset - sunrise

    for i in range(T):
        hour = i / 2
        if sunrise <= hour <= sunset:
            solar[i] = max(0, np.sin((hour - sunrise) / daylight_hours * np.pi)) * peak_factor

    return solar


if __name__ == '__main__':
    import numpy as np

    load = generate_load_profile()
    print(f"Length: {len(load)}")
    print(f"Range: {load.min():.2f} – {load.max():.2f}")
    print(f"Peak index: {load.argmax()} → hour {load.argmax() / 2:.1f}")

    # Spot checks
    print(f"00:00 (index 0):  {load[0]:.2f}")   # expect 0.35
    print(f"07:00 (index 14): {load[14]:.2f}")   # expect 0.80
    print(f"12:00 (index 24): {load[24]:.2f}")   # expect 0.40
    print(f"18:00 (index 36): {load[36]:.2f}")   # expect 0.95
    print(f"22:00 (index 44): {load[44]:.2f}")   # expect 0.45