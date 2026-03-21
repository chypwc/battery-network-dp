# NPV Analysis: Community Battery Investment

## Model

The net present value of a community battery investment over $Y$ years is:

$$NPV = -C_0 + \sum_{y=1}^{Y} \frac{R_y + S_y - M_y}{(1+r)^y} - \frac{C_{\text{repl}}}{(1+r)^{y_r}}$$

with an optional DNSP-only augmentation deferral term:

$$NPV_{\text{DNSP}} = NPV + PV_{\text{aug}}$$

where the annual revenue accounts for capacity fade with reset at module replacement:

$$R_y = 365 \cdot p_{\text{daily}} \cdot f(y), \quad f(y) = \max\left(0.7, \; 1 - \delta \cdot \begin{cases} y & \text{if } y \leq y_r \\\\ y - y_r & \text{if } y > y_r \end{cases}\right)$$

| Symbol | Meaning | Value | Source |
|--------|---------|-------|--------|
| $C_0$ | Initial capital cost | $E \times c_{\text{kWh}}$ | GenCost 2025 |
| $Y$ | Project lifetime | 20 years | Industry standard |
| $r$ | Discount rate | 6.53% | AER RORI 2025 |
| $p_{\text{daily}}$ | Daily RL revenue at full capacity | Varies by model and config | Q-learning results |
| $f(y)$ | Capacity fade factor | Resets to 1.0 at replacement | Linear 2%/year |
| $\delta$ | Annual fade rate | 0.02 | Industry estimate |
| $y_r$ | Module replacement year | 12 | 70% capacity threshold |
| $S_y$ | Export LRMC saving | $P_{\text{absorb}} \times c_{\text{LRMC}}$ = A\$1,150/yr | Evoenergy TSS 2024 |
| $M_y$ | O&M cost | $\mu \times C_0$ (1.5% of capital) | Industry estimate |
| $C_{\text{repl}}$ | Module replacement cost | $E \times c_{\text{module,2037}}$ | GenCost projected |
| $PV_{\text{aug}}$ | Avoided augmentation PV | $C_{\text{aug}} / (1+r)^{n_d}$ | Evoenergy estimate |

### Who Receives Each Revenue Stream?

Avoided augmentation and export LRMC savings are network benefits that accrue to the DNSP (Evoenergy), not to the battery operator. Whether the operator receives a payment for these services depends on the contractual arrangement:

| Revenue component | Model A (Market participant) | Model B (Community group) | Model C (DNSP-owned) |
|---|:---:|:---:|:---:|
| Arbitrage revenue ($R_y$) | Yes — NEM spot | Yes — retail TOU bill savings | No — not a market participant |
| Export LRMC saving ($S_y$) | Possibly — if DNSP contracts | Possibly — if DNSP contracts | Yes — direct network benefit |
| Avoided augmentation ($PV_{\text{aug}}$) | No — unless DNSP pays | No — unless DNSP pays | Yes — direct cost saving |

### Three-Tier NPV Framework

Results are reported at three tiers reflecting different assumptions about DNSP payments to the battery operator:

**Tier 1: Arbitrage only (most realistic).** The operator receives only arbitrage revenue ($R_y$) and pays battery costs ($C_0$, $M_y$, $C_{\text{repl}}$). No payments from the DNSP are included. This is the most realistic scenario for a market participant (Model A) or community group (Model B), since DNSP network support contracts for community batteries do not yet exist in the ACT regulatory framework.

$$NPV_1 = -C_0 + \sum_{y=1}^{Y} \frac{R_y - M_y}{(1+r)^y} - \frac{C_{\text{repl}}}{(1+r)^{y_r}}$$

**Tier 2: + augmentation deferral.** The DNSP pays the operator for deferring a specific transformer upgrade (A\$45,000 deferred by 10 years, PV = A\$21,095). This is a concrete, project-level benefit that could be contracted under the NER's non-network alternatives framework — a mechanism that allows DNSPs to procure demand management or generation services as an alternative to network augmentation.

$$NPV_2 = NPV_1 + PV_{\text{aug}}$$

**Tier 3: + augmentation + export LRMC (theoretical maximum).** The DNSP further pays the operator for reducing solar export flows, valued at the system-wide LRMC of export services (A\$1,150/yr, 20-year PV = A\$12,641). This is more abstract — the A\$23/kW/year LRMC is derived from Evoenergy's network-wide average incremental cost methodology, not from a specific avoided project on this feeder. A practical DNSP contract would more likely reference a specific avoided project (Tier 2) than a system-wide average cost.

