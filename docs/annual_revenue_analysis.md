# Full-Year Revenue Analysis: PyPSA Dispatch Optimisation

## Overview

This analysis replaces the single typical day revenue estimate with a full-year revenue distribution. Using PyPSA's linear optimal power flow (LOPF), we optimise the battery dispatch for every day of 2024 using AEMO NSW1 spot prices, producing 366 daily revenue figures that capture the full variability of NEM wholesale prices.

The PyPSA model solves the same arbitrage problem as our DP solver — maximise revenue subject to SoC constraints — but formulates it as a linear program (LP) solved by HiGHS. Both find the global optimum for unconstrained (no voltage constraints) revenue maximisation. The key advantage of PyPSA is speed: each daily LP solves in ~10ms, enabling the full-year sweep in under 60 seconds.


### Battery Configuration

| Parameter | Value | Source |
|-----------|-------|--------|
| Power rating | ±100 kW | GenCost 2hr spec |
| Energy capacity | 200 kWh | GenCost 2hr spec |
| Efficiency (one-way) | 95% | Round-trip 90.25% |
| Degradation cost | A\$0.02/kWh | Battery class default |
| Minimum SoC | 20 kWh (10%) | Reserve constraint |
| Initial SoC | 100 kWh (50%) | Each day starts fresh |
| Price data | AEMO NSW1, Jan–Dec 2024 | 5-min dispatch, resampled to 30-min |

### Relationship to Other Project Layers

```
PyPSA LOPF (this analysis)  →  365-day unconstrained revenue (LP, continuous actions)
DP solver (existing)        →  Single-day unconstrained revenue (backward induction, discrete actions)
RL Q-learning (existing)    →  Single-day network-safe revenue (OpenDSS voltage feedback)
```

PyPSA and DP solve the same problem with different methods. PyPSA uses continuous decision variables (can dispatch 42.3 kW), while DP uses a discrete action grid (e.g., 0, ±6, ±12, ..., ±100 kW). For our typical day (June 28), the results are close:

| Method | Revenue | Constraints |
|--------|:---:|-------------|
| PyPSA LOPF | A\$36.30 | SoC limits, efficiency, degradation |
| DP solver | A\$41.23 | Same (discrete actions, no degradation in objective matching) |
| RL Q-learning | A\$36.31 | Same + OpenDSS voltage limits |

## Annual Revenue Statistics

### Summary (±100kW / 200kWh, Calendar Year 2024)

| Metric | Value |
|--------|------:|
| Days analysed | 366 |
| Annual total | A\$36,190 |
| Mean daily | A\$98.88 |
| Median daily | A\$31.17 |
| Std dev | A\$388.24 |
| P10 (pessimistic day) | A\$7.34 |
| P90 (good day) | A\$94.43 |
| Min daily | A\$2.56 |
| Max daily (spike) | A\$4,808.33 |
| Spike days (> A\$500) | 10 |

### Revenue Distribution

The distribution is heavily right-skewed. Most days earn A\$10–50, but rare spike days dominate the annual total.

| Bucket | Days | % of year | Character |
|--------|:---:|:---:|-----------|
| < A\$10 | 51 | 13.9% | Low-spread days (mild weather, holidays) |
| A\$10–50 | 227 | 62.0% | Normal trading days — the bulk of the year |
| A\$50–100 | 52 | 14.2% | Above-average spread (seasonal transitions) |
| A\$100–500 | 26 | 7.1% | High-spread days (cold snaps, heatwaves) |
| > A\$500 | 10 | 2.7% | Extreme spike days (generator outages, NEM price cap) |

### The Spike Day Effect

10 spike days (2.7% of the year) contribute A\$19,617 — **54% of annual revenue**. This concentration makes the annual total highly sensitive to rare events.

| Scenario | Annual | Mean daily | Interpretation |
|----------|------:|------:|------|
| Full year (366 days) | A\$36,190 | A\$98.88 | Includes all spikes — best-case historical |
| Excluding top 5 days | A\$21,257 | A\$58.88 | Remove most extreme events |
| Excluding top 10 days | A\$16,573 | A\$46.55 | Remove all spike days |
| Excluding top 20 days | A\$13,303 | A\$38.45 | Conservative — stable revenue only |

