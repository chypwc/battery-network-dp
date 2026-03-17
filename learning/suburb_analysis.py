"""
Suburban Feeder — Community Battery Network Analysis (Layer 1)
=================================================================
This script loads the OpenDSS feeder model and runs power flow analysis
for multiple scenarios, extracting voltages, currents, losses, and
power flows at every bus and element.

Topology:
    11kV source → 200kVA Tx → LV bus → Junction
        ├── Branch A: 5 houses, 3 with PV, 1 community battery
        └── Branch B: 5 houses, 3 with PV, no battery

Scenarios:
    1. Base case:   loads only (evening peak, no solar)
    2. High solar:  midday, PV generating at full power
    3. Battery:     battery discharging during evening peak
    4. Battery:     battery charging during solar surplus

Requires: pip install opendssdirect.py
"""

import opendssdirect as dss
import math
import os


# ============================================================
# Helper functions
# ============================================================

def load_circuit(dss_file):
    """Load and compile the DSS file (do NOT solve yet)."""
    path = os.path.abspath(dss_file)
    if not os.path.exists(path):
        raise FileNotFoundError(f"DSS file not found: {path}")
    dss.Text.Command(f'Redirect "{path}"')
    print(f"Loaded: {path}")
    print(f"  Buses:    {dss.Circuit.NumBuses()}")
    print(f"  Elements: {dss.Circuit.NumCktElements()}")

def solve():
    """Run power flow and check convergence."""
    dss.Text.Command('Solve')
    if not dss.Solution.Converged():
        print("WARNING: Solution did not converge.")
    return dss.Solution.Converged()

def get_all_bus_voltages():
    """
    Read voltage at every bus in the circuit.

    Returns:
        list of dict: [{name, phases, v_mag_pu, v_mag_v, kv_base}, ...]

    Physics:
        Each bus may have 1 or 3 phases.
        Voltages() returns [V_re, V_im, ...] in actual volts.
        |V| = sqrt(V_re² + V_im²) for each phase.

    Note:
        CalcVoltageBases sometimes fails to propagate through
        transformers. We detect this (all buses same kv_base)
        and fall back to computing per-unit from known LV base.
    """
    results = []
    bus_names = dss.Circuit.AllBusNames()

    # First pass: collect raw data
    for name in bus_names:
        dss.Circuit.SetActiveBus(name)
        n_phases = dss.Bus.NumNodes()
        kv_base = dss.Bus.kVBase()  # phase-to-neutral kV (may be wrong)

        # Read raw voltages in volts (these are always correct)
        # v_mag_angle = dss.Bus.puVmagAngle()
        # puVmagAngle returns [mag_pu, angle, ...] — but pu may be wrong
        # Instead, use VMagAngle which returns actual volts
        v_actual = dss.Bus.VMagAngle()
        # VMagAngle returns [|V1| in volts, angle1, |V2|, angle2, ...]
        mags_v = [v_actual[2 * i] for i in range(n_phases)]

        results.append({
            'name': name,
            'phases': n_phases, 
            'v_volts': mags_v,
            'kv_base_reported': kv_base,
        })

    # Detect if CalcVoltageBases failed (all buses have same kv_base)
    unique_bases = set(r['kv_base_reported'] for r in results)
    bases_propagated = len(unique_bases) > 1

    # Assign correct kv_base and compute per-unit
    # Known bases: HV = 11 kV LL → 6.351 kV LN, LV = 0.4 kV LL → 0.2309 kV LN
    HV_BASE_LN = 11.0 / math.sqrt(3)  # 6.351 kV
    LV_BASE_LN = 0.4 / math.sqrt(3)   # 0.2309 kV = 230.9 V

    for r in results:
        if bases_propagated:
            # CalcVoltageBases worked — use reported base
            kv_base = r['kv_base_reported']
        else:
            # CalcVoltageBases failed — assign base from voltage magnitude
            # HV bus has voltages ~6350 V, LV buses have voltages ~230 V
            # Average voltage over a three-phase or single phases bus
            avg_v = sum(r['v_volts']) / len(r['v_volts']) if r['v_volts'] else 0 
            if avg_v > 1000:  # HV bus
                kv_base = HV_BASE_LN
            else:  # LV bus
                kv_base = LV_BASE_LN

        r['kv_base'] = kv_base
        r['v_pu'] = [v / (kv_base * 1000) for v in r['v_volts']]

    return results


