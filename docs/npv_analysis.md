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

| Parameter | Model A (Spot) | Model B (TOU) | Source |
|-----------|:---:|:---:|--------|
| Daily RL revenue ±80kW / 200kWh | A\$34.44 | A\$80.57 | Q-learning (0 violations) |
| Daily RL revenue ±80kW / 400kWh | A\$48.93 | A\$144.82 | Q-learning (0 violations) |
| Export absorption power | 50 kW | 50 kW | Midday solar charge |
| LRMC export rate | A\$23/kW/year | A\$23/kW/year | Evoenergy TSS 2024 |
| O&M rate | 1.5% of capital/year | 1.5% of capital/year | Industry estimate |
| Discount rate | 6.53% | 6.53% | AER RORI 2025 |

Model A price signal: NEM NSW1 spot prices (typical day, spread A\$245/MWh).
Model B price signal: ActewAGL Home Daytime Economy tariff (GST excl., from 1 July 2025). Solar soak 16.00 c/kWh, shoulder 29.00 c/kWh, peak 44.07 c/kWh. Spread A\$281/MWh.

Avoided augmentation (DNSP benefit only):

| Parameter | Value | Source |
|-----------|-------|--------|
| Avoided augmentation cost | A\$45,000 | Transformer upgrade estimate |
| Augmentation deferral period | 10 years | Assumption |
| PV of deferral | A\$21,095 | Discounted at 6.53% |

## Results

### Model A: Wholesale Spot Arbitrage (±80kW dispatch, RL network-safe)

| Metric | 200 kWh | 400 kWh |
|--------|---------|---------|
| Capital cost | A\$116,000 | A\$162,400 |
| Year 1 revenue | A\$12,319 | A\$17,502 |
| Year 1 net cash flow | A\$10,579 | A\$15,066 |
| Year 12 replacement cost | A\$39,000 | A\$67,200 |
| Simple payback | 10.4 years | 10.3 years |

**Three-tier NPV (200 kWh / 400 kWh):**

| Tier | What it includes | 200 kWh | 400 kWh | Realistic? |
|------|-----------------|:---:|:---:|------------|
| **Tier 1: Arbitrage only** | Revenue − costs | **-A\$29,969** | **-A\$45,296** | Most realistic for market participants |
| Tier 2: + augmentation | + deferred transformer (A\$21,095 PV) | -A\$8,874 | -A\$24,201 | Requires DNSP contract for specific project |
| Tier 3: + aug + LRMC | + export saving (A\$12,641 PV) | +A\$3,767 | -A\$11,560 | Theoretical maximum, unlikely in practice |

**Tier 1 is the most realistic** for a market participant or community group. The operator earns arbitrage revenue and pays battery costs — no DNSP payments are involved.

**Tier 2** requires Evoenergy to enter a network support agreement paying the operator for deferring a specific transformer upgrade. This is technically possible under the NER's non-network alternatives framework but has not been implemented for community batteries in the ACT.

**Tier 3** further assumes Evoenergy pays the operator for reducing solar export flows, valued at the system-wide LRMC of export services. This is the most abstract — the A\$23/kW/year LRMC is an aggregate figure derived from Evoenergy's network-wide average incremental cost methodology, not from a specific avoided project on this feeder. A practical DNSP contract would more likely reference a specific avoided project (Tier 2) than a system-wide average cost.

Under spot prices, the 200 kWh battery only turns positive at Tier 3 — requiring the DNSP to pay for both the specific transformer deferral and the system-wide export LRMC saving. This is a fragile result.

### Model B: Retail TOU Arbitrage (±80kW dispatch, RL network-safe)

| Metric | 200 kWh | 400 kWh |
|--------|---------|---------|
| Capital cost | A\$116,000 | A\$162,400 |
| Year 1 revenue | A\$28,840 | A\$51,838 |
| Year 1 net cash flow | A\$27,100 | A\$49,402 |
| Year 12 replacement cost | A\$39,000 | A\$67,200 |
| Simple payback | **4.3 years** | **3.3 years** |

**Three-tier NPV (200 kWh / 400 kWh):**

| Tier | What it includes | 200 kWh | 400 kWh | Realistic? |
|------|-----------------|:---:|:---:|------------|
| **Tier 1: Arbitrage only** | Revenue − costs | **+A\$135,533** | **+A\$298,675** | Most realistic for community groups |
| Tier 2: + augmentation | + deferred transformer (A\$21,095 PV) | +A\$156,627 | +A\$319,770 | Bonus if DNSP contract exists |
| Tier 3: + aug + LRMC | + export saving (A\$12,641 PV) | +A\$169,269 | +A\$332,411 | Theoretical maximum |

Under TOU retail arbitrage, **all three tiers are strongly positive**. The battery is viable from pure arbitrage revenue (Tier 1) without any DNSP payment. DNSP network benefits are a bonus that improves an already strong investment case.

### Cross-Model Comparison (±80kW / 200kWh, Tier 1 — Arbitrage Only)

| Metric | Model A (Spot) | Model B (TOU) | TOU Advantage |
|--------|:---:|:---:|:---:|
| Daily RL revenue | A\$34.44 | A\$80.57 | +A\$46.13 (2.3×) |
| Year 1 net cash flow | A\$10,579 | A\$27,100 | +A\$16,521 |
| Simple payback | 10.4 years | 4.3 years | -6.1 years |
| NPV (20 years) | -A\$29,969 | +A\$135,533 | +A\$165,502 |
| Viable at Tier 1? | No | **Yes** | — |
| Viable at Tier 2? | No (-A\$8,874) | Yes (+A\$156,627) | — |
| Viable at Tier 3? | Marginal (+A\$3,767) | Yes (+A\$169,269) | — |