### Top 10 Revenue Days

| Date | Revenue | Max price | Likely cause |
|------|------:|------:|------|
| 2024-05-08 | A\$4,808 | A\$16,600/MWh | Autumn cold snap, generator constraint |
| 2024-08-05 | A\$3,840 | A\$15,887/MWh | Winter peak demand |
| 2024-11-07 | A\$2,449 | A\$14,832/MWh | Spring heatwave onset |
| 2024-11-27 | A\$2,040 | A\$17,500/MWh | NEM price cap event |
| 2024-05-07 | A\$1,796 | A\$14,523/MWh | Preceding day of May 8 spike |
| 2024-02-29 | A\$1,594 | A\$13,326/MWh | Summer heat, leap day |
| 2024-12-02 | A\$1,277 | A\$13,502/MWh | Early summer heat |
| 2024-01-21 | A\$752 | A\$8,008/MWh | January heat event |
| 2024-12-06 | A\$555 | A\$8,044/MWh | December heat |
| 2024-12-03 | A\$507 | A\$9,371/MWh | Continued December heat |

Spike days cluster in autumn (May) and late spring/summer (Nov–Dec) when temperature extremes coincide with tight supply. The two highest days (May 7–8) are consecutive, suggesting a multi-day generator outage event.

### Seasonal Breakdown (Australian Seasons)

| Season | Months | Days | Total | Mean | Median |
|--------|--------|:---:|------:|------:|------:|
| Summer | Dec–Feb | 91 | A\$7,874 | A\$86.5 | A\$21.0 |
| Autumn | Mar–May | 92 | A\$9,810 | A\$106.6 | A\$23.9 |
| Winter | Jun–Aug | 92 | A\$8,862 | A\$96.3 | A\$38.4 |
| Spring | Sep–Nov | 91 | A\$9,644 | A\$106.0 | A\$31.0 |

Revenue is relatively even across seasons by total, but the median tells a different story: **winter has the highest median** (A\$38.4/day) because cold weather creates consistent daily price spreads, while summer and autumn have low medians (A\$21–24) inflated by rare spikes.

For a battery operator, winter provides the most reliable daily income. Spike revenue is a bonus concentrated in May, August, and November–December.

## Comparison with Single-Day Estimates

| Estimate | Daily | Annual | Basis |
|----------|------:|------:|-------|
| Our typical day (Jun 28) | A\$36.30 | A\$13,249 | Median-spread day, used in current NPV |
| PyPSA median day | A\$31.17 | A\$11,377 | 50th percentile of 366 days |
| Conservative (excl top 20) | A\$38.45 | A\$13,303 | Stable, repeatable revenue |
| Full year (incl spikes) | A\$98.88 | A\$36,190 | Historical 2024 including all events |
| TOU fixed daily | A\$81.56 | A\$29,790 | Guaranteed by retail tariff |

### Was Our Typical Day Representative?

Yes. Our typical day (A\$36.30) is very close to the annual median (A\$31.17) and to the conservative mean excluding spikes (A\$38.45). The single-day NPV estimate of A\$13,249/year was a reasonable representation of stable, repeatable spot revenue.

The full-year total of A\$36,190 is 2.7× higher because of spike days, but this overstates reliable revenue. A prudent investor would use the conservative estimate (A\$13,303) for base-case NPV and treat spike revenue as upside.

## Spot vs TOU: Full-Year Comparison

| Metric | Spot (PyPSA) | TOU (fixed) |
|--------|------:|------:|
| Daily revenue (median) | A\$31.17 | A\$81.56 |
| Daily revenue (mean) | A\$98.88 | A\$81.56 |
| Annual total | A\$36,190 | A\$29,790 |
| Revenue variance | Very high (σ = A\$388) | Zero |
| Spike day dependence | 54% from top 10 days | None |
| Conservative annual (excl spikes) | A\$13,303 | A\$29,790 |
| Predictability | Low — varies 50× day to day | Perfect — same every day |

### Key Finding: TOU Dominates on Risk-Adjusted Basis

Spot total revenue (A\$36,190) exceeds TOU (A\$29,790) in 2024, but this comparison is misleading:

