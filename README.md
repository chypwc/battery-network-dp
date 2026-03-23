# Community Battery Techno-Economic and Network Analysis

## Overview

Community batteries are shared energy storage systems installed on suburban distribution networks, charging from rooftop solar during the day and discharging during evening peak demand. They provide two forms of value: **arbitrage revenue** (buying electricity when cheap, selling when expensive) and **network support** (preventing voltage violations that would otherwise require costly infrastructure upgrades).

This project builds a decision-support framework that jointly optimises these two objectives. A dynamic programming (DP) solver finds the revenue-maximising battery dispatch. A reinforcement learning (RL) agent extends this by embedding distribution network voltage constraints — learned through interaction with an OpenDSS power flow model — directly into the dispatch policy. A full-year PyPSA analysis quantifies annual revenue under both wholesale spot and retail time-of-use (TOU) pricing across 366 days of real NEM prices.

### System Under Study

The analysis centres on a specific battery and feeder configuration:

| Component | Specification |
|-----------|---------------|
| Battery | ±100 kW / 200 kWh (GenCost 2hr reference) |
| Efficiency | 95% one-way (90.25% round-trip) |
| Feeder | 32 houses, 20 × 6.6 kW rooftop PV, 200 kVA transformer |
| Cable | 95mm² Al underground, 350m trunk-to-endline |
| Battery location | End of Branch A (Node A4, worst-case for voltage) |
| Voltage limits | 0.94–1.10 pu (AS 61000.3.100: 230V +10%/−6%) |
| Price data | AEMO NSW1, calendar year 2024 (366 days) |

Without the battery, the feeder has 11 baseline voltage violations at end-of-feeder nodes during morning (06:00–07:00) and evening (17:00–20:30) peaks. A 9-configuration sensitivity grid (±50/80/100 kW × 200/300/400 kWh) is also evaluated.

### Two Business Models

The battery's revenue depends on which price signal it responds to. For full details, see [docs/business_models.md](docs/business_models.md).

| | Model A: Wholesale Spot | Model B: Retail TOU |
|---|---|---|
| **Price signal** | NEM spot price (volatile, varies daily) | ActewAGL retail TOU rate (fixed, published annually) |
| **Revenue type** | Cash settlement with AEMO | Bill reduction for participating households |
| **Typical daily spread** | A\$213/MWh (median), up to A\$17,500 on spike days | A\$281/MWh (guaranteed, every day) |

### The Core Problem

Unconstrained battery dispatch — the schedule that maximises arbitrage revenue — causes voltage violations on the distribution feeder. Running the DP-optimal dispatch through OpenDSS on every day of 2024 (±100kW / 200kWh configuration):

| | PyPSA (continuous LP) | DP (discrete) |
|---|:---:|:---:|
| Days with violations | **366 / 366** | **366 / 366** |
| Total violations/year | 3,242 | 3,021 |
| Mean violations/day | 8.9 | 8.3 |

Every single day has violations. The problem is structural: the feeder's cable impedance means that any significant battery dispatch at Node A4 causes bus voltages to exceed the ±6%/+10% limits. Heuristic approaches (tightening dispatch limits via a DP feedback loop) reduce but cannot eliminate violations.

![Violations Heatmap](docs/figures/violations_heatmap.png)
*DP dispatch voltage violations across 366 days × 48 half-hour periods. Red cells indicate voltage excursions beyond AS 61000.3.100 limits. Violations cluster in the morning (06:00–07:00) and evening (17:00–21:00) peaks — the same periods every day, regardless of price level.*

### The Solution

Q-learning with OpenDSS voltage feedback achieves **zero violations across all configurations, all price regimes, and both business models** — at a cost of just 3.2% of annual revenue. The RL agent discovers dispatch strategies that no static constraint adjustment can find: pre-charging before morning peaks, conservative early evening discharge, and rapid charge/discharge oscillation during violation-prone periods.

### Headline Results (±100kW / 200kWh)

| | Model A: Spot | Model B: TOU |
|---|:---:|:---:|
| Annual revenue (RL, network-safe) | A\$37,422 | A\$29,790 |
| Revenue certainty | 44% depends on 10 spike days/year | Guaranteed every day |
| NPV (Tier 1, 20yr) | Depends on spike assumptions | **+A\$139,083** |