### Cash Flow Profile (200 kWh, Model A)

The 200 kWh battery's cash flow illustrates the capacity fade reset at module replacement:

| Year | Capacity | Annual Revenue | O&M | Replacement | Net CF |
|------|:---:|:---:|:---:|:---:|:---:|
| 0 | — | — | — | — | -A\$116,000 |
| 1 | 98% | A\$12,319 | -A\$1,740 | — | A\$10,579 |
| 5 | 90% | A\$11,314 | -A\$1,740 | — | A\$9,574 |
| 10 | 80% | A\$10,056 | -A\$1,740 | — | A\$8,316 |
| 12 | 76% | A\$9,554 | -A\$1,740 | -A\$39,000 | -A\$31,186 |
| 13 | 98% (reset) | A\$12,319 | -A\$1,740 | — | A\$10,579 |
| 15 | 94% | A\$11,816 | -A\$1,740 | — | A\$10,076 |
| 20 | 84% | A\$10,559 | -A\$1,740 | — | A\$8,819 |

Export LRMC saving (A\$1,150/yr) is excluded from the operator's cash flow — it is a DNSP benefit.

### Key Result

Under Model A (spot), the 200 kWh battery achieves marginal viability only if the DNSP pays an augmentation deferral credit — a payment that the market participant would not automatically receive. Under Model B (TOU), the same battery is strongly viable from pure retail arbitrage revenue (NPV +A\$148,174) without any DNSP payment. The business model choice — not battery sizing, dispatch algorithm, or network constraints — is the primary determinant of investment viability.

## Sensitivity and Assumptions

### Revenue Assumption: Single-Day vs Full-Year

The daily revenue (A\$34.44) is based on one typical price day with a spread of A\$244/MWh (from -A\$14 midday to A\$230 morning peak). This is the largest source of uncertainty in the model.

A full year of NEM prices includes low-spread days (A\$10–15/day revenue), typical days (A\$25–35/day), and occasional spike days (A\$100–500/day). The annual average is likely lower than our typical day:

| Revenue scenario | Daily average | Annual | NPV impact (200 kWh, spot) |
|-----------------|:---:|:---:|:---:|
| Conservative (full-year avg) | A\$25/day | A\$8,942 | ~-A\$43,000 |
| Base (our typical day) | A\$34.44/day | A\$12,319 | -A\$29,969 |
| Optimistic (incl. spike days) | A\$40/day | A\$14,332 | ~-A\$23,000 |

The spot model NPV is negative across all reasonable revenue scenarios. The TOU model (A\$80.57/day, fixed) is not subject to this uncertainty — the revenue is determined by the published retail tariff schedule.

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
| Daily revenue (single day) | Overstated for spot | -A\$20,000 to -A\$35,000 |
| TOU revenue (fixed tariff) | Accurate | Neutral |
| Export LRMC | Excluded from operator NPV | Neutral (DNSP benefit) |
| Avoided augmentation | Excluded from operator NPV | Neutral (DNSP benefit) |
| Module replacement timing | Conservative | +A\$0 to +A\$18,000 |
| O&M rate | Uncertain | -A\$5,000 to +A\$5,000 |
| Capital cost | About right | Neutral |

For the spot model, the revenue assumption is the dominant risk. For the TOU model, the risk is primarily in whether the tariff structure is maintained by ActewAGL and Evoenergy over the 20-year project life.

## Conclusions

**1. The business model is the dominant investment variable.** The TOU retail arbitrage model (Model B) transforms the 200 kWh battery from marginally viable (spot NPV -A\$17,328) to strongly profitable (TOU NPV +A\$148,174). This effect exceeds the impact of doubling battery capacity, changing the dispatch algorithm, or adding DNSP augmentation credits.

**2. Spot arbitrage alone does not justify the investment.** Under Model A, neither the 200 kWh nor the 400 kWh battery achieves positive NPV from arbitrage revenue. The 200 kWh battery requires a DNSP network support payment (augmentation deferral credit) for marginal viability (+A\$3,767), but a market participant would not automatically receive this payment.

**3. TOU arbitrage is viable without DNSP support.** Under Model B, both batteries are strongly viable from retail bill savings alone. Simple payback is 4.1 years (200 kWh) and 3.2 years (400 kWh). Augmentation deferral credits are a bonus, not a requirement.

**4. Avoided augmentation is a DNSP benefit, not an operator benefit.** The A\$23,905 augmentation deferral PV accrues to Evoenergy (avoided transformer upgrade), not to the battery operator. Models A and B should be evaluated on arbitrage revenue only. The augmentation value could flow to the operator through a DNSP network support contract, but this requires a regulatory framework that does not yet exist for community batteries in the ACT.

**5. The 200 kWh battery has a better business case than 400 kWh under spot, but 400 kWh dominates under TOU.** Under spot, the 200 kWh battery's lower capital and replacement costs outweigh its lower revenue. Under TOU, the 400 kWh battery's additional revenue (A\$144.82 vs A\$80.57 per day) more than justifies the extra cost, achieving NPV of +A\$311,316 versus +A\$148,174.

**6. Additional revenue streams remain important for spot-only operators.** FCAS participation (est. A\$3,000–5,000/year) or DNSP network support payments (est. A\$5,000–10,000/year) would push the spot NPV positive. These are essential for Model A viability but optional for Model B.

**7. Falling battery costs will improve both models.** GenCost projects 2hr battery costs declining from A\$580/kWh (2025) to A\$306/kWh (2035) under current policies. The spot model reaches viability at approximately A\$400/kWh (2028–2030). The TOU model is already viable at current costs.