**1. Spot revenue is unreliable.** Remove the top 10 spike days and spot annual drops to A\$16,573 — barely half of TOU. The A\$36,190 figure depends on 10 days that may not recur in other years.

**2. TOU revenue is guaranteed.** The retail tariff is published annually by ActewAGL. The battery earns A\$81.56 every day regardless of weather, demand, or generator outages. This predictability dramatically improves bankability — a lender can underwrite a TOU project with confidence.

**3. The median day tells the real story.** On a typical day, spot earns A\$31 while TOU earns A\$82 — a 2.6× TOU advantage. This is the daily revenue the operator can count on.

**4. Spike days favour spot but are a gamble.** A battery operator choosing spot over TOU is essentially betting A\$16,000/year of guaranteed revenue (the TOU advantage on non-spike days) against the chance of earning A\$20,000+ from spike days. In 2024, this bet paid off. In a mild year with fewer spikes, it would not.

### Why the TOU Spread Is Wider Than the Typical Spot Spread

The TOU price spread (A\$281/MWh between solar soak and peak) is structurally wider than the median spot spread because:

**The retail peak rate embeds a markup.** ActewAGL's peak rate (44.07 c/kWh = A\$441/MWh) bundles wholesale energy, network charges, retail margin, and hedging costs. The wholesale spot peak is typically A\$100–300/MWh.

**The retail solar soak rate has a floor.** The solar soak rate (16.00 c/kWh = A\$160/MWh) never goes negative, while wholesale spot prices can drop to -A\$100/MWh during solar surplus.

**The TOU spread applies every day.** The A\$281/MWh spread is guaranteed by the published tariff for every day of the year. The spot spread varies from A\$50 (quiet days) to A\$17,500 (extreme spikes).

## Implications for NPV

### Revised Revenue Estimates

| Scenario | Daily | Annual | Use case |
|----------|------:|------:|----------|
| **Spot conservative** | A\$38.45 | A\$14,052 | Base case for spot NPV — excludes unreliable spikes |
| Spot median | A\$31.17 | A\$11,377 | Pessimistic spot scenario |
| Spot full year | A\$98.88 | A\$36,190 | Optimistic — assumes 2024 spikes recur annually |
| **TOU guaranteed** | A\$81.56 | A\$29,790 | Base case for TOU NPV — no variance |

The conservative spot estimate (A\$14,052/year) is close to our original single-day extrapolation (A\$13,249/year). The NPV conclusions from the existing analysis remain valid:

- **Spot model (Tier 1):** NPV remains negative. Even with the full-year mean (A\$36,190/year), the spot model's NPV would improve but the revenue is unreliable.
- **TOU model (Tier 1):** NPV remains strongly positive (A\$139,083). The full-year analysis confirms that TOU revenue is higher than spot's reliable component and has zero variance.

### Revenue at Risk

A useful metric for lenders: what revenue can the operator count on with 90% confidence?

```
P10 daily revenue: A$7.34
P10 annual estimate: A$7.34 × 365 = A$2,679

P25 daily revenue: A$17.29
P25 annual estimate: A$17.29 × 365 = A$6,311
```

Under spot pricing, there is a 10% chance that any given day earns less than A\$7.34. The P25 annual estimate (A\$6,311) represents a conservative floor — even in a bad year with no spikes, the battery should earn at least this much. Compare with TOU's guaranteed A\$29,790.

## Methodology Notes

### PyPSA Model

The PyPSA network consists of one bus, one grid generator (unlimited power at spot price), and one StorageUnit (100 kW / 200 kWh). The LOPF minimises total system cost, which is equivalent to maximising arbitrage revenue.

#### Network Components

```
[Grid Generator] ←→ [Bus] ←→ [Battery StorageUnit]
  p_nom = ∞              ↑        p_nom = 0.1 MW
  marginal_cost = pₜ     |        max_hours = 2.0 h
                     [Load]       η_store = η_dispatch = 0.95
                   0.2 MW fixed   c_deg = A$20/MWh
```

The load (0.2 MW) is a modelling device: it ensures the grid generator always produces positive power, so the battery can displace grid output by discharging. Without it, the generator output can't go below zero and the battery has no incentive to discharge.

#### Decision Variables