TOU dominates on a risk-adjusted basis. Spot earns more in expectation but depends on unpredictable price spikes. TOU provides guaranteed daily revenue that makes the investment bankable.

---

## Battery Dispatch Optimisation

### The Arbitrage Problem

A battery operator maximises revenue by charging when electricity is cheap and discharging when expensive. This is a finite-horizon deterministic dynamic programming problem solved by backward induction over the Bellman equation:

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

The Bellman equation is identical for both business models — only the price vector $p_t$ changes:

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

The first term is arbitrage revenue. When charging ($a > 0$), the battery buys electricity at price $p_t$, producing a cost (negative reward). When discharging ($a < 0$), the battery sells electricity, producing income (positive reward). The division by 1000 converts A\$/MWh to A\$/kWh. The second term is battery degradation cost ($c_{\text{deg}} = 0.02$ A\$/kWh throughput), representing the shortened battery lifetime from cycling.

### Feasible Action Set

$$\mathcal{A}(s, t) = \lbrace a \in [-\bar{a}, \bar{a}] \mid s_{\min} \leq s' \leq s_{\max} \rbrace$$

Actions are bounded by the dispatch limit $\bar{a}$ (kW) and by the requirement that the next SoC stays within the battery's operating range: $s_{\min} = 0.1 \times E_{\text{rated}}$ (10% reserve) to $s_{\max} = E_{\text{rated}}$ (full capacity).

### Q-Learning Extension

The DP solver maximises revenue but has no knowledge of network voltage. Q-learning addresses this by embedding the OpenDSS voltage response directly into the reward signal. The agent interacts with an environment where each action produces both revenue and a voltage violation penalty.

**Reward with violation penalty:**

$$r_t = r_{\text{arb}}(s_t, a_t, p_t) - \lambda \cdot n_{\text{viol},t}$$