$$NPV_3 = NPV_2 + \sum_{y=1}^{Y} \frac{S_y}{(1+r)^y}$$

**Note on potential overlap between Tier 2 and Tier 3.** The augmentation deferral (Tier 2) and export LRMC saving (Tier 3) are conceptually separate services — the battery reduces peak demand through evening discharge (deferring demand-driven augmentation) and absorbs midday solar through daytime charging (reducing export-driven network costs). 
The clean way to think about it is that the DNSP's total avoided cost from the battery has two components, but they come from the same pool of network investment:

- The battery reduces **peak demand** (evening discharge) → defers demand-driven augmentation
- The battery reduces **solar exports** (midday charging) → defers export-driven augmentation

However, both benefits may ultimately defer the same physical infrastructure. If the transformer upgrade is triggered by both peak demand and reverse solar flow, some of the LRMC saving is already captured in the augmentation deferral, and Tier 3 partially double-counts. On our feeder, the violations are demand-driven (evening undervoltage), so the transformer deferral is primarily a demand-side benefit and the export LRMC is a separate export-side benefit. Whether Evoenergy would pay for both depends on how they attribute their capital planning across demand and export drivers. The three-tier framework presents the range; the reader should assess which tier is appropriate for their regulatory and contractual context.

## Input Parameters

### Capital Costs (GenCost 2025, current policies)

| Parameter | 200 kWh (2hr) | 400 kWh (4hr) |
|-----------|:---:|:---:|
| Total installed (A\$/kWh) | 580 | 406 |
| Battery module (A\$/kWh) | 309 | 269 |
| BOP (A\$/kWh) | 271 | 137 |
| Total capital (A\$) | 116,000 | 162,400 |

### Module Replacement at Year 12 (GenCost 2037 projected)

| Scenario | 2hr module (A\$/kWh) | 4hr module (A\$/kWh) |
|----------|:---:|:---:|
| Current policies | 195 | 168 |
| NZE post 2050 | 157 | 106 |
| NZE by 2050 | 98 | 88 |

### Revenue and Network Value

The primary analysis uses ±100kW dispatch, matching the GenCost 2hr and 4hr power rating assumptions. The ±80kW results are reported as a sensitivity (conservative design with wider voltage margins).

**Single-day RL revenue (used in original NPV sheets):**

| Parameter | Model A (Spot) | Model B (TOU) | Source |
|-----------|:---:|:---:|--------|
| Daily RL revenue ±100kW / 200kWh | A\$36.31 | A\$81.56 | Q-learning (0 violations) |
| Daily RL revenue ±100kW / 400kWh | A\$48.51 | A\$137.58 | Q-learning (0 violations) |
| Daily RL revenue ±80kW / 200kWh (sensitivity) | A\$34.44 | A\$80.57 | Q-learning (0 violations) |
| Daily RL revenue ±80kW / 400kWh (sensitivity) | A\$48.93 | A\$144.82 | Q-learning (0 violations) |

**Full-year spot revenue (used in new NPV sheets):**

| Scenario | Annual | Basis |
|----------|------:|-------|
| Spot — top line (RL, incl spikes) | A\$37,422 | 366-day DP × RL/DP ratios from 5 representative days |
| Spot — bottom line (excl top 20 spikes) | A\$13,303 | PyPSA 366 days, removing top 20 spike days |
| Spot — single typical day × 365 (original) | A\$13,249 | June 28, 2024 (median spread day) |

The full-year analysis reveals that the original single-day estimate (A\$13,249/year) closely matches the conservative bottom line (A\$13,303/year) — confirming it was a reasonable representation of stable, repeatable revenue. The top line (A\$37,422/year) is 2.8× higher because 10 spike days contribute 44% of annual spot revenue.

TOU revenue does not require a full-year analysis because the retail tariff is fixed: A\$81.56/day every day, A\$29,790/year with zero variance.

| Other parameters | Value | Source |
|-----------|-------|--------|
| Export absorption power | 50 kW | Midday solar charge |
| LRMC export rate | A\$23/kW/year | Evoenergy TSS 2024 |
| O&M rate | 1.5% of capital/year | Industry estimate |
| Discount rate | 6.53% | AER RORI 2025 |

