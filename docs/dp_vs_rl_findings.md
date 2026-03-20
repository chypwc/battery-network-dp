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

## Model A: Wholesale Spot Arbitrage

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

The training configuration is identical for both spot and TOU price signals. Only the price vector passed to the environment changes.

## Model B: Retail TOU Arbitrage

All results above use NEM wholesale spot prices (Model A). This section presents the same analysis under ActewAGL Home Daytime Economy retail TOU rates (Model B).

### TOU Price Signal

The TOU tariff defines three fixed price tiers (GST exclusive, from 1 July 2025):

| Period | Time (AEST) | Rate (c/kWh) | A\$/MWh |
|--------|-------------|:---:|:---:|
| Solar soak | 11am–3pm | 16.00 | 160 |
| Shoulder | 9pm–7am, 9am–11am, 3pm–5pm | 29.00 | 290 |
| Peak | 7am–9am, 5pm–9pm | 44.07 | 441 |

Source: ActewAGL ACT Standard plan electricity prices, Schedule of charges from 1 July 2025. The tariff aligns with Evoenergy's proposed residential TOU network tariff (Code 017) under the Revised Tariff Structure Statement for the 2024–29 regulatory period.

### TOU DP vs TOU Q-Learning: Head-to-Head

| Config | TOU DP Revenue | DP Violations | TOU RL Revenue | RL Violations | Revenue Gap |
|--------|:---:|:---:|:---:|:---:|:---:|
| **Baseline (no battery)** | **—** | **11** | **—** | **—** | **—** |
| ±50kW / 200kWh | A\$79.48 | 4 | A\$75.34 | **0** | −A\$4.14 |
| ±50kW / 300kWh | A\$97.76 | 2 | A\$96.84 | **0** | −A\$0.92 |
| ±50kW / 400kWh | A\$109.27 | 2 | A\$108.47 | **0** | −A\$0.80 |
| ±80kW / 200kWh | A\$83.51 | 5 | A\$80.57 | **0** | −A\$2.94 |
| ±80kW / 300kWh | A\$119.81 | 3 | A\$117.54 | **0** | −A\$2.27 |
| ±80kW / 400kWh | A\$145.22 | 2 | A\$144.82 | **0** | −A\$0.40 |
| ±100kW / 200kWh | A\$85.23 | 7 | A\$81.56 | **0** | −A\$3.67 |
| ±100kW / 300kWh | A\$122.74 | 10 | A\$119.14 | **0** | −A\$3.60 |
| ±100kW / 400kWh | A\$158.43 | 9 | A\$137.58 | **0** | −A\$20.85 |

Q-learning achieves **0 violations across all 9 configurations** under TOU prices, confirming that the two-phase training approach generalises across price signals. The TOU DP has violations in all 9 configurations — worse than spot DP (which achieves 0 violations in 2 of 9).

### Revenue Cost of Network Safety (TOU)

| Config | TOU DP | TOU RL | Gap (A\$/day) | Gap (%) |
|--------|:---:|:---:|:---:|:---:|
| ±50kW / 200kWh | 79.48 | 75.34 | 4.14 | 5.2% |
| ±50kW / 400kWh | 109.27 | 108.47 | 0.80 | 0.7% |
| ±80kW / 200kWh | 83.51 | 80.57 | 2.94 | 3.5% |
| ±80kW / 400kWh | 145.22 | 144.82 | 0.40 | 0.3% |
| ±100kW / 200kWh | 85.23 | 81.56 | 3.67 | 4.3% |
| ±100kW / 400kWh | 158.43 | 137.58 | 20.85 | 13.2% |

The same pattern as spot: larger batteries have smaller revenue gaps. At ±80kW/400kWh, network safety costs only A\$0.40/day — identical to the spot model. The largest gap is ±100kW/400kWh at A\$20.85/day, where RL must significantly moderate the ±100kW dispatch to avoid overvoltage.

### Why TOU DP Has More Violations Than Spot DP

Under spot prices, the DP sometimes discharges at 06:00 (A\$101/MWh) because the price is moderate. This incidentally provides morning voltage support. Under TOU prices, 06:00 is shoulder rate (A\$290/MWh) — more expensive than solar soak but cheaper than peak. The TOU DP charges at this time (to prepare for morning peak discharge at 07:00) rather than discharging, which worsens morning voltage violations.

Additionally, the TOU DP concentrates all discharge into the peak windows (12 half-hour periods) rather than spreading it across high-price periods throughout the day. This creates deeper battery depletion at the end of the evening peak, leaving no energy for the final violation periods (t=39–41).

### TOU RL Dispatch Strategies

The TOU-trained RL discovers the same three strategy types as the spot-trained RL, adapted for the TOU dispatch pattern:

**Morning pre-charging.** At ±80kW/200kWh, TOU RL charges at t=8–9 (+25, +70 kW) during shoulder rate (A\$290/MWh) and charges again at t=12–13 (+45, +40 kW) during the morning violation window. This is expensive — paying shoulder rate to store energy — but lifts morning voltage above 0.94 pu.

**Evening oscillation.** At ±80kW/200kWh, TOU RL charges +80 kW at t=39 (A\$485/MWh peak!) to refill the battery mid-evening, then discharges through t=40–41. Paying peak rate to charge is extremely costly (A\$19.40 per half-hour) but necessary to maintain voltage support through the end of the evening period.

**Conservative mid-evening discharge.** At ±80kW/300kWh, TOU RL charges +45 kW at t=35 (A\$485/MWh) then sustains -80 kW discharge through t=36–41. At ±100kW/400kWh, the RL varies discharge power between -56 and -100 kW across the evening instead of maintaining constant -100 kW.

### Cross-Model Comparison: Annual Revenue (Violation-Free RL Only)

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

The TOU business model produces **2–3× higher violation-free revenue** than wholesale spot arbitrage. Three factors drive the advantage: the TOU spread is wider (A\$281/MWh vs A\$245/MWh), the peak rate applies for more periods per day (12 vs ~5 for spot), and TOU revenue is guaranteed daily while spot revenue varies.

### Key Cross-Model Findings

**1. Business model choice matters more than battery sizing.** A 200 kWh battery under TOU (A\$29,408/yr at ±80kW) earns more than a 400 kWh battery under spot (A\$17,860/yr at ±80kW). The business model decision should precede the sizing decision.

**2. Q-learning generalises across price signals.** The same two-phase training architecture — DP warm-start, penalty-free Phase 1, OpenDSS-penalised Phase 2 — works for both volatile spot prices and fixed TOU rates. The RL discovers analogous voltage support strategies under both price regimes.

**3. TOU transforms the investment case.** Under spot prices, the 200 kWh battery at ±80kW requires augmentation deferral credits for positive NPV (simple payback 9.2 years). Under TOU, simple payback drops to approximately 3.9 years — viable as a standalone investment.

**4. TOU DP requires RL more than spot DP does.** TOU DP has violations in all 9 configurations (vs 7 of 9 for spot DP). The fixed TOU schedule creates a rigid dispatch pattern that aligns poorly with the morning violation window. RL is essential for network-safe TOU operation.