At each snapshot $t \in \{0, 1, \ldots, 47\}$ (half-hourly), the optimiser chooses:

| Variable | Symbol | Unit | Meaning |
|----------|--------|------|---------|
| Grid generation | $g_t$ | MW | Power produced by the grid |
| Battery charge | $c_t$ | MW | Power flowing into the battery ($\geq 0$) |
| Battery discharge | $d_t$ | MW | Power flowing out of the battery ($\geq 0$) |
| State of charge | $s_t$ | MWh | Energy stored in the battery at end of period $t$ |

PyPSA internally splits the battery dispatch into two non-negative variables $c_t$ and $d_t$ rather than using a single signed variable. This linearises the asymmetric efficiency (charging multiplies by $\eta$, discharging divides by $\eta$).

#### Objective Function

PyPSA minimises total system cost over the day:

$$\min \sum_{t=0}^{47} w_t \left[ p_t \cdot g_t + c_{\text{deg}} \cdot d_t + c_{\text{deg}} \cdot c_t \right]$$

where:

| Symbol | Value | Meaning |
|--------|-------|---------|
| $w_t$ | 0.5 h | Snapshot weighting (30-minute periods) |
| $p_t$ | A\$/MWh | Spot price at period $t$ (time-varying) |
| $c_{\text{deg}}$ | A\$20/MWh | Degradation cost per MWh throughput |

The first term ($p_t \cdot g_t$) is the cost of grid electricity. When the battery discharges, it displaces grid generation — $g_t$ decreases and total cost falls. When the battery charges, $g_t$ increases and total cost rises. Minimising grid cost is equivalent to maximising arbitrage revenue.

The second and third terms ($c_{\text{deg}} \cdot d_t$ and $c_{\text{deg}} \cdot c_t$) penalise battery throughput in both directions, discouraging cycling on small price spreads.

#### Constraints

