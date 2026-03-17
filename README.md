# Community Battery Techno-Economic and Network Analysis

## Overview

Community batteries are shared energy storage systems installed on suburban distribution networks, charging from rooftop solar during the day and discharging during evening peak demand. They provide two forms of value: **arbitrage revenue** (buying electricity when cheap, selling when expensive) and **network support** (preventing voltage violations that would otherwise require costly infrastructure upgrades).

This project builds a decision-support tool that jointly optimises these two objectives. A dynamic programming (DP) solver finds the revenue-maximising battery dispatch schedule using real NEM spot prices. An OpenDSS power flow model verifies whether that schedule is physically safe for the distribution network. A feedback loop iterates between the two until the dispatch is both economically optimal and network-feasible.

The tool is applied to a representative 32-house Australian suburban feeder with high rooftop solar penetration, producing concrete sizing and dispatch recommendations: what battery capacity is needed, what dispatch limit should the network operator impose, and what is the revenue cost of network safety.

## Battery Dispatch Optimisation

### The Arbitrage Problem

NEM spot prices vary throughout the day — low during midday solar surplus (sometimes negative), high during evening peak demand. A battery operator maximises revenue by charging when prices are low and discharging when prices are high. The challenge is deciding, at each half-hour, how much to charge or discharge given the current state of charge, the current price, and the knowledge that future prices may be higher or lower.

This is a finite-horizon deterministic dynamic programming problem. The price sequence is known in advance (day-ahead or historical), the battery physics are deterministic, and the planning horizon is one day (48 half-hour periods).

### Bellman Equation

The optimal dispatch is found by backward induction over the value function:

$$V_t(s) = \max_{a \in \mathcal{A}(s,t)} \left[ r(s, a, p_t) + V_{t+1}(s') \right], \quad t = T{-}1, \ldots, 0$$

with terminal condition $V_T(s) = 0$ for all $s$.

| Symbol | Code | Meaning |
|--------|------|---------|
| $t$ | `t` | Time step (0 = 00:00, ..., 47 = 23:30) |
| $s$ | `soc` | State of charge (kWh) |
| $a$ | `action_kw` | Charge (+kW) or discharge (−kW) |
| $p_t$ | `prices[t]` | NEM spot price (A\$/MWh) |
| $s'$ | `s_next` | SoC after action $a$ |
| $V_t(s)$ | `V[t][i]` | Max future revenue from state $s$ at time $t$ |

### State Transition

The battery's state of charge evolves differently for charging and discharging due to conversion losses:

$$s' = \begin{cases} s + \eta_c \cdot a \cdot \Delta t & \text{if } a \geq 0 \text{ (charging)} \\\\ s + \dfrac{a}{\eta_d} \cdot \Delta t & \text{if } a < 0 \text{ (discharging)} \end{cases}$$

When charging, the grid delivers $a \cdot \Delta t$ kWh but only $\eta_c \cdot a \cdot \Delta t$ reaches the battery (the rest is lost as heat). When discharging, the battery must release $|a| \cdot \Delta t / \eta_d$ kWh internally to deliver $|a| \cdot \Delta t$ to the grid. Parameters: $\eta_c = \eta_d = 0.95$, $\Delta t = 0.5$ h.

### Reward Function

$$r(s, a, p_t) = -\frac{p_t}{1000} \cdot a \cdot \Delta t - c_{\text{deg}} \cdot |a| \cdot \Delta t$$

The first term is arbitrage revenue. When charging ($a > 0$), the battery buys electricity at price $p_t$, producing a cost (negative reward). When discharging ($a < 0$), the battery sells electricity, producing income (positive reward). The second term is battery degradation cost ( $c_{\text{deg}} = 0.02$ A\$/kWh throughput), representing the shortened battery lifetime from cycling.

### Feasible Action Set

$$\mathcal{A}(s, t) = \left\lbrace a \in [-\bar{a}, \bar{a}] \mid s_{\min} \leq s' \leq s_{\max} \right\rbrace$$

Actions are bounded by the dispatch limit $\bar{a}$ (kW) and by the requirement that the next SoC stays within the battery's operating range: $s_{\min} = 0.1 \times E_{\text{rated}}$ (reserve) to $s_{\max} = E_{\text{rated}}$ (full capacity).

### Discretisation

The SoC and action spaces are discretised into $n_s$ and $n_a$ evenly spaced grid points. The value function at off-grid states is obtained by linear interpolation of $V_{t+1}$. Total computation per solve: $T \times n_s \times n_a$ evaluations (typically 48 × 81 × 81 ≈ 315,000, runs in under a second).

### Price Data

Real AEMO NSW1 spot prices (the ACT falls within the NSW1 NEM region). Data is downloaded from AEMO's public aggregated price and demand portal at 5-minute dispatch resolution, then resampled to 30-minute settlement periods by averaging six consecutive dispatch prices.

## Distribution Network Model

### Feeder Topology

The study network is a representative Australian suburban LV feeder with high rooftop solar penetration:

```
[ 11 kV Grid ]
       │
 ┌─────┴─────┐
 │ Tx1 200kVA│  11kV / 0.4kV
 └─────┬─────┘
       │
    (lv_bus)
       │
   [ Trunk ]  150m, 3-phase underground cable
       │
  (junction)
       │
  ┌────┴────┐
  │         │
BranchA  BranchB           ← identical topology, symmetric loads
  │         │
  ├─ A1 ──  ├─ B1 ──       50m:  4 houses, 2 × 6.6kW PV
  ├─ A2 ──  ├─ B2 ──      100m:  4 houses, 3 × 6.6kW PV
  ├─ A3 ──  ├─ B3 ──      150m:  4 houses, 2 × 6.6kW PV
  └─ A4 ──  └─ B4 ──      200m:  4 houses, 3 × 6.6kW PV
     │
  [Battery]                 ← community battery at end of Branch A
```

Branch A and Branch B are identical in topology, cable impedance, house loads, and solar capacity. The only difference is the community battery at Node A4. Branch B serves as the control group: any voltage difference between A4 and B4 at the same time step is attributable to the battery.

### Network Parameters

| Parameter | Value |
|-----------|-------|
| Houses | 32 (16 per branch) |
| Peak load | 96 kW |
| PV systems | 20 × 6.6 kW (10 per branch) |
| Solar capacity | 132 kW |
| Transformer | 200 kVA, 11kV/0.4kV |
| Cable | 95mm² Al, R=0.32 Ω/km, X=0.08 Ω/km |
| Total feeder length | 350m (trunk to end-of-line) |
| Voltage limits | 0.94–1.10 pu (AS 61000.3.100: 230V +10%/−6%) |

### Phase-Level Distribution

At each node, houses and PV systems are distributed across the three phases to represent realistic unbalanced loading:

```
        [ Node A2 ]
            │
  ┌─────────┼─────────┐
Phase 1   Phase 2   Phase 3
  │         │         │
 House     House     House      ← 3.0, 3.3, 2.6 kW
 House      —         —         ← 3.1 kW
 PV        PV        PV         ← 6.6 kW each
```

The community battery connects to all three phases, balancing its charge/discharge across the feeder.

### Baseline Violations

Without the battery, the feeder has 11 voltage violations (V < 0.94 pu):

| Period | Time | Cause | Worst voltage |
|--------|------|-------|--------------|
| Morning (3 periods) | 06:00–07:00 | High load, no solar | 0.939 pu |
| Evening (8 periods) | 17:00–20:30 | Peak load, no solar | 0.929 pu |

These violations occur at Nodes A4 and B4 (end-of-feeder, furthest from the transformer) where voltage drop is greatest.

## Two-Layer Framework

### Layer 1: OpenDSS Network Model

The OpenDSS layer runs snapshot power flow at each half-hour time step. At each step, load multipliers, solar multipliers, and battery dispatch are set via the `opendssdirect` Python interface. The solver returns bus voltages, circuit losses, and transformer loading.

### Layer 2: DP Dispatch Optimiser

The DP layer solves the Bellman equation to produce a 48-element dispatch schedule (kW per half-hour). It uses real AEMO prices and the battery physical model but has no knowledge of the distribution network.

### Feedback Loop

The integration layer coordinates the two layers. The unconstrained DP dispatch may cause voltage violations when run through OpenDSS (e.g., the battery empties too early, leaving the evening peak unsupported). The feedback loop adds network constraints to the DP and re-solves:

```
constraints ← None

for iteration = 1 to max_iterations:

    if constraints is None:
        dispatch ← DP.solve(prices)
    else:
        dispatch ← DP.solve_constrained(prices, constraints)

    violations ← OpenDSS.check(dispatch, load_profile, solar_profile)

    if violations = 0:
        return dispatch                        ← converged

    if violations unchanged from last iteration:
        return dispatch                        ← battery capacity limit reached

    constraints ← generate_constraints(violations, battery)

return dispatch
```

### Network-Constrained Feasible Set

When constraints are active, the DP's feasible action set is restricted:

$$\mathcal{A}_c(s, t) = \left\lbrace a \in \mathcal{A}(s,t) \mid a \leq a_{\min}^{\text{dis}}(t), a \leq a_{\max}^{\text{chg}}(t), s' \geq s_{\min}^{\text{net}}(t{+}1) \right\rbrace$$

| Constraint | Source | Purpose |
|------------|--------|---------|
| $a_{\min}^{\text{dis}}(t) < 0$ | Undervoltage at period $t$ | Force minimum discharge power |
| $a_{\max}^{\text{chg}}(t)$ | Overvoltage at period $t$ | Limit charging power |
| $s_{\min}^{\text{net}}(t{+}1)$ | Future undervoltage periods | Preserve energy for later discharge |

The minimum discharge power at each violation period is determined by binary search in OpenDSS: test discharge levels from 10 to 100 kW and find the smallest that lifts $V_{\min}$ above 0.94 pu. When the total energy required to cover all violations exceeds the battery's usable capacity, the constraint generator prioritises the latest block (evening peak) where violations are most severe.

## Results

### Sensitivity: Dispatch Limit × Battery Capacity

| Limit | Capacity | Revenue/day | Violations | Eliminated | Losses (kWh) |
|-------|----------|-------------|-----------|------------|--------------|
| base  | ---      | ---         | 11        | ---        | 57.2         |
| ±30kW | 400kWh   | A\$17       | 8         | 3/11       | 59.4         |
| ±50kW | 200kWh   | A\$28       | 3         | 8/11       | 62.2         |
| ±50kW | 300kWh   | A\$32       | 1         | 10/11      | 60.9         |
| **±50kW** | **400kWh** | **A\$36** | **0**  | **11/11**  | **60.7**     |
| ±80kW | 400kWh   | A\$48       | 3         | 8/11       | 79.1         |
| ±100kW| 400kWh   | A\$39       | 3         | 8/11       | 86.4         |

### Key Findings

**1. Only ±50kW / 400kWh achieves full network feasibility.** At this configuration, the unconstrained DP dispatch is already network-safe — the economic optimum and network optimum coincide. The battery is large enough to discharge throughout the entire evening peak while pursuing arbitrage revenue.

**2. ±30kW is below the voltage correction threshold.** The cable impedance between the junction and Node A4 requires approximately 40–50 kW of injection to produce the 0.012 pu voltage rise needed to cross the 0.94 pu limit. At 30 kW, the voltage rise is insufficient regardless of battery capacity.

**3. ±80–100kW causes overvoltage.** High-power charge and discharge drives $V_{\max}$ to 1.096–1.102 pu, approaching or exceeding the 1.10 upper limit. The battery creates new voltage problems while trying to fix existing ones.

**4. Battery energy capacity (kWh) is the binding constraint.** At ±50kW, increasing capacity from 200→300→400 kWh reduces violations from 3→1→0. Each half-hour of discharge at 50 kW consumes 26.3 kWh from the battery. The evening block (8 periods) requires 210 kWh — exceeding the 200 kWh battery's 180 kWh usable capacity. Increasing the power rating cannot fix this; only more energy storage can.

**5. Losses increase with dispatch power following $I^2 R$ scaling.** From 57.2 kWh (baseline) to 86.4 kWh at ±100kW (+51%). The battery operator earns arbitrage revenue but the DNSP bears the additional loss costs — a cost externalisation that network tariff design must address.

## Project Structure

```
community-battery/
├── download_prices.py              ← Download AEMO price data
├── run_timeseries.py               ← Baseline vs DP-optimised comparison
├── run_feedback.py                 ← Sensitivity analysis
│
├── dss/
│   └── suburb_feeder_32.dss        ← OpenDSS circuit definition
│
├── src/
│   ├── dp/                         ← Layer 2: DP optimiser
│   │   ├── battery.py                  Battery physical model
│   │   ├── solver.py                   Bellman equation solver
│   │   └── prices.py                   AEMO data loader
│   │
│   ├── opendss/                    ← Layer 1: Network model
│   │   ├── network.py                  OpenDSS interface
│   │   ├── profiles.py                 Load & solar profiles
│   │   └── feeders.py                  Element configuration
│   │
│   └── integration/                ← Feedback loop
│       ├── timeseries.py               Time-series simulation
│       ├── constraints.py              Constraint generation
│       └── feedback.py                 Iterative solver
│
└── data/aemo/                      ← Downloaded price data
```

## Quick Start

```bash
pip install opendssdirect.py numpy pandas requests

python download_prices.py        # Download AEMO NSW1 price data
python run_timeseries.py         # Baseline vs DP battery comparison
python run_feedback.py           # Full sensitivity analysis
```

## Dependencies

| Package | Purpose |
|---------|---------|
| `opendssdirect.py` | OpenDSS power flow engine |
| `numpy` | Numerical computation |
| `pandas` | Data handling and resampling |
| `requests` | AEMO data download |