def get_total_losses():
    """
    Read total circuit losses.

    Returns:
        (P_loss_kW, Q_loss_kVAR)

    Physics:
        P_loss = sum of I²R across all lines and transformers.
        Q_loss = sum of I²X (reactive power absorbed by inductance).
    """
    losses = dss.Circuit.Losses()
    # Losses() returns [P_watts, Q_var]
    return losses[0] / 1000, losses[1] / 1000  # convert to kW, kVAR


def get_line_data():
    """
    Read power flow through each line element.

    Returns:
        list of dict with line name, current, power, loading.

    Physics:
        Powers() returns [P1, Q1, P2, Q2, ...] per terminal (kW, kVAR).
        Currents() returns [I_re, I_im, ...] per terminal (A).
        Loading = max phase current / rated current × 100%.
    """
    results = []

    # Iterate through all line elements
    dss.Circuit.SetActiveClass('Line')
    flag = dss.ActiveClass.First() # moves the iterator to the first line and returns its index as an integer
    while flag > 0:
        # full name string like `'Line.BranchA'`
        name = dss.CktElement.Name()
        # flat list of P and Q values per phase per terminal, in kW and kVAR
        powers = dss.CktElement.Powers()
        # flat list of real and imaginary current components per phase per terminal, in amps
        currents = dss.CktElement.Currents()
        # number of phases on this line (1 or 3 in this circuit)
        n_phases = dss.CktElement.NumPhases()
        i_mags = []
        for p in range(n_phases):
            i_re = currents[2 * p]          # 0, 2, 4
            i_im = currents[2 * p + 1]      # 1, 3, 5
            i_mags.append(math.sqrt(i_re**2 + i_im**2)) # |I| = √(I_re² + I_im²)

        # Power at sending end (terminal 1)
        p_send = sum(powers[2 * p] for p in range(n_phases))
        q_send = sum(powers[2 * p + 1] for p in range(n_phases))

        results.append({
            'name': name,
            'phases': n_phases,
            'I_amps': i_mags,
            'I_max': max(i_mags),
            'P_kW': abs(p_send),
            'Q_kVAR': abs(q_send),
        })

        flag = dss.ActiveClass.Next()

    return results



def get_transformer_loading():
    """
    Read transformer loading as percentage of rated kVA.

    Returns:
        dict with transformer name, actual kVA, rated kVA, loading %.

    Physics:
        |S| = sqrt(P² + Q²) at terminal 1.
        Loading = |S| / rated_kVA × 100%.
    """
    dss.Circuit.SetActiveElement('Transformer.Tx1')
    powers = dss.CktElement.Powers()

    # Sum P and Q across all phases at terminal 1
    # Transformer has 3 phases × 2 terminals → powers has 12 entries
    # Terminal 1: powers[0..5] = [Pa, Qa, Pb, Qb, Pc, Qc]
    p_total = abs(powers[0]) + abs(powers[2]) + abs(powers[4])
    q_total = abs(powers[1]) + abs(powers[3]) + abs(powers[5])
    s_total = math.sqrt(p_total**2 + q_total**2)

    rated_kva = 200 # from DSS file
    loading_pct = s_total / rated_kva * 100

    return {
        'name': 'Transformer.Tx1',
        'P_kW': p_total,
        'Q_kVAR': q_total,
        'S_kVA': s_total,
        'rated_kVA': rated_kva,
        'loading_pct': loading_pct,
    }

    


def set_battery_state(state, kw=0):
    """
    Set community battery state.

    Args:
        state: 'CHARGING', 'DISCHARGING', or 'IDLING'
        kw: charge/discharge power in kW (positive)
            For CHARGING: battery absorbs this power from grid
            For DISCHARGING: battery injects this power into grid

    OpenDSS Storage convention:
        State=CHARGING  + kW=50  → battery absorbs 50 kW
        State=DISCHARGING + kW=50 → battery injects 50 kW
        State=IDLING → battery does nothing
    """
    dss.Circuit.SetActiveElement('Storage.CommunityBatt')
    dss.Text.Command(f'Storage.CommunityBatt.State={state}')
    if state != 'IDLING':
        dss.Text.Command(f'Storage.CommunityBatt.kW={kw}')

    


