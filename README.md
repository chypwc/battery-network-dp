# Community Battery Techno-Economic and Network Analysis

## Overview

Community batteries are shared energy storage systems installed on suburban distribution networks, charging from rooftop solar during the day and discharging during evening peak demand. They provide two forms of value: **arbitrage revenue** (buying electricity when cheap, selling when expensive) and **network support** (preventing voltage violations that would otherwise require costly infrastructure upgrades).

This project builds a decision-support tool that jointly optimises these two objectives using two complementary methods. A dynamic programming (DP) solver finds the revenue-maximising battery dispatch schedule using real NEM spot prices. A Q-learning agent extends this by embedding network voltage constraints directly into the reward signal, discovering dispatch strategies that are both profitable and network-safe.

Both methods are verified against an OpenDSS power flow model of a representative 32-house Australian suburban feeder with high rooftop solar penetration. The tool produces concrete sizing and dispatch recommendations: what battery capacity is needed, what dispatch limit should the network operator impose, and what is the revenue cost of network safety.

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

The first term is arbitrage revenue. When charging ($a > 0$), the battery buys electricity at price $p_t$, producing a cost (negative reward). When discharging ($a < 0$), the battery sells electricity, producing income (positive reward). The second term is battery degradation cost ($c_{\text{deg}} = 0.02$ A\$/kWh throughput), representing the shortened battery lifetime from cycling.

### Feasible Action Set

$$\mathcal{A}(s, t) = \lbrace a \in [-\bar{a}, \bar{a}] \mid s_{\min} \leq s' \leq s_{\max} \rbrace$$

Actions are bounded by the dispatch limit $\bar{a}$ (kW) and by the requirement that the next SoC stays within the battery's operating range: $s_{\min} = 0.1 \times E_{\text{rated}}$ (reserve) to $s_{\max} = E_{\text{rated}}$ (full capacity).

### Discretisation

The SoC and action spaces are discretised into $n_s$ and $n_a$ evenly spaced grid points. The value function at off-grid states is obtained by linear interpolation of $V_{t+1}$. Total computation per solve: $T \times n_s \times n_a$ evaluations (typically 48 x 81 x 81 = 315,000, runs in under a second).

### Price Data

Real AEMO NSW1 spot prices (the ACT falls within the NSW1 NEM region). Data is downloaded from AEMO's public aggregated price and demand portal at 5-minute dispatch resolution, then resampled to 30-minute settlement periods by averaging six consecutive dispatch prices.

### Q-Learning Extension

The DP solver maximises revenue but has no knowledge of network voltage. Violations are only detected afterward, and the feedback loop's heuristic constraints cannot discover strategies that are revenue-suboptimal but network-optimal.

Q-learning addresses this by embedding the network response directly into the reward signal. The agent interacts with an OpenDSS-based environment where each action produces both revenue and a voltage violation penalty.

**Environment.** At each time step $t$, the agent observes state $(s_t, t)$, selects an action $a_t$, and receives:

$$r_t = r_{\text{arb}}(s_t, a_t, p_t) - \lambda \cdot n_{\text{viol},t}$$

where $r_{\text{arb}}$ is the arbitrage reward (same as DP), $\lambda$ is the violation penalty, and $n_{\text{viol},t}$ is the number of bus phases with voltage outside the 0.94–1.10 pu range, determined by OpenDSS power flow at each step.

**Q-learning update.** The agent maintains a Q-table $Q(s, t, a)$ indexed by discretised SoC bin, time step, and action index. After each transition:

$$Q(s_t, t, a_t) \leftarrow Q(s_t, t, a_t) + \alpha_t \left[ r_t + \gamma \max_{a'} Q(s_{t+1}, t{+}1, a') - Q(s_t, t, a_t) \right]$$

Both the learning rate $\alpha_t$ and exploration rate $\epsilon_t$ decay exponentially over training episodes.

**Two-phase training.** A single penalty value cannot simultaneously encourage arbitrage exploration and violation avoidance. Training proceeds in two phases:

| | Phase 1: Arbitrage | Phase 2: Network Safety |
|---|---|---|
| Objective | Learn profitable dispatch | Refine for voltage feasibility |
| Penalty $\lambda$ | 0 | 5.0 – 10.0 |
| OpenDSS calls | None (skip_network) | Every time step |
| Q-table init | DP value function | Phase 1 output |
| Epsilon | 0.3 to 0.05 | 0.1 to 0.001 |
| Episodes | 30,000 – 50,000 | 50,000 – 100,000 |

Phase 1 uses penalty=0 and skips OpenDSS calls entirely, running approximately 100x faster than Phase 2. The Q-table is initialised from the DP value function: for each SoC bin and time step, the DP's optimal action receives a Q-value equal to the interpolated value $V_t(s)$. This gives the agent a strong arbitrage foundation without requiring hundreds of thousands of exploration episodes.

Phase 2 enables OpenDSS and introduces the violation penalty. The agent starts with a profitable strategy from Phase 1 and makes targeted adjustments at violation periods. Lower initial epsilon (0.1) protects the good arbitrage strategy while allowing exploration at critical evening periods.

**Network-constrained feasible set (feedback loop).** When the DP feedback loop is used instead of Q-learning, the feasible set is restricted by heuristic constraints:

$$\mathcal{A}_c(s, t) = \lbrace a \in \mathcal{A}(s,t) \mid a \leq a_{\min}^{\text{dis}}(t), a \leq a_{\max}^{\text{chg}}(t), s' \geq s_{\min}^{\text{net}}(t{+}1) \rbrace$$

| Constraint | Source | Purpose |
|------------|--------|---------|
| $a_{\min}^{\text{dis}}(t) < 0$ | Undervoltage at period $t$ | Force minimum discharge power |
| $a_{\max}^{\text{chg}}(t)$ | Overvoltage at period $t$ | Limit charging power |
| $s_{\min}^{\text{net}}(t{+}1)$ | Future undervoltage periods | Preserve energy for later discharge |

The minimum discharge power at each violation period is determined by binary search in OpenDSS.

For full mathematical details of the DP solver, feedback loop, Q-learning update rule, two-phase training, and hyperparameter configurations, see [methods.md](doc/methods.md).

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

Branch A and Branch B are identical in topology, cable impedance, house loads, and solar capacity. The only difference is the community battery at Node A4. Branch B serves as the control group.

### Network Parameters

| Parameter | Value |
|-----------|-------|
| Houses | 32 (16 per branch) |
| Peak load | 96 kW |
| PV systems | 20 x 6.6 kW (10 per branch) |
| Solar capacity | 132 kW |
| Transformer | 200 kVA, 11kV/0.4kV |
| Cable | 95mm² Al, R=0.32 ohm/km, X=0.08 ohm/km |
| Total feeder length | 350m (trunk to end-of-line) |
| Voltage limits | 0.94–1.10 pu (AS 61000.3.100: 230V +10%/-6%) |

### Baseline Violations

Without the battery, the feeder has 11 voltage violations (V < 0.94 pu):

| Period | Time | Cause | Worst voltage |
|--------|------|-------|--------------|
| Morning (3 periods) | 06:00–07:00 | High load, no solar | 0.939 pu |
| Evening (8 periods) | 17:00–20:30 | Peak load, no solar | 0.929 pu |

These violations occur at Nodes A4 and B4 (end-of-feeder, furthest from the transformer) where voltage drop is greatest.

## Results

### DP Sensitivity: Dispatch Limit x Battery Capacity

| Limit | Capacity | Revenue/day | Violations | Eliminated | Losses (kWh) |
|-------|----------|-------------|-----------|------------|--------------|
| base  | ---      | ---         | 11        | ---        | 57.2         |
| ±30kW | 400kWh   | A\$17       | 8         | 3/11       | 59.4         |
| ±50kW | 200kWh   | A\$28       | 3         | 8/11       | 62.2         |
| ±50kW | 300kWh   | A\$32       | 1         | 10/11      | 60.9         |
| **±50kW** | **400kWh** | **A\$36** | **0**  | **11/11**  | **60.7**     |
| ±80kW | 400kWh   | A\$48       | 3         | 8/11       | 79.1         |
| ±100kW| 400kWh   | A\$39       | 3         | 8/11       | 86.4         |

