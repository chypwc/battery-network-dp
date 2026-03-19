# Community Battery Dispatch Optimisation: DP vs Q-Learning

## Executive Summary

This report compares two dispatch optimisation methods for community batteries on Australian suburban distribution networks: deterministic dynamic programming (DP) and tabular Q-learning with two-phase training. Both methods are evaluated across a grid of battery dispatch limits (±50, ±80, ±100 kW) and energy capacities (200, 300, 400 kWh) on a 32-house feeder with 132 kW of rooftop solar.

The key finding: **Q-learning achieves zero voltage violations across all tested configurations, while DP leaves 3–10 violations in 8 of 9 configurations.** Q-learning discovers novel dispatch strategies — notably rapid charge/discharge cycling during evening peak — that the revenue-maximising DP cannot find. The revenue cost of network safety ranges from less than 1% to 14% depending on configuration.

## Problem Setup

### Baseline Network

The study feeder has 11 voltage violations without any battery — 3 in the morning (06:00–07:00) and 8 in the evening (17:00–20:30). Violations occur at the end-of-feeder nodes where voltage drop is greatest.

| Parameter | Value |
|-----------|-------|
| Houses | 32 (16 per branch) |
| Peak load | 96 kW |
| Solar capacity | 132 kW (20 × 6.6 kW) |
| Voltage limits | 0.94–1.10 pu |
| Baseline violations | 11 of 48 periods |

### Methods

**Dynamic Programming** solves the Bellman equation exactly for revenue-maximising dispatch. It has no knowledge of network voltage — violations are checked afterward.

**Q-Learning (two-phase)** uses a tabular Q-learning agent that interacts with an OpenDSS-based environment. Training proceeds in two phases:

- Phase 1 (penalty=0, skip_network=True): Learn profitable arbitrage strategy, initialised from DP value function. No OpenDSS calls — runs ~100× faster than Phase 2.
- Phase 2 (penalty=5–10, skip_network=False): Refine dispatch to avoid voltage violations. Each time step calls OpenDSS for power flow and violation detection.

## Results

### Head-to-Head Comparison

| Config | DP Revenue | DP Violations | RL Revenue | RL Violations | Revenue Gap |
|--------|-----------|--------------|-----------|--------------|-------------|
| **Baseline (no battery)** | **—** | **11** | **—** | **—** | **—** |
| ±50kW / 200kWh | A\$28.38 | 4 | A\$24.98 | **0** | −A\$3.40 |
| ±50kW / 300kWh | A\$32.69 | 0 | A\$32.55 | 0 | −A\$0.14 |
| ±50kW / 400kWh | A\$35.92 | 0 | A\$35.90 | 0 | −A\$0.02 |
| ±80kW / 200kWh | A\$37.08 | 6 | A\$34.44 | **0** | −A\$2.64 |
| ±80kW / 300kWh | A\$44.26 | 4 | A\$42.50 | **0** | −A\$1.76 |
| ±80kW / 400kWh | A\$49.36 | 3 | A\$48.93 | **0** | −A\$0.43 |
| ±100kW / 200kWh | A\$41.23 | 10 | A\$36.31 | **0** | −A\$4.92 |
| ±100kW / 300kWh | A\$50.54 | 10 | A\$44.53 | **0** | −A\$6.00 |
| ±100kW / 400kWh | A\$56.56 | 10 | A\$48.51 | **0** | −A\$8.05 |

### Network Impact

| Config | DP Losses (kWh) | RL Losses (kWh) | Loss Reduction | DP Peak Tx | RL Peak Tx |
|--------|----------------|----------------|----------------|-----------|-----------|
| **Baseline (no battery)** | **57.2** | **57.2** | **—** | **49.7%** | **49.7%** |
| ±50kW / 200kWh | 62.2 | 55.1 | −7.1 (−11%) | 52.1% | 52.2% |
| ±80kW / 200kWh | 70.6 | 64.1 | −6.5 (−9%) | 64.8% | 65.0% |
| ±80kW / 300kWh | 76.7 | 72.1 | −4.6 (−6%) | 65.0% | 65.0% |
| ±80kW / 400kWh | 81.4 | 78.0 | −3.4 (−4%) | 65.0% | 65.0% |
| ±100kW / 200kWh | 78.3 | 68.6 | −9.7 (−12%) | 73.5% | 67.0% |
| ±100kW / 300kWh | 85.8 | 73.6 | −12.2 (−14%) | 73.5% | 67.0% |
| ±100kW / 400kWh | 95.4 | 81.8 | −13.6 (−14%) | 73.5% | 67.0% |