Model A price signal: NEM NSW1 spot prices (calendar year 2024, 366 days).
Model B price signal: ActewAGL Home Daytime Economy tariff (GST excl., from 1 July 2025). Solar soak 16.00 c/kWh, shoulder 29.00 c/kWh, peak 44.07 c/kWh. Spread A\$281/MWh.

Avoided augmentation (DNSP benefit only):

| Parameter | Value | Source |
|-----------|-------|--------|
| Avoided augmentation cost | A\$45,000 | Transformer upgrade estimate |
| Augmentation deferral period | 10 years | Assumption |
| PV of deferral | A\$21,095 | Discounted at 6.53% |

## Results

### Model A: Wholesale Spot Arbitrage (±100kW dispatch, RL network-safe)

| Metric | 200 kWh (2hr) | 400 kWh (4hr) |
|--------|---------|---------|
| Capital cost | A\$116,000 | A\$162,400 |
| Year 1 revenue | A\$12,988 | A\$17,356 |
| Year 1 net cash flow | A\$11,248 | A\$14,916 |
| Year 12 replacement cost | A\$39,000 | A\$67,200 |
| Simple payback | 10.3 years | 10.9 years |

**Three-tier NPV (200 kWh / 400 kWh):**

| Tier | What it includes | 200 kWh | 400 kWh | Realistic? |
|------|-----------------|:---:|:---:|------------|
| **Tier 1: Arbitrage only** | Revenue − costs | **-A\$23,268** | **-A\$46,801** | Most realistic for market participants |
| Tier 2: + augmentation | + deferred transformer (A\$21,095 PV) | -A\$2,173 | -A\$25,706 | Requires DNSP contract for specific project |
| Tier 3: + aug + LRMC | + export saving (A\$12,641 PV) | +A\$10,468 | -A\$13,065 | Theoretical maximum, unlikely in practice |

**Tier 1 is the most realistic** for a market participant or community group. The operator earns arbitrage revenue and pays battery costs — no DNSP payments are involved.

**Tier 2** requires Evoenergy to enter a network support agreement paying the operator for deferring a specific transformer upgrade. This is technically possible under the NER's non-network alternatives framework but has not been implemented for community batteries in the ACT.

**Tier 3** further assumes Evoenergy pays the operator for reducing solar export flows, valued at the system-wide LRMC of export services. This is the most abstract — the A\$23/kW/year LRMC is an aggregate figure derived from Evoenergy's network-wide average incremental cost methodology, not from a specific avoided project on this feeder. A practical DNSP contract would more likely reference a specific avoided project (Tier 2) than a system-wide average cost.

Under spot prices, the 200 kWh battery only turns positive at Tier 3 — requiring the DNSP to pay for both the specific transformer deferral and the system-wide export LRMC saving. The 400 kWh battery remains negative across all tiers.

### Model B: Retail TOU Arbitrage (±100kW dispatch, RL network-safe)

| Metric | 200 kWh (2hr) | 400 kWh (4hr) |
|--------|---------|---------|
| Capital cost | A\$116,000 | A\$162,400 |
| Year 1 revenue | A\$29,194 | A\$49,254 |
| Year 1 net cash flow | A\$27,454 | A\$46,810 |
| Year 12 replacement cost | A\$39,000 | A\$67,200 |
| Simple payback | **4.2 years** | **3.5 years** |

**Three-tier NPV (200 kWh / 400 kWh):**

| Tier | What it includes | 200 kWh | 400 kWh | Realistic? |
|------|-----------------|:---:|:---:|------------|
| **Tier 1: Arbitrage only** | Revenue − costs | **+A\$139,083** | **+A\$272,713** | Most realistic for community groups |
| Tier 2: + augmentation | + deferred transformer (A\$21,095 PV) | +A\$160,177 | +A\$293,808 | Bonus if DNSP contract exists |
| Tier 3: + aug + LRMC | + export saving (A\$12,641 PV) | +A\$172,819 | +A\$306,449 | Theoretical maximum |

Under TOU retail arbitrage, **all three tiers are strongly positive**. The battery is viable from pure arbitrage revenue (Tier 1) without any DNSP payment. DNSP network benefits are a bonus that improves an already strong investment case.

### Cross-Model Comparison (±100kW / 200kWh, Tier 1 — Arbitrage Only)