### DP vs Q-Learning: Head-to-Head

| Config | DP Revenue | DP Violations | RL Revenue | RL Violations | Revenue Gap |
|--------|-----------|--------------|-----------|--------------|-------------|
| **Baseline (no battery)** | **—** | **11** | **—** | **—** | **—** |
| ±50kW / 200kWh | A\$28.38 | 4 | A\$24.98 | **0** | -A\$3.40 |
| ±50kW / 300kWh | A\$32.69 | 0 | A\$32.55 | 0 | -A\$0.14 |
| ±50kW / 400kWh | A\$35.92 | 0 | A\$35.90 | 0 | -A\$0.02 |
| ±80kW / 200kWh | A\$37.08 | 6 | A\$34.44 | **0** | -A\$2.64 |
| ±80kW / 300kWh | A\$44.26 | 4 | A\$42.50 | **0** | -A\$1.76 |
| ±80kW / 400kWh | A\$49.36 | 3 | A\$48.93 | **0** | -A\$0.43 |
| ±100kW / 200kWh | A\$41.23 | 10 | A\$36.31 | **0** | -A\$4.92 |
| ±100kW / 300kWh | A\$50.54 | 10 | A\$44.53 | **0** | -A\$6.00 |
| ±100kW / 400kWh | A\$56.56 | 10 | A\$48.51 | **0** | -A\$8.05 |

### Network Impact

| Config | DP Losses | RL Losses | Reduction | DP Peak Tx | RL Peak Tx |
|--------|----------|----------|-----------|-----------|-----------|
| **Baseline (no battery)** | **57.2 kWh** | **57.2 kWh** | **—** | **49.7%** | **49.7%** |
| ±50kW / 200kWh | 62.2 | 55.1 | -11% | 52.1% | 52.2% |
| ±80kW / 200kWh | 70.6 | 64.1 | -9% | 64.8% | 65.0% |
| ±80kW / 300kWh | 76.7 | 72.1 | -6% | 65.0% | 65.0% |
| ±80kW / 400kWh | 81.4 | 78.0 | -4% | 65.0% | 65.0% |
| ±100kW / 200kWh | 78.3 | 68.6 | -12% | 73.5% | 67.0% |
| ±100kW / 300kWh | 85.8 | 73.6 | -14% | 73.5% | 67.0% |
| ±100kW / 400kWh | 95.4 | 81.8 | -14% | 73.5% | 67.0% |

Losses represent electrical energy dissipated as heat in cables and the transformer. When current flows through a conductor with resistance $R$, the power lost is $P_{\text{loss}} = I^2 R$. Higher battery dispatch power drives higher current, increasing losses quadratically. RL consistently reduces losses compared to DP because the oscillating evening strategy uses lower sustained current than DP's aggressive continuous discharge.

### Key Findings

**1. Q-learning achieves 0 violations across all configurations.** DP achieves 0 violations in only 2 of 9 configurations (±50kW with 300+ kWh). Q-learning eliminates all violations by learning the voltage response to battery actions through direct interaction with the OpenDSS network model.

**2. DP provides the revenue upper bound; RL provides the feasibility boundary.** DP answers "what is the maximum possible revenue?" while RL answers "what is the maximum revenue achievable without violating network constraints?" Together they bracket the design space.

**3. The revenue cost of network safety is small for well-sized batteries.** At ±80kW/400kWh, the gap is only A\$0.43/day (A\$157/year). At ±50kW/200kWh, it is A\$3.40/day (A\$1,241/year). The cost increases with dispatch limit and decreases with battery capacity.

**4. ±30kW is below the voltage correction threshold.** The cable impedance requires approximately 40–50 kW of injection to produce the 0.012 pu voltage rise needed to cross the 0.94 pu limit. Below this, no algorithm can fix violations.

**5. ±80–100kW causes overvoltage under DP dispatch.** The DP charges and discharges at full power, driving V_max to 1.096–1.102 pu. Q-learning moderates the dispatch to stay within both voltage limits simultaneously.