Losses represent electrical energy dissipated as heat in cables and the transformer due to current flow (governed by $I^2 R$). Higher battery dispatch power drives higher current through the feeder, increasing losses quadratically. RL consistently reduces losses compared to DP because the oscillating evening strategy uses lower sustained current than DP's aggressive continuous discharge. At ±100kW/400kWh, RL saves 13.6 kWh/day in losses — energy that would otherwise be wasted as heat in the cables.

## Q-Learning Dispatch Strategies

The Q-learning agent independently discovered three strategies for eliminating voltage violations. These strategies appear consistently across all configurations and dispatch limits.

### Strategy 1: Pre-Charging Before Morning Peak

RL charges at t=11 (05:30, A\$60/MWh) and discharges slightly at t=12 (06:00, A\$101/MWh). The DP ignores 06:00 because it optimises only for revenue — at A\$101/MWh, the price isn't high enough to justify discharging. But RL learned from OpenDSS that even a 10 kW discharge at 06:00 lifts the morning voltage above 0.94 pu, eliminating one violation at minimal revenue cost (~A\$0.50).

| Config | DP at t=11 | RL at t=11 | DP at t=12 | RL at t=12 |
|--------|-----------|-----------|-----------|-----------|
| ±50kW / 200kWh | idle | +5 kW | idle | −10 kW |
| ±80kW / 200kWh | +25 kW | +70 kW | idle | −10 kW |
| ±100kW / 200kWh | +88 kW | +100 kW | idle | −10 kW |
| ±100kW / 300kWh | +50 kW | +94 kW | idle | −12 kW |

### Strategy 2: Conservative Early Evening Discharge

At t=32–34 (16:00–17:00), RL discharges less aggressively than DP to preserve energy for the critical late evening periods.

| Config | DP at t=32 | RL at t=32 | Energy Saved |
|--------|-----------|-----------|-------------|
| ±50kW / 200kWh | −40 kW | −20 kW | 10 kWh |
| ±80kW / 200kWh | idle | idle | — |
| ±80kW / 400kWh | −80 kW | −45 kW | 18 kWh |
| ±100kW / 400kWh | −88 kW | −56 kW | 16 kWh |

DP maximises immediate revenue by discharging at the first high evening prices. RL sacrifices early evening revenue to ensure the battery retains enough energy for t=38–42 (19:00–21:00) when violations are most severe.

The most striking example is ±100kW/200kWh at t=34 (A\$137/MWh): DP discharges −25 kW, but RL **charges** +60 kW — paying A\$3.42 to store energy that enables four more half-hours of voltage support.

### Strategy 3: Late Evening Oscillation

This is the signature Q-learning strategy. At t=38–42 (19:00–21:00), where the DP's battery is empty and cannot provide voltage support, RL rapidly cycles between charging and discharging:

**±50kW / 200kWh (4 oscillation cycles):**
```
t=38  +40 kW (charge — refill battery)
t=39  −45 kW (discharge — support voltage)
t=40  +45 kW (charge — refill battery)
t=41  −40 kW (discharge — support voltage)
t=42  −15 kW (final small discharge)
```

**±100kW / 200kWh (2 oscillation cycles):**
```
t=38  +38 kW (charge)
t=39  −38 kW (discharge)
t=40  +38 kW (charge)
t=41  −38 kW (discharge)
t=42   −6 kW (final discharge)
```

Each discharge period injects power into the feeder, lifting voltage above 0.94 pu. Each charge period refills just enough energy for the next discharge. The strategy is revenue-negative (charging at A\$115/MWh and discharging at A\$105/MWh loses ~A\$0.50 per cycle) but prevents voltage violations.

The oscillation pattern adapts to battery capacity:

| Capacity | Oscillation Behaviour | Reason |
|----------|----------------------|--------|
| 200 kWh | 3–4 full cycles | Battery too small for sustained discharge; must refill repeatedly |
| 300 kWh | 1–2 cycles | Enough energy for most of evening; only last 2 periods need cycling |
| 400 kWh | Sustained discharge with minor adjustments | Enough energy for full evening; just redistributes power across periods |

At 400 kWh, the RL strategy converges toward the DP strategy because the battery has enough energy that sustained discharge is both profitable and network-safe. The oscillation only appears when the battery capacity is the binding constraint.

### Why DP Cannot Find These Strategies

The DP solver maximises revenue with no knowledge of network physics. It cannot discover that:

1. A small discharge at 06:00 (low price) prevents a morning violation
2. Holding back energy at 16:00 (high price) enables evening voltage support
3. Revenue-negative oscillation at 19:00–21:00 prevents the most severe violations

These strategies require knowledge of the **voltage response** to battery actions, which only exists in the OpenDSS power flow model. The DP's feedback loop attempts to add this knowledge through heuristic constraints, but it can only force discharge at violation periods — it cannot discover the oscillating strategy because it's revenue-suboptimal at every individual time step.

Q-learning discovers these strategies because each training step receives immediate feedback from OpenDSS: "this action caused 6 phase violations" or "this action caused 0 violations." Over 50,000–100,000 episodes, the agent learns the causal relationship between its actions and voltage outcomes.

## Revenue Cost of Network Safety

| Config | DP Revenue | RL Revenue | Gap (A\$/day) | Gap (%) | Gap (A\$/year) |
|--------|-----------|-----------|-------------|---------|---------------|
| **Baseline (no battery)** | **—** | **—** | **—** | **—** | **—** |
| ±50kW / 200kWh | 28.38 | 24.98 | 3.40 | 12.0% | 1,241 |
| ±80kW / 200kWh | 37.08 | 34.44 | 2.64 | 7.1% | 964 |
| ±80kW / 300kWh | 44.26 | 42.50 | 1.76 | 4.0% | 642 |
| ±80kW / 400kWh | 49.36 | 48.93 | 0.43 | 0.9% | 157 |
| ±100kW / 200kWh | 41.23 | 36.31 | 4.92 | 11.9% | 1,796 |
| ±100kW / 300kWh | 50.54 | 44.53 | 6.00 | 11.9% | 2,190 |
| ±100kW / 400kWh | 56.56 | 48.51 | 8.05 | 14.2% | 2,938 |

The revenue cost decreases with battery capacity: larger batteries achieve feasibility with smaller modifications to the DP strategy. At ±80kW/400kWh, the cost is only A\$0.43/day (A\$157/year) — network safety is essentially free.

The cost increases with dispatch limit: ±100kW configurations sacrifice more revenue because the DP strategy at ±100kW causes both overvoltage (midday charging at 100 kW) and undervoltage (evening depletion). RL must moderate both ends of the dispatch, requiring larger deviations from the revenue-optimal strategy.

## Key Findings

**1. Q-learning achieves 0 violations across all configurations.** DP achieves 0 violations in only 2 of 9 configurations (±50kW/300kWh and ±50kW/400kWh). The RL agent eliminates all violations by embedding network constraints directly in the reward signal.

**2. DP provides the revenue upper bound; RL provides the feasibility lower bound.** The two methods bracket the design space. DP answers "what is the maximum possible revenue?" while RL answers "what is the maximum revenue achievable without violating network constraints?"

**3. The oscillating evening dispatch is a novel strategy.** Rapid charge/discharge cycling during evening peak is revenue-suboptimal but network-optimal. This strategy cannot be found by any revenue-maximising algorithm and represents a genuine contribution of the RL approach.

**4. Battery capacity determines strategy type.** At 200 kWh, the agent must oscillate to maintain voltage support. At 400 kWh, sustained discharge is sufficient. The transition occurs around 300 kWh for this feeder topology.

**5. RL reduces network losses by 4–14%.** The oscillating strategy uses lower sustained current than DP's aggressive dispatch, reducing $I^2 R$ losses. The DNSP benefits from both fewer violations and lower loss costs.

**6. The revenue cost of network safety is configuration-dependent.** At ±80kW/400kWh, network safety costs only A\$157/year. At ±100kW/400kWh, it costs A\$2,938/year. This quantifies the value of voltage support for DNSP connection agreements.

## Training Configuration

| Parameter | Phase 1 | Phase 2 |
|-----------|---------|---------|
| Penalty | 0 | 5.0 (±80kW), 10.0 (±100kW) |
| OpenDSS calls | None (skip_network) | Every time step |
| Episodes | 30,000–50,000 | 50,000–100,000 |
| Epsilon | 0.3 → 0.05 | 0.1 → 0.001 |
| Alpha | 0.1 → 0.01 | 0.05 → 0.01 |
| SoC bins | 80 (±80kW), 100–120 (±100kW) | same |
| Actions | 33 (±80kW, ±100kW), 21 (±50kW) | same |
| Q-table init | DP value function | Phase 1 output |

## Branch A vs Branch B: Battery Spillover Analysis