**Power balance** at the bus (Kirchhoff's Current Law):

$$g_t + d_t = L + c_t \qquad \forall \; t$$

where $L = 0.2$ MW is the fixed load. Grid generation plus battery discharge must equal load plus battery charging.

**State of charge transition** (energy balance):

$$s_t = s_{t-1} + \eta \cdot c_t \cdot w_t - \frac{d_t}{\eta} \cdot w_t \qquad \forall \; t \geq 1$$

Charging at $c_t$ MW for $w_t = 0.5$ hours stores $\eta \cdot c_t \cdot 0.5$ MWh (efficiency loss on input). Discharging at $d_t$ MW for 0.5 hours removes $d_t / \eta \cdot 0.5$ MWh (efficiency loss on output). Round-trip efficiency is $\eta^2 = 0.95^2 = 0.9025$.

**Initial condition:**

$$s_0 = s_{-1} + \eta \cdot c_0 \cdot w_0 - \frac{d_0}{\eta} \cdot w_0, \qquad s_{-1} = 0.1 \text{ MWh} \; (= 100 \text{ kWh})$$

**Power limits** (charge and discharge bounded by rated power):

$$0 \leq c_t \leq \bar{P}, \qquad 0 \leq d_t \leq \bar{P} \qquad \forall \; t$$

where $\bar{P} = 0.1$ MW (= 100 kW).

**Energy capacity limits:**

$$\underline{s} \leq s_t \leq \bar{s} \qquad \forall \; t$$

where $\bar{s} = 0.2$ MWh (= 200 kWh) and $\underline{s} = 0.02$ MWh (= 20 kWh, 10% reserve).

Note: the minimum SoC constraint is added as a custom linopy constraint because PyPSA's StorageUnit does not natively support `state_of_charge_min`. The implementation uses:

```python
m = n.optimize.create_model()
sus = m.variables["StorageUnit-state_of_charge"]
m.add_constraints(sus >= 0.02, name="StorageUnit-minimum_soc")
n.optimize.solve_model(solver_name="highs")
```

See [PyPSA documentation](https://docs.pypsa.org/v1.0.0/user-guide/network-optimization/) for the custom constraint API.

**Grid generation limits:**

$$0 \leq g_t \leq 10^6 \qquad \forall \; t$$

The upper bound is effectively unlimited. The lower bound of zero means the grid cannot absorb power — but with the fixed load of 0.2 MW and battery max discharge of 0.1 MW, the grid always produces at least 0.1 MW, so this constraint never binds.

**No terminal constraint:**

There is no constraint on the final SoC $s_{47}$. The battery is free to end the day at any level above the 10% reserve. This matches our DP formulation where $V_T(s) = 0$ for all states (no terminal value).

#### LP Size

For a single day (48 snapshots):

| | Count |
|---|---:|
| Decision variables | 192 (48 × 4: $g_t$, $c_t$, $d_t$, $s_t$) |
| Constraints | ~528 (power balance, energy balance, bounds, custom SoC min) |
| Nonzeros | ~719 |
| Solve time | ~10 ms (HiGHS dual simplex, 65 iterations) |

#### Revenue Extraction

After solving, the daily revenue is computed from the dispatch variables:

$$\text{Revenue} = \sum_{t=0}^{47} (d_t - c_t) \cdot p_t \cdot w_t \cdot \frac{1}{1000} - c_{\text{deg}}^{\text{kWh}} \cdot \sum_{t=0}^{47} (d_t + c_t) \cdot w_t \cdot 1000$$

The first term is the arbitrage profit: energy sold at high prices minus energy bought at low prices. The factor $1/1000$ converts from MW × A\$/MWh to A\$ (since power is in MW but we report revenue in A\$). The second term subtracts degradation cost on total throughput, where $c_{\text{deg}}^{\text{kWh}} = 0.02$ A\$/kWh and the factor $\times 1000$ converts MW to kW.

#### Comparison with DP Formulation

The PyPSA LP and our DP solve the same optimisation problem but differ in method:

| Aspect | PyPSA LP | DP (Bellman) |
|--------|----------|-------------|
| Method | All 48 periods simultaneously | Backward induction, period by period |
| Actions | Continuous ($c_t, d_t \in \mathbb{R}^+$) | Discrete grid (e.g., 0, ±6, ..., ±100 kW) |
| State | Continuous SoC | Discrete SoC bins (80–120 levels) |
| Solver | HiGHS LP (simplex method) | Custom Python (nested loops) |
| Optimality | Global optimum (LP is convex) | Global optimum (finite-horizon, exact) |
| Speed | ~10 ms per day | ~50 ms per day |
| Extensions | Linear constraints only | Nonlinear costs, stochastic prices |

### Limitations

**No network constraints.** PyPSA revenue represents the unconstrained optimum — the battery dispatches without regard to feeder voltage. Our RL results show that network-safe dispatch reduces revenue by 0–14% depending on configuration. The RL/PyPSA ratio from the typical day (A\$36.31 / A\$36.30 ≈ 1.0) suggests the gap is small for this price day, but spike days with extreme dispatch may have larger gaps.

**Single year of data.** 2024 may not be representative of future years. NEM price volatility depends on generator fleet composition, renewable penetration, weather, and policy — all of which change over time. The spike day contribution (54% of annual revenue) is particularly uncertain year to year.

**Independent daily optimisation.** Each day is optimised independently, starting at 50% SoC. In reality, the battery's SoC at midnight depends on the previous day's dispatch. Multi-day optimisation would capture inter-day energy storage (e.g., charging on Saturday for Monday morning peak), but the effect is small for a 2-hour battery.

**Continuous vs discrete actions.** PyPSA uses continuous decision variables while our DP uses discrete actions. This means PyPSA can extract slightly more revenue from partial dispatches. The effect is small (< A\$2/day on our typical day) but systematic.

## Data Files

| File | Contents |
|------|----------|
| `data/aemo/PRICE_AND_DEMAND_2024{01-12}_NSW1.csv` | Raw AEMO monthly price data |
| `data/aemo/nem_prices_NSW1_clean.csv` | Cleaned, resampled 30-min prices (full year) |
| `data/pypsa/annual_revenue.csv` | 366 rows: date, revenue, spread, min/max/mean price |

## Reproduction

```bash
# Download AEMO prices (if not already present)
python download_prices.py

# Run full-year optimisation (~60 seconds)
python run_pypsa_annual.py

# Or analyse cached results
python run_pypsa_annual.py --cached
```