**6. Battery energy capacity (kWh) is the binding constraint for DP.** At ±50kW, the DP needs 400 kWh for 0 violations. Q-learning achieves 0 violations at 200 kWh — a 50% reduction in minimum battery size.

**7. RL reduces network losses by 4–14%.** The oscillating strategy uses lower sustained current than DP's aggressive dispatch. The DNSP benefits from both fewer violations and lower loss costs.

For the policy implications, see [policy implications.md](doc/policy%20implications.md).

### How Q-Learning Eliminates Violations

The Q-learning agent independently discovers three strategies that the revenue-maximising DP cannot find.

**Pre-charging before morning peak.** RL charges at t=11 (05:30) and discharges slightly at t=12 (06:00, A\$101/MWh). The DP ignores this period because the price isn't high enough for profitable discharge. But RL learned from OpenDSS that even 10 kW of discharge at 06:00 lifts morning voltage above 0.94 pu. The revenue cost is approximately A\$0.50 per eliminated violation.

**Conservative early evening discharge.** At t=32–34 (16:00–17:00), RL discharges less than DP to preserve energy for the critical late evening periods. For example, at ±80kW/400kWh, RL discharges -45 kW at t=32 where DP discharges -80 kW, saving 18 kWh. In the most extreme case (±100kW/200kWh at t=34), RL charges +60 kW during A\$137/MWh evening peak — paying A\$3.42 to store energy for later voltage support.

**Late evening oscillation.** At t=38–42 (19:00–21:00), where DP's battery is empty and cannot provide voltage support, RL rapidly cycles between charging and discharging. At ±50kW/200kWh:

```
t=38  +40 kW (charge — refill battery)
t=39  −45 kW (discharge — support voltage)
t=40  +45 kW (charge — refill battery)
t=41  −40 kW (discharge — support voltage)
t=42  −15 kW (final discharge)
```

Each discharge period injects power into the feeder, lifting voltage above 0.94 pu. Each charge period refills just enough energy for the next discharge. The strategy is revenue-negative (~A\$0.50 loss per cycle) but prevents the most severe voltage violations. The oscillation pattern adapts to battery capacity: 200 kWh batteries require 3–4 cycles, 300 kWh need 1–2 cycles, and 400 kWh batteries can sustain discharge with minor adjustments.

These strategies require knowledge of the voltage response to battery actions — knowledge that only exists in the OpenDSS power flow model. The DP feedback loop cannot discover the oscillating strategy because it is revenue-suboptimal at every individual time step.

## Project Structure

```
community-battery/
├── download_prices.py              ← Download AEMO price data
├── run_timeseries.py               ← Baseline vs DP-optimised comparison
├── run_feedback.py                 ← DP sensitivity analysis
├── run_qlearning.py                ← Q-learning sensitivity analysis
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
│   │   ├── profiles.py                 Load and solar profiles
│   │   └── feeders.py                  Element configuration
│   │
│   ├── integration/                ← DP feedback loop
│   │   ├── timeseries.py               Time-series simulation
│   │   ├── constraints.py              Constraint generation
│   │   └── feedback.py                 Iterative solver
│   │
│   └── rl/                         ← Q-learning extension
│       ├── environment.py              Gymnasium-style OpenDSS environment
│       ├── q_learning.py               Tabular Q-learning and two-phase training
│       └── utils.py                    DP value init, dispatch extraction, I/O
│
└── data/
    ├── aemo/                       ← Downloaded price data
    └── q_tables/                   ← Saved Q-tables (.npz)
```

## Quick Start

```bash
pip install opendssdirect.py numpy pandas requests

python download_prices.py        # Download AEMO NSW1 price data
python run_timeseries.py         # Baseline vs DP battery comparison
python run_feedback.py           # DP sensitivity analysis
python run_qlearning.py          # Q-learning sensitivity analysis
```

## Dependencies

| Package | Purpose |
|---------|---------|
| `opendssdirect.py` | OpenDSS power flow engine |
| `numpy` | Numerical computation |
| `pandas` | Data handling and resampling |
| `requests` | AEMO data download |
