import opendssdirect as dss
import math
import os

# ---- Load DSS file ----
dss_file = os.path.abspath('simple_feeder.dss')
print(f"Loading: {dss_file}")

dss.Text.Command(f'Redirect "{dss_file}"')
dss.Text.Command('Solve')

# ---- Helper function ----
VBASE = 230.0  # volts (Australian standard)

def get_bus_voltage(element_name):
    """
    Get voltage magnitude in volts and per unit (pu)
    from the first terminal of a given element.

    Parameters:
        element_name (str): e.g. 'Vsource.source', 'Load.House1'

    Returns:
        vmag (float): voltage magnitude in volts
        vpu  (float): voltage in per unit (vmag / 230V)
    """
    dss.Circuit.SetActiveElement(element_name)
    v = dss.CktElement.Voltages()   # [real, imag, real, imag, ...]
    vmag = math.sqrt(v[0]**2 + v[1]**2)
    return vmag, vmag / VBASE

# ---- Check solution ----
print(f"Solved:    {dss.Solution.Converged()}")
print(f"Frequency: {dss.Solution.Frequency()} Hz")
print(f"Num buses: {dss.Circuit.NumBuses()}")

# ---- Bus voltages ----
print("\n--- Bus Voltages ---")
vmag, vpu = get_bus_voltage('Vsource.source')
print(f"Bus: sourcebus       | Voltage: {vpu:.4f} pu | Vmag: {vmag:.2f} V")

vmag, vpu = get_bus_voltage('Load.House1')
print(f"Bus: housebus        | Voltage: {vpu:.4f} pu | Vmag: {vmag:.2f} V")

# ---- Source power ----
print("\n--- Source Power ---")
dss.Circuit.SetActiveElement('Vsource.source')
powers = dss.CktElement.Powers()    # [P_terminal1, Q_terminal1, P_terminal2, ...]
# Negative = supplying power (OpenDSS sign convention)
print(f"Active Power:   {abs(powers[0]):.2f} kW   (supplying)")
print(f"Reactive Power: {abs(powers[1]):.2f} kVAR (supplying)")

# ---- Load power ----
print("\n--- Load Power ---")
dss.Circuit.SetActiveElement('Load.House1')
powers = dss.CktElement.Powers()
print(f"House consumes: {abs(powers[0]):.2f} kW")
print(f"House Q:        {abs(powers[1]):.2f} kVAR")

# ---- Line losses ----
print("\n--- Line Losses ---")
dss.Circuit.SetActiveElement('Line.Line1')
powers = dss.CktElement.Powers()
# Terminal 1 (sending end) minus Terminal 2 (receiving end) = losses
p_loss = abs(powers[0]) - abs(powers[2])
print(f"Active Power Loss: {p_loss:.4f} kW")

# ---- Verify current ----
print("\n--- Current Verification ---")

# Method 1: Read current directly from the line
dss.Circuit.SetActiveElement('Line.Line1')
currents = dss.CktElement.Currents()  # [I1_real, I1_imag, I2_real, I2_imag, ...]
I_real = currents[0]
I_imag = currents[1]
I_mag = math.sqrt(I_real**2 + I_imag**2)
I_angle = math.degrees(math.atan2(I_imag, I_real))
print(f"Line current (from OpenDSS): {I_mag:.4f} A at {I_angle:.2f}°")

# Method 2: Compute current from load parameters (manual check)
P = 2.0   # kW
pf = 0.95
S = P / pf                          # apparent power in kVA
I_expected = S * 1000 / VBASE       # current at nominal voltage
print(f"Expected current (at nominal V): {I_expected:.4f} A")

# Method 3: Compute from S = V * I*, verifying the formula
dss.Circuit.SetActiveElement('Load.House1')
v = dss.CktElement.Voltages()
c = dss.CktElement.Currents()

V_phasor = complex(v[0], v[1])
I_phasor = complex(c[0], c[1])
S_complex = V_phasor * I_phasor.conjugate()  # S = V * I*

print(f"\nS = V × I* verification:")
print(f"  V phasor: {abs(V_phasor):.2f} V at {math.degrees(math.atan2(v[1], v[0])):.2f}°")
print(f"  I phasor: {abs(I_phasor):.4f} A at {math.degrees(math.atan2(c[1], c[0])):.2f}°")
print(f"  S = {S_complex.real/1000:.4f} kW + j{S_complex.imag/1000:.4f} kVAR")
print(f"  |S| = {abs(S_complex)/1000:.4f} kVA")
print(f"  pf = P/|S| = {S_complex.real/abs(S_complex):.4f}")