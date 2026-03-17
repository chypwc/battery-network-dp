"""
Feeder configurations — element names and parameters for each DSS model.

Each config is a dict consumed by the time-series and feedback modules.
This keeps the DSS element names in one place instead of scattered
across multiple scripts.
"""
FEEDER_32 = {
    'dss_file': 'dss/suburb_feeder_32.dss',
    'name': 'Suburb 32-house feeder',

    # All load names and their peak kW (from the DSS file)
    'load_names': {
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
    },

    # All PV generator names
    'pv_names': [
        'PV_A1a', 'PV_A1b',
        'PV_A2a', 'PV_A2b', 'PV_A2c',
        'PV_A3a', 'PV_A3b',
        'PV_A4a', 'PV_A4b', 'PV_A4c',
        'PV_B1a', 'PV_B1b',
        'PV_B2a', 'PV_B2b', 'PV_B2c',
        'PV_B3a', 'PV_B3b',
        'PV_B4a', 'PV_B4b', 'PV_B4c',
    ],

    'pv_rated_kw': 6.6,  # kW per PV system

    # Branch bus names for voltage monitoring (ordered by distance)
    'branch_a_buses': ['lv_bus', 'junction', 'bra1', 'bra2', 'bra3', 'bra4'],
    'branch_b_buses': ['lv_bus', 'junction', 'brb1', 'brb2', 'brb3', 'brb4'],

    # Battery bus
    'battery_bus': 'bra4',

    # Transformer
    'tx_rated_kva': 200,
}


if __name__ == '__main__':
    f = FEEDER_32
    total_load = sum(f['load_names'].values())
    total_solar = len(f['pv_names']) * f['pv_rated_kw']

    print(f"Feeder: {f['name']}")
    print(f"Houses: {len(f['load_names'])}")           # expect 32
    print(f"Peak load: {total_load:.0f} kW")           # expect ~96
    print(f"PV systems: {len(f['pv_names'])}")         # expect 20
    print(f"Solar capacity: {total_solar:.0f} kW")     # expect 132
    print(f"Branch A buses: {f['branch_a_buses']}")
    print(f"Battery at: {f['battery_bus']}")