def set_solar_output(multiplier):
    """
    Scale all PV generators by a multiplier (0.0 = night, 1.0 = full sun).

    Args:
        multiplier: 0.0 to 1.0

    This simulates time of day:
        0.0 = night or heavy cloud
        0.5 = morning/afternoon or partial cloud
        1.0 = midday clear sky (full 5 kW per system)
    """
    # List all PV generators
    pv_names = ['PV_A1', 'PV_A2', 'PV_A3', 'PV_B1', 'PV_B2', 'PV_B3']

    for name in pv_names:
        if multiplier <= 0.001:
            # Disable generator entirely for night-time scenarios
            dss.Text.Command(f'Generator.{name}.enabled=no')
        else:
            dss.Text.Command(f'Generator.{name}.enabled=yes')
            kw = 5.0 * multiplier  # 5 kW rated × multiplier
            dss.Text.Command(f'Generator.{name}.kW={kw}')
    


def print_voltage_report(bus_voltages, label=""):
    """Print voltage at all LV buses with violation flags."""
    print(f"\n{'='*65}")
    print(f"  Voltage Report: {label}")
    print(f"{'='*65}")
    print(f"  {'Bus':<15} {'Ph':>3} {'V (pu)':>25}  {'V (volts)':>22}  {'Status'}")
    print(f"  {'-'*15} {'---':>3} {'-'*25}  {'-'*22}  {'------'}")

    for bus in bus_voltages:
        # Each dict has keys: name, phases, v_volts, kv_base_reported, kv_base, v_pu.
        # Skip the HV source bus — we only care about LV buses
        # HV bus has kv_base ≥ 6 kV (11kV/√3 or 11kV depending on reporting)
        # LV buses have kv_base ≈ 0.23 kV (phase-neutral) or 0.4 kV (line-line)
        if bus['kv_base'] > 5.0:
            continue

        # Skip buses with no voltage data (shouldn't happen, but defensive)
        if not bus['v_pu'] or bus['v_pu'][0] == 0:
            continue

        pu_str = ', '.join(f"{v:.4f}" for v in bus['v_pu'])
        v_str = ', '.join(f"{v:.1f}" for v in bus['v_volts'])

        # Check Australian voltage limits: 230V +10%/-6% → 0.94–1.10 pu
        violations = []
        for v in bus['v_pu']:
            if v > 1.10:
                violations.append('HIGH')
            elif v < 0.94:
                violations.append('LOW')

        status = ', '.join(violations) if violations else 'OK'
        flag = ' ⚠️' if violations else ''

        print(f"  {bus['name']:<15} {bus['phases']:>3}   {pu_str:<25} {v_str:<22}  {status}{flag}")

    # If nothing printed, show debug info
    lv_buses = [b for b in bus_voltages if b['kv_base'] <= 5.0]
    if not lv_buses:
        print(f"\n  DEBUG: No LV buses found. All bus kv_base values:")
        for bus in bus_voltages:
            print(f"    {bus['name']}: kv_base={bus['kv_base']}, phases={bus['phases']}, v_pu={bus['v_pu']}")


def print_loss_report(losses_kw, losses_kvar, label=""):
    """Print circuit losses."""
    print(f"\n  Losses ({label}):")
    print(f"    Active:   {losses_kw:.4f} kW")
    print(f"    Reactive: {losses_kvar:.4f} kVAR")


def print_line_report(line_data, label=""):
    """Print current and power through each line."""
    print(f"\n  Line Flows ({label}):")
    print(f"  {'Line':<20} {'I_max (A)':>10} {'P (kW)':>10} {'Q (kVAR)':>10}")
    print(f"  {'-'*20} {'-'*10} {'-'*10} {'-'*10}")
    for line in line_data:
        print(f"  {line['name']:<20} {line['I_max']:>10.2f} {line['P_kW']:>10.3f} {line['Q_kVAR']:>10.3f}")


# ============================================================
# Main analysis
# ============================================================

def run_scenario(label, solar_mult, batt_state, batt_kw=0):
    """
    Run one scenario and print full results.

    Args:
        label: description of this scenario
        solar_mult: solar output multiplier (0.0–1.0)
        batt_state: 'IDLING', 'CHARGING', or 'DISCHARGING'
        batt_kw: battery power in kW
    """
    print(f"\n{'#'*65}")
    print(f"# SCENARIO: {label}")
    print(f"{'#'*65}")

    # Configure solar and battery
    set_solar_output(solar_mult)
    set_battery_state(batt_state, batt_kw)

    # Solve power flow
    converged = solve()
    print(f"  Converged: {converged}")

    # Extract results
    bus_v = get_all_bus_voltages()
    losses = get_total_losses()
    lines = get_line_data()
    tx = get_transformer_loading()

    # Print reports
    print_voltage_report(bus_v, label)
    print_loss_report(losses[0], losses[1], label)
    print_line_report(lines, label)
    print(f"\n  Transformer loading: {tx['S_kVA']:.1f} kVA / {tx['rated_kVA']} kVA = {tx['loading_pct']:.1f}%")

    # Return data for comparison
    return {
        'label': label,
        'bus_voltages': bus_v,
        'losses_kw': losses[0],
        'losses_kvar': losses[1],
        'lines': lines,
        'tx': tx,
    }


