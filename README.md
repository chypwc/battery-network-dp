# Community Battery Techno-Economic and Network Analysis

## Overview

Community batteries are shared energy storage systems installed on suburban distribution networks, charging from rooftop solar during the day and discharging during evening peak demand. They provide two forms of value: **arbitrage revenue** (buying electricity when cheap, selling when expensive) and **network support** (preventing voltage violations that would otherwise require costly infrastructure upgrades).

This project builds a decision-support tool that jointly optimises these two objectives using two complementary methods. A dynamic programming (DP) solver finds the revenue-maximising battery dispatch schedule. A Q-learning agent extends this by embedding network voltage constraints directly into the reward signal, discovering dispatch strategies that are both profitable and network-safe.

The tool evaluates two alternative business models that determine the price signal the battery responds to:

| | Model A: Wholesale Spot | Model B: Retail TOU |
|---|---|---|
| **Owner** | Market participant | Community group or third-party |
| **Price signal** | NEM spot price (volatile, changes every 5 min) | ActewAGL retail TOU rate (fixed, published annually) |
| **Revenue type** | Cash settlement with AEMO | Bill reduction for participating households |
| **Trades with** | AEMO directly | No trading — offsets retail bills |

**Model A** represents a battery operator registered as a NEM market participant who buys and sells electricity at the wholesale spot price. Revenue depends on the daily price spread, which varies significantly across days and seasons. This model also incurs a separate network tariff payable to the distribution network operator (Evoenergy).

**Model B** represents a community-owned or third-party-operated battery that sits behind participating households' meters. It charges when the retail rate is lowest (solar soak period, 11am–3pm) and discharges when the rate is highest (peak periods, 7am–9am and 5pm–9pm), reducing each household's electricity bill. The retail rate already bundles wholesale energy, network charges, and retail margin — there is no separate network tariff. The price signal is the ActewAGL Home Daytime Economy tariff, which aligns with Evoenergy's proposed residential TOU network tariff (Code 017) for the 2024–29 regulatory period.

Both models are verified against an OpenDSS power flow model of a representative 32-house Australian suburban feeder with high rooftop solar penetration. The tool produces concrete sizing and dispatch recommendations: what battery capacity is needed, what dispatch limit should the network operator impose, and what is the revenue cost of network safety — under each business model.

## Battery Dispatch Optimisation

### The Arbitrage Problem

A battery operator maximises revenue by charging when electricity is cheap and discharging when it is expensive. The challenge is deciding, at each half-hour, how much to charge or discharge given the current state of charge, the current price, and the knowledge that future prices may be higher or lower.

The price signal depends on the business model:

**Model A (Wholesale Spot).** NEM spot prices vary throughout the day — low during midday solar surplus (sometimes negative), high during evening peak demand. The price sequence is volatile and differs every day. A typical ACT day shows prices ranging from -A\$14/MWh at midday to A\$230/MWh at the morning peak, a spread of approximately A\$245/MWh. The optimal dispatch changes daily because the price profile is different each day.

**Model B (Retail TOU).** The ActewAGL Home Daytime Economy tariff defines three fixed price tiers (GST exclusive, from 1 July 2025):

| Period | Time (AEST) | Rate | A\$/MWh |
|--------|-------------|------|:---:|
| Solar soak | 11am–3pm | 16.00 c/kWh | 160 |
| Shoulder | 9pm–7am, 9am–11am, 3pm–5pm | 29.00 c/kWh | 290 |
| Peak | 7am–9am, 5pm–9pm | 44.07 c/kWh | 441 |

The spread between solar soak and peak is A\$281/MWh — wider than the typical spot day and guaranteed every day. The optimal dispatch is the same every day because the tariff structure is fixed: charge during solar soak, discharge during morning and evening peaks.

Under both models, this is a finite-horizon deterministic dynamic programming problem. The price sequence is known in advance (day-ahead spot prices for Model A; published tariff schedule for Model B), the battery physics are deterministic, and the planning horizon is one day (48 half-hour periods).

### Bellman Equation

The optimal dispatch is found by backward induction over the value function:

$$V_t(s) = \max_{a \in \mathcal{A}(s,t)} \left[ r(s, a, p_t) + V_{t+1}(s') \right], \quad t = T{-}1, \ldots, 0$$

with terminal condition $V_T(s) = 0$ for all $s$.

| Symbol | Code | Meaning |
|--------|------|---------|
| $t$ | `t` | Time step (0 = 00:00, ..., 47 = 23:30) |
| $s$ | `soc` | State of charge (kWh) |
| $a$ | `action_kw` | Charge (+kW) or discharge (−kW) |
| $p_t$ | `prices[t]` | Price at time $t$ (A\$/MWh) |
| $s'$ | `s_next` | SoC after action $a$ |
| $V_t(s)$ | `V[t][i]` | Max future revenue from state $s$ at time $t$ |

The Bellman equation is identical for both business models — only the price vector $p_t$ changes. Under Model A, $p_t$ is the NEM spot price downloaded from AEMO. Under Model B, $p_t$ is the ActewAGL retail TOU rate constructed from the published tariff schedule:

```python
# Model A: volatile, different every day
prices_spot = load_day_prices('data/aemo/prices_typical_2024-06-28.csv')

# Model B: fixed, same every day
prices_tou = build_tou_profile()  # [160, 160, ..., 290, ..., 441, ...]
```

This separation of optimisation algorithm from price signal is a key design feature. The same DP solver, Q-learning agent, and OpenDSS network model are reused across business models — only the 48-element price vector changes.

### State Transition

The battery's state of charge evolves differently for charging and discharging due to conversion losses:

$$s' = \begin{cases} s + \eta_c \cdot a \cdot \Delta t & \text{if } a \geq 0 \text{ (charging)} \\\\ s + \dfrac{a}{\eta_d} \cdot \Delta t & \text{if } a < 0 \text{ (discharging)} \end{cases}$$

When charging, the grid delivers $a \cdot \Delta t$ kWh but only $\eta_c \cdot a \cdot \Delta t$ reaches the battery (the rest is lost as heat). When discharging, the battery must release $|a| \cdot \Delta t / \eta_d$ kWh internally to deliver $|a| \cdot \Delta t$ to the grid. Parameters: $\eta_c = \eta_d = 0.95$, $\Delta t = 0.5$ h.

### Reward Function

$$r(s, a, p_t) = -\frac{p_t}{1000} \cdot a \cdot \Delta t - c_{\text{deg}} \cdot |a| \cdot \Delta t$$

The first term is arbitrage revenue. When charging ($a > 0$), the battery buys electricity at price $p_t$, producing a cost (negative reward). When discharging ($a < 0$), the battery sells electricity, producing income (positive reward). The second term is battery degradation cost ($c_{\text{deg}} = 0.02$ A\$/kWh throughput), representing the shortened battery lifetime from cycling.

Under Model A, $p_t$ is the NEM spot price and the revenue represents direct cash settlement with AEMO. Under Model B, $p_t$ is the retail TOU rate and the "revenue" represents the reduction in participating households' electricity bills — the battery avoids buying expensive peak electricity by discharging stored solar soak energy.

### Feasible Action Set

$$\mathcal{A}(s, t) = \lbrace a \in [-\bar{a}, \bar{a}] \mid s_{\min} \leq s' \leq s_{\max} \rbrace$$

Actions are bounded by the dispatch limit $\bar{a}$ (kW) and by the requirement that the next SoC stays within the battery's operating range: $s_{\min} = 0.1 \times E_{\text{rated}}$ (reserve) to $s_{\max} = E_{\text{rated}}$ (full capacity).

### Discretisation

The SoC and action spaces are discretised into $n_s$ and $n_a$ evenly spaced grid points. The value function at off-grid states is obtained by linear interpolation of $V_{t+1}$. Total computation per solve: $T \times n_s \times n_a$ evaluations (typically 48 x 81 x 81 = 315,000, runs in under a second).

### Price Data

**Model A:** Real AEMO NSW1 spot prices (the ACT falls within the NSW1 NEM region). Data is downloaded from AEMO's public aggregated price and demand portal at 5-minute dispatch resolution, then resampled to 30-minute settlement periods by averaging six consecutive dispatch prices.

**Model B:** ActewAGL Home Daytime Economy tariff rates from the ACT Standard plan electricity prices schedule (from 1 July 2025). The tariff aligns with Evoenergy's proposed residential TOU network tariff (Code 017) under the Revised Tariff Structure Statement for the 2024–29 regulatory period.

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

The two-phase approach applies to both business models. Under Model A, Phase 1 learns spot price arbitrage patterns. Under Model B, Phase 1 learns TOU arbitrage patterns (charge during solar soak, discharge during peaks). In both cases, Phase 2 refines the dispatch for network feasibility using the same OpenDSS environment — the network physics are identical regardless of which price signal the battery responds to.

**Network-constrained feasible set (feedback loop).** When the DP feedback loop is used instead of Q-learning, the feasible set is restricted by heuristic constraints:

$$\mathcal{A}_c(s, t) = \lbrace a \in \mathcal{A}(s,t) \mid a \leq a_{\min}^{\text{dis}}(t), a \leq a_{\max}^{\text{chg}}(t), s' \geq s_{\min}^{\text{net}}(t{+}1) \rbrace$$

| Constraint | Source | Purpose |
|------------|--------|---------|
| $a_{\min}^{\text{dis}}(t) < 0$ | Undervoltage at period $t$ | Force minimum discharge power |
| $a_{\max}^{\text{chg}}(t)$ | Overvoltage at period $t$ | Limit charging power |
| $s_{\min}^{\text{net}}(t{+}1)$ | Future undervoltage periods | Preserve energy for later discharge |

The minimum discharge power at each violation period is determined by binary search in OpenDSS.

For full mathematical details of the DP solver, feedback loop, Q-learning update rule, two-phase training, and hyperparameter configurations, see [docs/methods.md](docs/methods.md).

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

### Model A: Wholesale Spot Arbitrage

#### DP Sensitivity: Dispatch Limit x Battery Capacity

| Limit | Capacity | Revenue/day | Violations | Eliminated | Losses (kWh) |
|-------|----------|-------------|-----------|------------|--------------|
| base  | ---      | ---         | 11        | ---        | 57.2         |
| ±30kW | 400kWh   | A\$17       | 8         | 3/11       | 59.4         |
| ±50kW | 200kWh   | A\$28       | 3         | 8/11       | 62.2         |
| ±50kW | 300kWh   | A\$32       | 1         | 10/11      | 60.9         |
| **±50kW** | **400kWh** | **A\$36** | **0**  | **11/11**  | **60.7**     |
| ±80kW | 400kWh   | A\$48       | 3         | 8/11       | 79.1         |
| ±100kW| 400kWh   | A\$39       | 3         | 8/11       | 86.4         |

#### DP vs Q-Learning: Head-to-Head

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

#### Network Impact

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

### Key Findings (Model A)

**1. Q-learning achieves 0 violations across all configurations.** DP achieves 0 violations in only 2 of 9 configurations (±50kW with 300+ kWh). Q-learning eliminates all violations by learning the voltage response to battery actions through direct interaction with the OpenDSS network model.

**2. DP provides the revenue upper bound; RL provides the feasibility boundary.** DP answers "what is the maximum possible revenue?" while RL answers "what is the maximum revenue achievable without violating network constraints?" Together they bracket the design space.

**3. The revenue cost of network safety is small for well-sized batteries.** At ±80kW/400kWh, the gap is only A\$0.43/day (A\$157/year). At ±50kW/200kWh, it is A\$3.40/day (A\$1,241/year). The cost increases with dispatch limit and decreases with battery capacity.

**4. ±30kW is below the voltage correction threshold.** The cable impedance requires approximately 40–50 kW of injection to produce the 0.012 pu voltage rise needed to cross the 0.94 pu limit. Below this, no algorithm can fix violations.

**5. ±80–100kW causes overvoltage under DP dispatch.** The DP charges and discharges at full power, driving V_max to 1.096–1.102 pu. Q-learning moderates the dispatch to stay within both voltage limits simultaneously.

**6. Battery energy capacity (kWh) is the binding constraint for DP.** At ±50kW, the DP needs 400 kWh for 0 violations. Q-learning achieves 0 violations at 200 kWh — a 50% reduction in minimum battery size.

**7. RL reduces network losses by 4–14%.** The oscillating strategy uses lower sustained current than DP's aggressive dispatch. The DNSP benefits from both fewer violations and lower loss costs.

For the policy implications, see [docs/policy implications.md](docs/policy%20implications.md).

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

### NPV Analysis

A 20-year discounted cash flow model evaluates the investment case for the 200 kWh and 400 kWh batteries at ±80kW with RL dispatch. Cost data is sourced from CSIRO GenCost 2025, AER RORI 2025 (6.53% discount rate), and Evoenergy's 2024 Tariff Structure Statement. Costs (capital, O&M, module replacement) are identical across business models — only the revenue differs.

**Model A (Spot) — ±80kW / 200kWh:**

| Tier | NPV | Includes |
|------|:---:|---------|
| **Tier 1: Arbitrage only** | **-A\$29,969** | Operator revenue − costs (most realistic) |
| Tier 2: + augmentation | -A\$8,874 | + deferred transformer, requires DNSP contract |
| Tier 3: + aug + LRMC | +A\$3,767 | + export saving, theoretical maximum |

**Model B (TOU) — ±80kW / 200kWh:**

| Tier | NPV | Includes |
|------|:---:|---------|
| **Tier 1: Arbitrage only** | **+A\$135,533** | Operator revenue − costs (most realistic) |
| Tier 2: + augmentation | +A\$156,627 | Bonus if DNSP contract exists |
| Tier 3: + aug + LRMC | +A\$169,269 | Theoretical maximum |

**Tier 1** assumes the operator receives only arbitrage revenue (NEM spot settlement or retail TOU bill savings) with no payments from the distribution network operator. **Tier 2** adds a DNSP network support payment for deferring a specific A\$45,000 transformer upgrade by 10 years — a concrete, project-level benefit that could be contracted under the NER's non-network alternatives framework. **Tier 3** further adds the system-wide export LRMC saving (A\$1,150/yr), which reflects Evoenergy's average incremental cost of managing solar exports across the network — a more abstract value that is unlikely to appear in a practical contract.

For full model details, equations, and sensitivity analysis, see [docs/npv_analysis.md](docs/npv_analysis.md).

### Model B: Retail TOU Arbitrage

#### DP vs Q-Learning: Head-to-Head (TOU)

The same DP solver and Q-learning agent are applied with ActewAGL Home Daytime Economy retail TOU rates (GST exclusive, from 1 July 2025) as the price signal. The network model, battery physics, and violation thresholds are identical to Model A — only the 48-element price vector changes.

| Config | TOU DP Revenue | DP Violations | TOU RL Revenue | RL Violations | Revenue Gap |
|--------|:---:|:---:|:---:|:---:|:---:|
| **Baseline (no battery)** | **—** | **11** | **—** | **—** | **—** |
| ±50kW / 200kWh | A\$79.48 | 4 | A\$75.34 | **0** | -A\$4.14 |
| ±50kW / 300kWh | A\$97.76 | 2 | A\$96.84 | **0** | -A\$0.92 |
| ±50kW / 400kWh | A\$109.27 | 2 | A\$108.47 | **0** | -A\$0.80 |
| ±80kW / 200kWh | A\$83.51 | 5 | A\$80.57 | **0** | -A\$2.94 |
| ±80kW / 300kWh | A\$119.81 | 3 | A\$117.54 | **0** | -A\$2.27 |
| ±80kW / 400kWh | A\$145.22 | 2 | A\$144.82 | **0** | -A\$0.40 |
| ±100kW / 200kWh | A\$85.23 | 7 | A\$81.56 | **0** | -A\$3.67 |
| ±100kW / 300kWh | A\$122.74 | 10 | A\$119.14 | **0** | -A\$3.60 |
| ±100kW / 400kWh | A\$158.43 | 9 | A\$137.58 | **0** | -A\$20.85 |

Q-learning again achieves **0 violations across all 9 configurations** under TOU prices, just as it does under spot prices. The TOU DP has violations in all 9 configurations (the TOU dispatch pattern differs from spot and creates violations at different times).

#### Annual Revenue: Model A vs Model B (Violation-Free RL Only)

| Config | Spot RL (A\$/yr) | TOU RL (A\$/yr) | TOU Advantage |
|--------|:---:|:---:|:---:|
| ±50kW / 200kWh | A\$9,662 | A\$27,499 | +A\$17,838 (2.8×) |
| ±50kW / 300kWh | A\$11,934 | A\$35,348 | +A\$23,413 (3.0×) |
| ±50kW / 400kWh | A\$13,103 | A\$39,592 | +A\$26,488 (3.0×) |
| ±80kW / 200kWh | A\$12,542 | A\$29,408 | +A\$16,866 (2.3×) |
| ±80kW / 300kWh | A\$15,513 | A\$42,904 | +A\$27,391 (2.8×) |
| ±80kW / 400kWh | A\$17,860 | A\$52,861 | +A\$35,001 (3.0×) |
| ±100kW / 200kWh | A\$13,254 | A\$29,769 | +A\$16,515 (2.2×) |
| ±100kW / 300kWh | A\$16,254 | A\$43,486 | +A\$27,232 (2.7×) |
| ±100kW / 400kWh | A\$17,706 | A\$50,217 | +A\$32,511 (2.8×) |

The retail TOU business model produces **2–3× higher violation-free revenue** than wholesale spot arbitrage across all configurations. This is because the TOU price spread (A\$281/MWh between solar soak and peak) is wider than the typical spot day spread (A\$245/MWh), the peak rate applies for 12 half-hour periods per day (versus approximately 5 high-price periods for spot), and the TOU revenue is guaranteed every day while spot revenue varies.

### Key Findings (Model B)

**1. Q-learning achieves 0 violations under TOU prices.** The same two-phase training approach works: Phase 1 learns TOU arbitrage (charge during solar soak, discharge during peaks), Phase 2 adds OpenDSS violation penalties. The RL discovers similar voltage support strategies — morning pre-charging, conservative early evening discharge, and late evening oscillation — adapted to the TOU dispatch pattern.

**2. The business model choice has a larger impact on viability than battery sizing.** The TOU advantage (2–3×) exceeds the effect of doubling battery capacity within either model. A 200 kWh battery under TOU (A\$29,408/yr) earns more than a 400 kWh battery under spot (A\$17,860/yr).

**3. TOU revenue transforms the NPV.** At ±80kW/200kWh, TOU RL earns A\$29,408/year versus A\$12,542/year for spot RL. The 200 kWh battery's simple payback drops from 9.2 years (spot) to approximately 3.9 years (TOU). The TOU business model makes the community battery clearly viable without requiring augmentation deferral credits.

**4. TOU DP has violations in all 9 configurations.** Unlike spot DP (which achieves 0 violations at ±50kW/300kWh and ±50kW/400kWh), TOU DP causes violations in every configuration because its dispatch pattern is different: it idles during the morning (shoulder rate, no incentive to discharge) while baseline violations occur at 06:00–06:30. Q-learning is essential for network-safe TOU operation.

**5. The revenue cost of network safety follows the same pattern.** Well-sized batteries (±80kW/400kWh) lose only A\$0.40/day for network safety. The largest gap is ±100kW/400kWh at A\$20.85/day, where RL must significantly moderate the ±100kW dispatch to avoid overvoltage during midday charging.


## Project Structure

```
community-battery/
├── download_prices.py              ← Download AEMO price data
├── run_timeseries.py               ← Baseline vs DP-optimised comparison
├── run_feedback.py                 ← DP sensitivity analysis
├── run_qlearning.py                ← Q-learning sensitivity (Model A: spot prices)
├── run_qlearning_tou.py            ← Q-learning sensitivity (Model B: TOU prices)
├── run_business_model_comparison.py← Model A vs Model B revenue and violations
├── run_branch_comparison.py        ← Branch A vs Branch B voltage analysis
│
├── dss/
│   └── suburb_feeder_32.dss        ← OpenDSS circuit definition
│
├── src/
│   ├── dp/                         ← Layer 2: DP optimiser
│   │   ├── battery.py                  Battery physical model
│   │   ├── solver.py                   Bellman equation solver
│   │   └── prices.py                   AEMO data loader + TOU profile builder
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
├── data/
│   ├── aemo/                       ← Downloaded price data
│   └── q_tables/                   ← Saved Q-tables (.npz, spot and TOU)
│
└── docs/
    ├── methods.md                  ← Full mathematical formulation
    ├── dp_vs_rl_findings.md        ← Detailed dispatch comparison
    ├── npv_analysis.md             ← NPV model and sensitivity
    └── policy_implications.md      ← Policy recommendations
```

## Quick Start

```bash
pip install opendssdirect.py numpy pandas requests

python download_prices.py                  # Download AEMO NSW1 price data
python run_timeseries.py                   # Baseline vs DP battery comparison
python run_feedback.py                     # DP sensitivity analysis
python run_qlearning.py                    # Q-learning: Model A (spot prices)
python run_qlearning_tou.py                # Q-learning: Model B (TOU prices)
python run_business_model_comparison.py    # Model A vs Model B comparison
```

## Dependencies

| Package | Purpose |
|---------|---------|
| `opendssdirect.py` | OpenDSS power flow engine |
| `numpy` | Numerical computation |
| `pandas` | Data handling and resampling |
| `requests` | AEMO data download |