| Metric | Model A (Spot) | Model B (TOU) | TOU Advantage |
|--------|:---:|:---:|:---:|
| Daily RL revenue | A\$36.31 | A\$81.56 | +A\$45.25 (2.2×) |
| Year 1 net cash flow | A\$11,248 | A\$27,454 | +A\$16,206 |
| Simple payback | 10.3 years | 4.2 years | -6.1 years |
| NPV (20 years) | -A\$23,268 | +A\$139,083 | +A\$162,351 |
| Viable at Tier 1? | No | **Yes** | — |
| Viable at Tier 2? | No (-A\$2,173) | Yes (+A\$160,177) | — |
| Viable at Tier 3? | Marginal (+A\$10,468) | Yes (+A\$172,819) | — |

### Cash Flow Profile (±100kW / 200kWh, Model A)

The 200 kWh battery's cash flow illustrates the capacity fade reset at module replacement:

| Year | Capacity | Annual Revenue | O&M | Replacement | Net CF |
|------|:---:|:---:|:---:|:---:|:---:|
| 0 | — | — | — | — | -A\$116,000 |
| 1 | 98% | A\$12,988 | -A\$1,740 | — | A\$11,248 |
| 5 | 90% | A\$11,928 | -A\$1,740 | — | A\$10,188 |
| 10 | 80% | A\$10,603 | -A\$1,740 | — | A\$8,863 |
| 12 | 76% | A\$10,073 | -A\$1,740 | -A\$39,000 | -A\$30,667 |
| 13 | 98% (reset) | A\$12,988 | -A\$1,740 | — | A\$11,248 |
| 15 | 94% | A\$12,459 | -A\$1,740 | — | A\$10,719 |
| 20 | 84% | A\$11,134 | -A\$1,740 | — | A\$9,394 |

Export LRMC saving (A\$1,150/yr) is excluded from the operator's cash flow — it is a DNSP benefit.

### Key Result

Under Model A (spot), the 200 kWh battery achieves marginal viability only at Tier 3 — requiring the DNSP to pay for both a specific transformer deferral and system-wide export LRMC saving. Under Model B (TOU), the same battery is strongly viable at Tier 1 from pure retail arbitrage revenue (NPV +A\$139,083) without any DNSP payment. The business model choice — not battery sizing, dispatch algorithm, or network constraints — is the primary determinant of investment viability.

## Sensitivity and Assumptions

### Dispatch Limit: ±80kW (Conservative Design)

The primary analysis uses ±100kW to match GenCost's 2hr/4hr power rating specifications. At ±80kW, the inverter is underutilised but voltage margins are wider (V_min = 0.9413 pu vs 0.9406 pu at ±100kW). Tier 1 NPV comparison:

| Config | Spot RL daily | TOU RL daily | Spot Tier 1 NPV | TOU Tier 1 NPV |
|--------|:---:|:---:|:---:|:---:|
| ±100kW / 200kWh (primary) | A\$36.31 | A\$81.56 | -A\$23,268 | +A\$139,083 |
| ±80kW / 200kWh (sensitivity) | A\$34.44 | A\$80.57 | -A\$29,969 | +A\$135,533 |
| ±100kW / 400kWh (primary) | A\$48.51 | A\$137.58 | -A\$46,801 | +A\$272,713 |
| ±80kW / 400kWh (sensitivity) | A\$48.93 | A\$144.82 | -A\$45,296 | +A\$298,675 |

The ±80kW / 400kWh TOU configuration actually earns higher daily revenue (A\$144.82 vs A\$137.58) than ±100kW / 400kWh TOU. This is because at ±100kW, the RL must moderate its discharge more aggressively to avoid overvoltage during midday charging and undervoltage during evening peak — the revenue cost of network safety is 13.2% at ±100kW versus only 0.3% at ±80kW. The ±80kW dispatch is a better match for the 400 kWh battery on this feeder.

### Full-Year Revenue Analysis: Top Line vs Bottom Line

The full-year PyPSA + DP analysis (366 days of 2024 AEMO NSW1 prices) reveals that spot revenue is dominated by rare spike events:

| Statistic | PyPSA | DP |
|-----------|------:|------:|
| Annual total | A\$36,190 | A\$38,661 |
| Mean daily | A\$98.88 | A\$105.63 |
| Median daily | A\$31.17 | A\$37.83 |
| Spike days (> A\$500/day) | 10 | 10 |
| Spike contribution | 44% of annual | 41% of annual |

The top 10 spike days (2.7% of the year) contribute nearly half the annual revenue. Removing them, spot annual drops to A\$16,573 (PyPSA). This extreme concentration of revenue in rare events creates two valid NPV scenarios:

**Top line (A\$37,422/year):** Uses the full-year RL-estimated revenue, assuming 2024's spike pattern recurs annually. This is the best-case spot scenario. The RL estimate applies RL/DP ratios from 5 representative days (one per revenue bucket) to the 366-day DP results, accounting for the 3.2% network safety cost.

**Bottom line (A\$13,303/year):** Excludes the top 20 spike days, representing only stable, repeatable revenue. This is the worst-case spot scenario. It closely matches the original single-day estimate (A\$13,249/year), confirming that our typical day was representative of non-spike conditions.

### NPV: Four Scenarios (±100kW / 200kWh)

| Scenario | Annual Revenue | NPV (Tier 1) | Simple Payback |
|----------|------:|------:|------:|
| **Spot — top line (incl spikes)** | A\$37,422 | **+A\$214,013** | 3.3 yr |
| **TOU — guaranteed** | A\$29,790 | **+A\$139,083** | 3.9 yr |
| Spot — bottom line (excl spikes) | A\$13,303 | -A\$22,779 | 10.0 yr |
| Spot — single day × 365 (original) | A\$13,249 | -A\$23,268 | 8.9 yr |

The spot model NPV ranges from -A\$23K (bottom line) to +A\$214K (top line) depending on spike day assumptions. The investment decision hinges entirely on whether the operator expects spike days to recur. TOU sits at +A\$139K with certainty.

**Key insight:** The original single-day NPV (-A\$23,268) was not wrong — it accurately represents the bottom line. The full-year analysis doesn't overturn it; rather, it reveals the upside from spike days that the typical day misses.

### Violation Context

All revenue figures above use network-safe (RL) dispatch with zero violations. For reference, unconstrained dispatch (PyPSA and DP) causes 3,000+ violations per year — every single day has violations. The network safety cost is A\$1,239/year (3.2% of DP revenue), which is already deducted from the RL revenue estimate.

### Why the TOU Spread Is Wider Than the Typical Spot Spread

The TOU spread (A\$281/MWh) is wider than the median spot day spread (A\$213/MWh) for structural reasons:

**The retail peak rate embeds a markup.** ActewAGL's peak rate (44.07 c/kWh = A\$441/MWh) bundles wholesale energy cost, Evoenergy network charges, retail margin, hedging costs, and green scheme levies. The wholesale spot peak on a normal day is typically A\$100–300/MWh.

**The TOU charging cost has a floor.** Under TOU, the cheapest charging window is A\$160/MWh (solar soak). Under spot pricing, midday prices can drop below zero — the battery gets **paid** to charge. This benefits spot on days with negative prices (20–30% of days), but the TOU spread is available every day.

**The TOU advantage narrows but persists in the full year.** Using the full-year data, the TOU annual revenue (A\$29,790) is 80% of the spot top line (A\$37,422). The original single-day comparison suggested a 2.2× TOU advantage — the full-year data narrows this to 0.8× when spikes are included, but TOU still dominates on a risk-adjusted basis because 44% of spot revenue depends on 10 unpredictable days.

### Export LRMC Saving: DNSP Benefit Only

The A\$1,150/year LRMC saving assumes 50 kW solar absorption every day. This is excluded from the operator's NPV because it accrues to Evoenergy as avoided network export costs. If Evoenergy were to pay the operator for this service through a network support contract, the payment would depend on actual absorption levels:

| Export absorption | Annual DNSP saving | Over 20 years (discounted) |
|:---:|:---:|:---:|
| 50 kW (our estimate) | A\$1,150 | ~A\$12,600 |
| 35 kW (conservative) | A\$805 | ~A\$8,800 |
| 25 kW (pessimistic) | A\$575 | ~A\$6,300 |

### Avoided Augmentation: Most Uncertain

The augmentation value depends on three uncertain inputs:

| Parameter | Conservative | Base | Optimistic |
|-----------|:---:|:---:|:---:|
| Augmentation cost | A\$30,000 | A\$45,000 | A\$70,000 |
| Deferral period | 5 years | 10 years | 15 years |
| **PV of deferral** | **A\$8,500** | **A\$21,095** | **A\$46,800** |

The augmentation cost depends on what fix the DNSP would otherwise implement (transformer upgrade A\$30,000–60,000 vs cable reconductoring A\$70,000–175,000). The deferral period depends on local load growth — stable established suburbs may defer 15–20 years, while growing suburbs may only defer 5 years.