def main():
    """Run all scenarios and compare results."""

    # Load the DSS circuit
    load_circuit('suburb_feeder.dss')

    # ---- Scenario 1: Evening peak, no solar ----
    # Typical 6pm: all houses consuming, no PV generation.
    # This is the baseline — shows normal voltage drop.
    s1 = run_scenario(
        label="Evening peak — no solar, no battery",
        solar_mult=0.0,
        batt_state='IDLING',
    )

    # ---- Scenario 2: Midday, full solar, no battery ----
    # Typical 12pm: houses at low demand, PV at full output.
    # PV injects power back into grid → voltage RISES.
    # This may cause overvoltage at end of feeder.
    s2 = run_scenario(
        label="Midday — full solar, no battery",
        solar_mult=1.0,
        batt_state='IDLING',
    )

    # ---- Scenario 3: Midday, full solar, battery CHARGING (oversized) ----
    # Battery charges at 50 kW — more than local solar surplus.
    # EXPECT: worse performance (draws power from grid through transformer).
    s3 = run_scenario(
        label="Midday — solar, battery charging 50 kW (oversized)",
        solar_mult=1.0,
        batt_state='CHARGING',
        batt_kw=50,
    )

    # ---- Scenario 4: Midday, full solar, battery CHARGING (right-sized) ----
    # Solar produces ~30 kW, houses consume ~10 kW at midday.
    # Net surplus ≈ 20 kW. Battery absorbs just the surplus.
    # EXPECT: voltage rise reduced, losses reduced vs Scenario 2.
    s4 = run_scenario(
        label="Midday — solar, battery charging 15 kW (matched)",
        solar_mult=1.0,
        batt_state='CHARGING',
        batt_kw=15,
    )

    # ---- Scenario 5: Evening peak, battery DISCHARGING (oversized) ----
    # Battery injects 80 kW but local load is only ~28 kW.
    # EXPECT: excess power flows backward, increases losses.
    s5 = run_scenario(
        label="Evening — battery discharging 80 kW (oversized)",
        solar_mult=0.0,
        batt_state='DISCHARGING',
        batt_kw=80,
    )

    # ---- Scenario 6: Evening peak, battery DISCHARGING (right-sized) ----
    # Battery injects 20 kW — serves ~70% of local demand.
    # EXPECT: voltage drop reduced, losses reduced, Tx loading reduced.
    s6 = run_scenario(
        label="Evening — battery discharging 20 kW (matched)",
        solar_mult=0.0,
        batt_state='DISCHARGING',
        batt_kw=20,
    )

    all_scenarios = [s1, s2, s3, s4, s5, s6]

    # ---- Summary comparison ----
    print(f"\n{'='*72}")
    print(f"  SCENARIO COMPARISON")
    print(f"{'='*72}")
    print(f"  {'Scenario':<55} {'Losses':>8} {'Tx Load':>8}")
    print(f"  {'':55} {'(kW)':>8} {'(%)':>8}")
    print(f"  {'-'*55} {'-'*8} {'-'*8}")
    for s in all_scenarios:
        print(f"  {s['label']:<55} {s['losses_kw']:>8.3f} {s['tx']['loading_pct']:>7.1f}%")

    # ---- Voltage comparison at Branch A end (most stressed bus) ----
    print(f"\n  Voltage at Branch A end (brA):")
    print(f"  {'Scenario':<55} {'Ph1':>7} {'Ph2':>7} {'Ph3':>7}")
    print(f"  {'-'*55} {'-'*7} {'-'*7} {'-'*7}")
    for s in all_scenarios:
        for bus in s['bus_voltages']:
            if bus['name'] == 'bra':  # OpenDSS lowercases bus names
                pu = bus['v_pu']
                while len(pu) < 3:
                    pu.append(0)
                print(f"  {s['label']:<55} {pu[0]:>7.4f} {pu[1]:>7.4f} {pu[2]:>7.4f}")


if __name__ == '__main__':
    main()