The study feeder has two identical branches — Branch A (battery at Node A4) and Branch B (no battery, control group). This design tests whether a single community battery provides localised or feeder-wide voltage support.

### Results

| Config | Method | A4 Violations | B4 Violations | A4 V_min (pu) | B4 V_min (pu) | B4 Avg Lift |
|--------|--------|:---:|:---:|:---:|:---:|:---:|
| **Baseline** | **—** | **11** | **11** | **0.9285** | **0.9285** | **—** |
| ±50kW / 200kWh | DP | 4 | 4 | 0.9264 | 0.9267 | +0.0055 pu |
| ±50kW / 200kWh | RL | 0 | 0 | 0.9455 | 0.9413 | +0.0071 pu |
| ±80kW / 200kWh | DP | 5 | 6 | 0.9264 | 0.9267 | +0.0069 pu |
| ±80kW / 200kWh | RL | 0 | 0 | 0.9455 | 0.9413 | +0.0083 pu |
| ±80kW / 400kWh | DP | 3 | 3 | 0.9308 | 0.9286 | +0.0122 pu |
| ±80kW / 400kWh | RL | 0 | 0 | 0.9455 | 0.9413 | +0.0125 pu |
| ±100kW / 400kWh | DP | 4 | 4 | 0.9264 | 0.9267 | +0.0120 pu |
| ±100kW / 400kWh | RL | 0 | 0 | 0.9476 | 0.9406 | +0.0137 pu |

### Mechanism: Junction Voltage Rise

When the battery discharges at Node A4, current flows backward through the Branch A cables toward the junction bus. This raises the junction voltage, which propagates to Branch B. The voltage improvement at B4 is approximately 47% of the improvement at A4, determined by the feeder impedance ratio:
```
Trunk cable:   150m  (impedance from transformer to junction)
Branch cable:  200m  (impedance from junction to end-of-branch)
Total:         350m

Junction rise / A4 rise ≈ trunk impedance / total impedance ≈ 150/350 ≈ 43%
B4 rise / A4 rise ≈ 47% (measured across all configurations)
```

At the critical evening period t=35 (17:30):

| Config | A4 voltage lift | B4 voltage lift | Ratio |
|--------|:---:|:---:|:---:|
| RL ±50kW / 200kWh | +0.0381 pu | +0.0170 pu | 45% |
| RL ±80kW / 200kWh | +0.0618 pu | +0.0289 pu | 47% |
| RL ±80kW / 400kWh | +0.0618 pu | +0.0289 pu | 47% |
| RL ±100kW / 400kWh | +0.0770 pu | +0.0365 pu | 47% |

### Key Findings

**1. A single battery protects both branches.** Across all four RL configurations, the battery on Branch A eliminates all 11 violations on both A4 and B4. The DNSP does not need one battery per branch — one well-placed battery per feeder is sufficient.

**2. DP leaves residual violations on both branches; RL eliminates all.** Under DP dispatch, B4 has 3–6 remaining violations because the battery empties before the evening peak ends. The RL's oscillating strategy maintains discharge through the full evening, keeping both branches above the 0.94 pu limit.

**3. Branch B margins are thin.** B4 minimum voltage under RL is 0.9406–0.9416 pu — only 0.1–0.2% above the 0.94 limit. A4 has a more comfortable margin at 0.9455–0.9476 pu. Branch B is the marginal constraint: if the feeder had longer branches, higher Branch B loads, or more than two branches, the spillover might be insufficient.

**4. Higher dispatch power improves spillover.** The B4 average voltage lift increases with dispatch limit: +0.0071 pu at ±50kW to +0.0137 pu at ±100kW. This is because higher discharge power drives more current through the trunk cable, producing a larger junction voltage rise. However, the additional lift has diminishing returns — ±80kW provides most of the benefit.

### Implications for Battery Placement

The 47% attenuation ratio is specific to this feeder's 150m trunk / 200m branch geometry. On feeders with different topologies:

- **Short trunk, long branches** (e.g., 50m trunk, 300m branch): attenuation ratio drops to ~15%. A single battery may not protect the opposite branch. Multiple batteries or central placement at the junction would be needed.
- **Long trunk, short branches** (e.g., 250m trunk, 100m branch): attenuation ratio rises to ~70%. A single battery provides strong feeder-wide support.
- **Three or more branches**: the junction voltage rise is shared across all branches, but each branch's own cable drop remains. Central placement or coordinated multi-battery dispatch becomes the research question.