### Module Replacement: Conservative Assumption

The year-12 replacement at projected 2037 costs (A\$195/kWh for 2hr) may be conservative:

- Operators may **defer replacement** to year 14–15 if 76% capacity is still acceptable, reducing the discounted cost
- Operators may **not replace at all** if the battery is decommissioned or if a newer technology is available, saving the entire A\$39,000
- Module costs may fall **faster than projected** under the NZE scenario (A\$98/kWh instead of A\$195/kWh), reducing replacement cost to A\$19,600

### O&M Rate: Uncertain

1.5% of capital per year is an industry rule of thumb. Reported community battery O&M ranges from 0.5% (well-designed, minimal intervention) to 3% (including insurance, site lease, active management).

### Summary of Assumption Risks

| Component | Direction of bias | NPV impact (spot) |
|-----------|------------------|:---:|
| Spot revenue — single day | Underestimates (misses spikes) | Original NPV too pessimistic by ~A\$237K |
| Spot revenue — with spikes | Overstates stable component | Top line may not recur annually |
| TOU revenue (fixed tariff) | Accurate | Neutral |
| Export LRMC | Excluded from operator NPV | Neutral (DNSP benefit) |
| Avoided augmentation | Excluded from operator NPV | Neutral (DNSP benefit) |
| Module replacement timing | Conservative | +A\$0 to +A\$18,000 |
| O&M rate | Uncertain | -A\$5,000 to +A\$5,000 |
| Capital cost | About right | Neutral |

For the spot model, the revenue distribution (spike dependence) is the dominant risk. For the TOU model, the risk is primarily in whether the tariff structure is maintained by ActewAGL and Evoenergy over the 20-year project life.

## Conclusions

**1. The spot model NPV ranges from -A\$23K to +A\$214K.** The investment outcome depends entirely on spike day frequency. The top line (A\$37,422/year, including spikes) gives a strongly positive NPV with 3.3-year payback. The bottom line (A\$13,303/year, excluding spikes) gives a negative NPV with 10-year payback. An investor must decide which scenario to underwrite.

**2. TOU provides a certain +A\$139K NPV.** The TOU model is positive regardless of market conditions because revenue is fixed by the published retail tariff. Simple payback is 3.9 years. This certainty makes TOU the bankable choice — a lender can underwrite the project with confidence.

**3. The original single-day NPV was the bottom line, not wrong.** Our original estimate (A\$13,249/year → NPV -A\$23,268) matches the conservative full-year figure (A\$13,303/year → NPV -A\$22,779). The full-year analysis reveals the spike upside that the typical day misses, but the conservative case remains valid.

**4. TOU dominates spot on a risk-adjusted basis.** Even at the spot top line (A\$37,422/year), the spot model's revenue depends on 10 unpredictable spike days. If 2025 has 3 spike days instead of 10, spot annual revenue drops to ~A\$22,000 — below TOU's guaranteed A\$29,790. TOU earns less than spot's best case but more than spot's likely case.

**5. The business model is the dominant investment variable.** TOU transforms the 200 kWh battery from marginal (spot bottom line NPV -A\$23K) to strongly profitable (TOU NPV +A\$139K). This effect exceeds the impact of doubling battery capacity, changing the dispatch algorithm, or adding DNSP augmentation credits.

**6. Network safety cost is negligible in the NPV.** The RL network-safe dispatch sacrifices A\$1,239/year (3.2% of DP revenue) to eliminate all 3,021 annual violations. Over 20 years discounted, this is ~A\$13,000 — a small fraction of the capital cost and well within the uncertainty range of other assumptions.

**7. Additional revenue streams remain important for spot-only operators.** FCAS participation (est. A\$3,000–5,000/year) or DNSP network support payments (est. A\$5,000–10,000/year) would push the spot bottom line NPV positive. These are essential for Model A viability without spike revenue but optional for Model B.

**8. Falling battery costs will improve both models.** GenCost projects 2hr battery costs declining from A\$580/kWh (2025) to A\$306/kWh (2035) under current policies. At A\$306/kWh, the spot bottom line NPV turns positive. The TOU model is already strongly viable at current costs.

For the full-year revenue distribution, violation analysis, and representative day methodology, see [docs/full_year_dispatch_analysis.md](docs/full_year_dispatch_analysis.md).