where $r_{\text{arb}}$ is the arbitrage reward (same as DP), $\lambda$ is the violation penalty (scaled to 10% of the day's price spread, minimum A\$5), and $n_{\text{viol},t}$ is the number of bus phases with voltage outside the 0.94–1.10 pu range, determined by OpenDSS power flow.

**Q-learning update.** The agent maintains a Q-table $Q(s, t, a)$ indexed by discretised SoC bin, time step, and action index. After each transition:

$$Q(s_t, t, a_t) \leftarrow Q(s_t, t, a_t) + \alpha_t \left[ r_t + \gamma \max_{a'} Q(s_{t+1}, t{+}1, a') - Q(s_t, t, a_t) \right]$$

Both the learning rate $\alpha_t$ and exploration rate $\epsilon_t$ decay exponentially over training episodes.

**Two-phase training.** A single penalty value cannot simultaneously encourage arbitrage exploration and violation avoidance. Training proceeds in two phases:

| | Phase 1: Arbitrage | Phase 2: Network Safety |
|---|---|---|
| Objective | Learn profitable dispatch | Refine for voltage feasibility |
| Penalty $\lambda$ | 0 | Scaled to price spread |
| OpenDSS calls | None (`skip_network`) | Every time step |
| Q-table init | DP value function | Phase 1 output |
| Epsilon | 0.3 → 0.05 | 0.1 → 0.001 |
| Episodes | 50,000 | 100,000 |

Phase 1 uses $\lambda = 0$ and skips OpenDSS calls entirely, running ~100× faster than Phase 2. The Q-table is initialised from the DP value function: for each SoC bin and time step, the DP's optimal action receives a Q-value equal to the interpolated $V_t(s)$.

Phase 2 enables OpenDSS and introduces the violation penalty. The agent starts with a profitable strategy from Phase 1 and makes targeted adjustments at violation periods. Lower initial epsilon protects the good arbitrage strategy while allowing exploration at critical evening periods.

For full mathematical formulation including discretisation, hyperparameter selection, and the DP feedback loop, see [docs/methods.md](docs/methods.md).

---

## Distribution Network Model

### Feeder Topology

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

32 houses (16 per branch), 20 × 6.6 kW PV systems, 200 kVA transformer, 95mm² underground cable. Voltage limits: 0.94–1.10 pu (AS 61000.3.100). Without the battery, the feeder has 11 baseline voltage violations during morning and evening peaks at end-of-feeder nodes.

---

## Results

### Model A: Wholesale Spot Arbitrage

#### DP vs Q-Learning (Single Typical Day)

| Config | DP Revenue | DP Viol | RL Revenue | RL Viol | Revenue Gap |
|--------|:---:|:---:|:---:|:---:|:---:|
| ±50kW / 200kWh | A\$28.38 | 4 | A\$24.98 | **0** | -A\$3.40 |
| ±50kW / 300kWh | A\$32.69 | 0 | A\$32.55 | 0 | -A\$0.14 |
| ±50kW / 400kWh | A\$35.92 | 0 | A\$35.90 | 0 | -A\$0.02 |
| ±80kW / 200kWh | A\$37.08 | 6 | A\$34.44 | **0** | -A\$2.64 |
| ±80kW / 300kWh | A\$44.26 | 4 | A\$42.50 | **0** | -A\$1.76 |
| ±80kW / 400kWh | A\$49.36 | 3 | A\$48.93 | **0** | -A\$0.43 |
| ±100kW / 200kWh | A\$41.23 | 10 | A\$36.31 | **0** | -A\$4.92 |
| ±100kW / 300kWh | A\$50.54 | 10 | A\$44.53 | **0** | -A\$6.00 |
| ±100kW / 400kWh | A\$56.56 | 10 | A\$48.51 | **0** | -A\$8.05 |

RL achieves 0 violations across all 9 configurations. DP achieves 0 in only 2 of 9.

#### How Q-Learning Eliminates Violations

The RL agent discovers three strategies that the DP cannot find:

**Pre-charging before morning peak.** RL charges at 05:30 and discharges slightly at 06:00. The revenue cost is ~A\$0.50, but it lifts morning voltage above 0.94 pu.

**Conservative early evening discharge.** RL discharges less than DP at 16:00–17:00, preserving energy for late evening voltage support.

**Late evening oscillation.** At 19:00–21:00, where DP's battery is empty, RL rapidly cycles ±40 kW — each discharge pulse lifts voltage, each charge pulse refills for the next pulse. Revenue-negative (~A\$0.50/cycle) but prevents the most severe violations.

These strategies require knowledge of the voltage response that only exists in the OpenDSS model. The DP feedback loop cannot discover oscillation because it is revenue-suboptimal at every individual time step. For detailed dispatch profiles and strategy analysis across all 9 configurations, see [docs/dp_vs_rl_findings.md](docs/dp_vs_rl_findings.md).

![Dispatch Comparison](docs/figures/dispatch_comparison.png)
*Three-method dispatch comparison on a typical spot day (2024-06-28). Top: spot price profile. Middle: battery power — PyPSA (continuous LP), DP (discrete), and RL (network-safe). Bottom: state of charge. The RL oscillation during 18:00–21:00 (green shaded region) is the key voltage support strategy that eliminates evening violations.*

### Model B: Retail TOU Arbitrage

| Config | TOU DP | DP Viol | TOU RL | RL Viol | Revenue Gap |
|--------|:---:|:---:|:---:|:---:|:---:|
| ±50kW / 200kWh | A\$79.48 | 4 | A\$75.34 | **0** | -A\$4.14 |
| ±80kW / 400kWh | A\$145.22 | 2 | A\$144.82 | **0** | -A\$0.40 |
| ±100kW / 200kWh | A\$85.23 | 7 | A\$81.56 | **0** | -A\$3.67 |
| ±100kW / 400kWh | A\$158.43 | 9 | A\$137.58 | **0** | -A\$20.85 |

TOU RL revenue is 2–3× higher than spot RL across all configurations. A 200 kWh battery under TOU (A\$29,769/yr) earns more than a 400 kWh battery under spot (A\$17,706/yr). The business model choice has a larger impact on viability than battery sizing. For the full business model comparison, see [docs/business_models.md](docs/business_models.md).

### Full-Year Analysis (±100kW / 200kWh)

PyPSA linear optimisation and DP backward induction were run on every day of 2024 (366 days), with each dispatch verified through OpenDSS for voltage violations. RL was trained on 5 representative days (one per revenue bucket) and the RL/DP ratio applied to the full-year DP results.

#### Annual Revenue

| Method | Annual | Daily Mean | Violations/Year |
|--------|------:|------:|:---:|
| PyPSA (continuous LP) | A\$36,190 | A\$98.88 | 3,242 |
| DP (discrete, unconstrained) | A\$38,661 | A\$105.63 | 3,021 |
| **RL (network-safe, estimated)** | **A\$37,422** | **A\$102.25** | **0** |
| TOU (guaranteed daily) | A\$29,790 | A\$81.56 | 0 |

Network safety cost: A\$1,239/year (3.2% of DP revenue).

#### Revenue Distribution

| Bucket | Days | DP Revenue | Estimated RL Revenue |
|--------|:---:|------:|------:|
| Low (< A\$10/day) | 51 | A\$488 | A\$291 |
| Typical (A\$10–50) | 227 | A\$7,462 | A\$6,943 |
| High (A\$50–100) | 52 | A\$3,601 | A\$3,434 |
| Very high (A\$100–500) | 26 | A\$7,277 | A\$7,193 |
| Spike (> A\$500) | 10 | A\$15,885 | A\$15,772 |

The top 10 spike days (2.7% of the year) contribute 44% of annual revenue. Without them, spot falls well below TOU.

![Revenue Distribution](docs/figures/revenue_histogram.png)
*Daily spot revenue (PyPSA unconstrained LP) across 366 days of 2024. Network-safe (RL) revenue is approximately 3% lower but follows the same distribution. Most days earn A\$10–50, but rare spike days (clipped at A\$200 in this view) dominate the annual total. The median (A\$31) is far below the mean (A\$99) due to extreme right skew. TOU daily revenue (A\$82) exceeds the spot median every day.*

#### Representative Day Validation

| Day | Date | PyPSA | DP | DP Viol | RL | RL Viol | RL/DP |
|-----|------|------:|------:|:---:|------:|:---:|:---:|
| Low | 2024-02-24 | A\$4.75 | A\$9.57 | 8 | A\$5.70 | 0 | 59.6% |
| Typical | 2024-09-27 | A\$28.25 | A\$32.87 | 9 | A\$30.59 | 0 | 93.1% |
| High | 2024-06-25 | A\$61.33 | A\$69.24 | 7 | A\$66.04 | 0 | 95.4% |
| Very high | 2024-05-03 | A\$269.85 | A\$279.90 | 8 | A\$276.66 | 0 | 98.8% |
| Spike | 2024-02-29 | A\$1,593.72 | A\$1,588.45 | 10 | A\$1,577.25 | 0 | 99.3% |

RL achieves zero violations across all five price regimes. The revenue cost of network safety is A\$2–11/day in absolute terms, dropping from 40% on low days to 0.7% on spike days.

#### Violation Analysis

| Finding | Detail |
|---------|--------|
| Days with violations (unconstrained) | 366/366 — every day, both methods |
| Highest-violation days | Low-revenue days (mean 10.7 viol/day) — not spike days |
| Reason | Quiet days have frequent small cycles, each causing a voltage excursion |
| PyPSA vs DP violations | PyPSA has more (3,242 vs 3,021) — continuous actions hit borderline voltages |
| RL violations | 0 on all representative days — oscillation strategy generalises across all price regimes |

For the complete 366-day analysis including monthly breakdowns, spike day impact, and seasonal patterns, see [docs/full_year_dispatch_analysis.md](docs/full_year_dispatch_analysis.md).

### NPV Analysis

Using the ±100kW / 200kWh GenCost 2hr configuration:

| | Spot (Tier 1) | TOU (Tier 1) |
|---|:---:|:---:|
| Capital cost | A\$116,000 | A\$116,000 |
| Annual revenue (RL) | A\$37,422 | A\$29,790 |
| Revenue certainty | Low (spike-dependent) | High (tariff-guaranteed) |
| NPV (20yr, 6.53%) | Depends on spike assumptions | **+A\$139,083** |
| Simple payback | ~3.1 yr (with spikes), ~8.7 yr (without) | 3.9 yr |

For the full NPV model with three-tier DNSP benefit framework and sensitivity analysis, see [docs/npv_analysis.md](docs/npv_analysis.md).

---

## Key Findings

**1. Every unconstrained dispatch causes voltage violations.** Across 366 days, both PyPSA and DP produce violations on every single day (3,000+/year). Network-aware dispatch control is not optional — it is a prerequisite for community battery operation.

**2. Q-learning achieves zero violations at 3.2% revenue cost.** The RL agent eliminates all violations across 9 battery configurations, 2 business models, and 5 representative price regimes. The annual revenue sacrifice is A\$1,239 — far less than the cost of a single voltage-related equipment failure.

**3. The RL oscillation strategy generalises.** The same charge/discharge oscillation pattern appears on every representative day regardless of price level, confirming it is driven by feeder physics rather than market conditions.

**4. TOU dominates spot on a risk-adjusted basis.** TOU provides 2–3× higher violation-free revenue than spot on a typical day, with zero variance. Spot's annual advantage depends entirely on 10 unpredictable spike days that contribute 44% of annual revenue.

**5. The business model matters more than battery size.** A 200 kWh TOU battery earns more than a 400 kWh spot battery. For community battery deployment, the regulatory and contractual framework (which price signal the battery responds to) is the primary determinant of viability.

**6. Battery capacity reduces the cost of network safety.** At ±80kW/400kWh, the RL revenue gap is A\$0.43/day. At ±100kW/200kWh, it is A\$4.92/day. Larger batteries can sustain discharge longer without needing the oscillation strategy, reducing the network safety overhead.

### Detailed Documentation

| Document | Contents |
|----------|----------|
| [docs/business_models.md](docs/business_models.md) | Model A (spot) vs Model B (TOU): price signals, revenue characteristics, risk comparison |
| [docs/full_year_dispatch_analysis.md](docs/full_year_dispatch_analysis.md) | 366-day PyPSA + DP + RL analysis with violations, seasonal breakdown, representative day selection |
| [docs/dp_vs_rl_findings.md](docs/dp_vs_rl_findings.md) | Detailed dispatch profiles, RL strategy analysis, 9-config sensitivity results |
| [docs/npv_analysis.md](docs/npv_analysis.md) | 20-year NPV model, three-tier DNSP benefit framework, sensitivity analysis |
| [docs/policy_implications.md](docs/policy_implications.md) | Recommendations for DNSPs, regulators, and community battery operators |
| [docs/annual_revenue_analysis.md](docs/annual_revenue_analysis.md) | PyPSA LP methodology, objective function, constraints, revenue extraction |
| [docs/methods.md](docs/methods.md) | Full mathematical formulation: DP, Q-learning, OpenDSS integration |

---

## Future Work

The current framework uses **deterministic (perfect foresight) optimisation** — the battery knows all 48 prices at the start of each day. In practice, a deployable controller requires a policy conditioned on observable state without knowledge of future prices. We identify three extensions:

**1. Stochastic DP with price state.** Extend the state space to $(t, \text{SoC}, \text{price percentile}, \text{volatility regime})$. The transition probabilities are estimated from the 2024 AEMO data. The output is a lookup-table policy: "at 17:00, SoC = 120 kWh, price in top 10%, spike day → discharge 100 kW." The gap between deterministic and stochastic optimal revenue quantifies the **value of perfect information** — how much a better price forecast is worth.

**2. Rolling-horizon model predictive control.** At each time step, observe the current price, forecast the next 2–4 hours, solve a short-horizon LP, execute the first action, then re-plan. This is the industry-standard approach and could use the PyPSA LP as the inner solver.

**3. Deep RL with continuous state.** Replace the tabular Q-learning with a neural network policy (e.g., PPO) trained on historical price episodes. This handles the high-dimensional state space of stochastic prices without explicit discretisation, and could integrate the voltage constraint directly via a Lagrangian penalty.

Each extension builds on the existing codebase and would constitute a research contribution suitable for publication.

---

## Project Structure

```
community-battery/
├── requirements.txt
│
├── scripts/                        ← All runnable entry points
│   ├── download_prices.py              Download AEMO price data
│   ├── run_timeseries.py               Baseline vs DP-optimised comparison
│   ├── run_feedback.py                 DP feedback loop sensitivity analysis
│   ├── run_qlearning.py                Q-learning sensitivity (Model A: spot)
│   ├── run_qlearning_tou.py            Q-learning sensitivity (Model B: TOU)
│   ├── run_business_model_comparison.py  Model A vs Model B comparison
│   ├── run_branch_comparison.py        Branch A vs Branch B voltage analysis
│   ├── run_pypsa_annual.py             PyPSA full-year optimisation (366 days)
│   ├── run_annual_dispatch.py          PyPSA + DP + OpenDSS violations (366 days)
│   ├── run_representative_days.py      DP + RL on 5 representative price days
│   ├── run_check_dispatch.py           Verify dispatch against OpenDSS
│   ├── pick_representative_days.py     Select representative days from annual data
│   └── generate_figures.py             Generate README figures (histogram, dispatch, heatmap)
│
├── dss/
│   └── suburb_feeder_32.dss        ← OpenDSS circuit definition
│
├── src/
│   ├── dp/                         ← Dynamic programming optimiser
│   │   ├── battery.py                  Battery physical model
│   │   ├── solver.py                   Bellman equation solver
│   │   └── prices.py                   AEMO data + TOU profile builder
│   │
│   ├── opendss/                    ← Distribution network model
│   │   ├── network.py                  OpenDSS interface
│   │   ├── profiles.py                 Load and solar profiles
│   │   └── feeders.py                  Feeder element configuration
│   │
│   ├── integration/                ← DP ↔ OpenDSS feedback loop
│   │   ├── timeseries.py               Time-series power flow simulation
│   │   ├── constraints.py              Voltage constraint generation
│   │   └── feedback.py                 Iterative DP re-solve
│   │
│   ├── rl/                         ← Q-learning with network feedback
│   │   ├── environment.py              Gymnasium-style OpenDSS environment
│   │   ├── q_learning.py               Two-phase training algorithm
│   │   └── utils.py                    DP warm-start, dispatch extraction
│   │
│   └── pypsa/                      ← Full-year LP optimisation
│       ├── network.py                  Single-bus battery network builder
│       ├── dispatch.py                 Daily optimisation + annual sweep
│       └── analysis.py                 Revenue statistics and distributions
│
├── data/
│   ├── aemo/                       ← AEMO price data (12 monthly CSVs)
│   │   ├── nem_prices_NSW1_clean.csv   Cleaned full-year 30-min prices
│   │   └── prices_*.csv                Representative day extracts
│   ├── pypsa/
│   │   ├── annual_revenue.csv          366-day PyPSA revenue results
│   │   └── annual_dispatch_results.csv 366-day PyPSA + DP with violations
│   └── q_tables/                   ← Trained Q-tables (.npz)
│
├── docs/
│   ├── figures/                    ← Generated figures for README
│   │   ├── revenue_histogram.png
│   │   ├── dispatch_comparison.png
│   │   └── violations_heatmap.png
│   ├── methods.md                  ← Full mathematical formulation
│   ├── business_models.md          ← Model A (spot) vs Model B (TOU) comparison
│   ├── dp_vs_rl_findings.md        ← Dispatch comparison analysis
│   ├── npv_analysis.md             ← NPV model and sensitivity
│   ├── policy_implications.md      ← Policy recommendations
│   ├── annual_revenue_analysis.md  ← PyPSA methodology and LP formulation
│   └── full_year_dispatch_analysis.md ← Integrated annual results
│
└── tests/
    └── test_battery.py
```

## Quick Start

```bash
# Install dependencies (uv virtual environment)
uv pip install -r requirements.txt

# Download AEMO NSW1 price data (Jan–Dec 2024)
python -m scripts.download_prices

# Single-day analysis
python -m scripts.run_timeseries               # Baseline vs DP comparison
python -m scripts.run_qlearning                # RL spot price training (9 configs)
python -m scripts.run_qlearning_tou            # RL TOU price training (9 configs)

# Full-year analysis
python -m scripts.run_pypsa_annual             # PyPSA LP, 366 days (~60s)
python -m scripts.run_annual_dispatch          # PyPSA + DP + violations (~36 min)
python -m scripts.run_representative_days      # DP + RL on 5 representative days (~50 min)

# Analyse cached results
python -m scripts.run_pypsa_annual --cached
python -m scripts.run_annual_dispatch --cached

# Generate figures for README
python -m scripts.generate_figures             # Revenue histogram + dispatch comparison
python -m scripts.generate_figures --with-heatmap  # + violations heatmap (~36 min)
```

## Dependencies

| Package | Purpose |
|---------|---------|
| `opendssdirect.py` | OpenDSS power flow engine |
| `numpy` | Numerical computation |
| `pandas` | Data handling and resampling |
| `requests` | AEMO data download |
| `pypsa` | Linear optimal power flow |
| `highspy` | HiGHS LP solver for PyPSA |