# NPV Analysis: Community Battery Investment

## Model

The net present value of a community battery investment over $Y$ years is:

$$NPV = -C_0 + \sum_{y=1}^{Y} \frac{R_y + S_y - M_y}{(1+r)^y} - \frac{C_{\text{repl}}}{(1+r)^{y_r}} + PV_{\text{aug}}$$

where the annual revenue accounts for capacity fade with reset at module replacement:

$$R_y = 365 \cdot p_{\text{daily}} \cdot f(y), \quad f(y) = \max\left(0.7, \; 1 - \delta \cdot \begin{cases} y & \text{if } y \leq y_r \\\\ y - y_r & \text{if } y > y_r \end{cases}\right)$$

| Symbol | Meaning | Value | Source |
|--------|---------|-------|--------|
| $C_0$ | Initial capital cost | $E \times c_{\text{kWh}}$ | GenCost 2025 |
| $Y$ | Project lifetime | 20 years | Industry standard |
| $r$ | Discount rate | 6.53% | AER RORI 2025 |
| $p_{\text{daily}}$ | Daily RL revenue at full capacity | A\$34.44 (200kWh) / A\$48.93 (400kWh) | Q-learning results |
| $f(y)$ | Capacity fade factor | Resets to 1.0 at replacement | Linear 2%/year |
| $\delta$ | Annual fade rate | 0.02 | Industry estimate |
| $y_r$ | Module replacement year | 12 | 70% capacity threshold |
| $S_y$ | Export LRMC saving | $P_{\text{absorb}} \times c_{\text{LRMC}}$ = A\$1,150/yr | Evoenergy TSS 2024 |
| $M_y$ | O&M cost | $\mu \times C_0$ (1.5% of capital) | Industry estimate |
| $C_{\text{repl}}$ | Module replacement cost | $E \times c_{\text{module,2037}}$ | GenCost projected |
| $PV_{\text{aug}}$ | Avoided augmentation PV | $C_{\text{aug}} \times (1 - \frac{1}{(1+r)^{n_d}})$ | Evoenergy estimate |

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

| Parameter | Value | Source |
|-----------|-------|--------|
| Daily RL revenue ±80kW / 200kWh | A\$34.44 | Q-learning (0 violations) |
| Daily RL revenue ±80kW / 400kWh | A\$48.93 | Q-learning (0 violations) |
| Export absorption power | 50 kW | Midday solar charge |
| LRMC export rate | A\$23/kW/year | Evoenergy TSS 2024 |
| Avoided augmentation cost | A\$45,000 | Transformer upgrade estimate |
| Augmentation deferral period | 10 years | Assumption |
| O&M rate | 1.5% of capital/year | Industry estimate |
| Discount rate | 6.53% | AER RORI 2025 update |

## Results

### NPV Summary (±80kW dispatch, RL network-safe)

| Metric | 200 kWh | 400 kWh |
|--------|---------|---------|
| Capital cost | A\$116,000 | A\$162,400 |
| Year 1 revenue | A\$12,319 | A\$17,502 |
| Year 1 net cash flow | A\$11,729 | A\$16,216 |
| Year 12 replacement cost | A\$39,000 | A\$67,200 |
| Simple payback | 9.4 years | 9.3 years |
| **NPV (20 years)** | **-A\$17,328** | **-A\$32,655** |
| Avoided augmentation PV | A\$21,095 | A\$21,095 |
| **NPV + augmentation** | **+A\$3,767** | **-A\$11,560** |

### Cash Flow Profile (200 kWh)

The 200 kWh battery's cash flow illustrates the capacity fade reset at module replacement:

| Year | Capacity | Annual Revenue | O&M | Replacement | Net CF |
|------|:---:|:---:|:---:|:---:|:---:|
| 0 | — | — | — | — | -A\$116,000 |
| 1 | 98% | A\$12,319 | -A\$1,740 | — | A\$11,729 |
| 5 | 90% | A\$11,314 | -A\$1,740 | — | A\$10,724 |
| 10 | 80% | A\$10,056 | -A\$1,740 | — | A\$9,466 |
| 12 | 76% | A\$9,554 | -A\$1,740 | -A\$39,000 | -A\$30,036 |
| 13 | 98% (reset) | A\$12,319 | -A\$1,740 | — | A\$11,729 |
| 15 | 94% | A\$11,816 | -A\$1,740 | — | A\$11,226 |
| 20 | 84% | A\$10,559 | -A\$1,740 | — | A\$9,969 |

### Key Result

The 200 kWh battery achieves a marginally positive NPV (+A\$3,767) when including avoided network augmentation. The 400 kWh battery remains negative (-A\$11,560) despite higher revenue because the module replacement cost (A\$67,200 vs A\$39,000) and higher capital cost outweigh the revenue gain.

## Sensitivity and Assumptions

### Revenue Assumption: Single-Day vs Full-Year

The daily revenue (A\$34.44) is based on one typical price day with a spread of A\$244/MWh (from -A\$14 midday to A\$230 morning peak). This is the largest source of uncertainty in the model.

A full year of NEM prices includes low-spread days (A\$10–15/day revenue), typical days (A\$25–35/day), and occasional spike days (A\$100–500/day). The annual average is likely lower than our typical day:

| Revenue scenario | Daily average | Annual | NPV impact (200 kWh) |
|-----------------|:---:|:---:|:---:|
| Conservative (full-year avg) | A\$25/day | A\$8,942 | ~-A\$30,000 |
| Base (our typical day) | A\$34.44/day | A\$12,319 | -A\$17,328 |
| Optimistic (incl. spike days) | A\$40/day | A\$14,332 | ~-A\$10,000 |

The positive NPV (+A\$3,767) has a thin margin that would likely disappear with full-year price data. A full-year simulation running the DP and RL across 365 days of AEMO prices would resolve this uncertainty.

### Export LRMC Saving: Likely Overstated

The A\$1,150/year assumes 50 kW solar absorption every day. In reality, winter days have less solar (20–30 kW), cloudy days reduce output, and the battery may not always charge at midday. A more realistic average of 30–35 kW gives A\$690–805/year.

| Export absorption | Annual saving | NPV impact over 20 years |
|:---:|:---:|:---:|
| 50 kW (our estimate) | A\$1,150 | Baseline |
| 35 kW (conservative) | A\$805 | ~-A\$3,500 |
| 25 kW (pessimistic) | A\$575 | ~-A\$5,800 |

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

| Component | Direction of bias | NPV impact |
|-----------|------------------|:---:|
| Daily revenue (single day) | Overstated | -A\$20,000 to -A\$35,000 |
| Export LRMC (daily absorption) | Overstated | -A\$3,000 to -A\$6,000 |
| Avoided augmentation | Highly uncertain | -A\$13,000 to +A\$26,000 |
| Module replacement timing | Conservative | +A\$0 to +A\$18,000 |
| O&M rate | Uncertain | -A\$5,000 to +A\$5,000 |
| Capital cost | About right | Neutral |

The revenue assumption is the dominant risk. A full-year price simulation would reduce this uncertainty and is the most important model refinement.

## Conclusions

**1. Arbitrage alone does not justify the investment at current battery costs.** The 200 kWh NPV on arbitrage revenue alone is -A\$17,328 over 20 years. The battery generates substantial revenue (A\$12,319/year in year 1) but not enough to recover the A\$116,000 capital cost plus A\$39,000 module replacement at year 12.

**2. Including avoided augmentation makes the 200 kWh battery marginally viable.** NPV + augmentation = +A\$3,767. However, this margin is fragile — it assumes a specific augmentation cost (A\$45,000), deferral period (10 years), and optimistic daily revenue.

**3. The 200 kWh battery has a better business case than 400 kWh.** Despite earning less daily revenue (A\$34 vs A\$49), the 200 kWh battery has lower capital cost (A\$116,000 vs A\$162,400) and lower replacement cost (A\$39,000 vs A\$67,200). Both achieve 0 violations with RL dispatch, so the extra capacity provides no network benefit — only additional arbitrage revenue that doesn't justify the cost.

**4. Additional revenue streams would close the gap.** FCAS participation (est. A\$3,000–5,000/year) or DNSP network support payments (est. A\$5,000–10,000/year) would push the NPV firmly positive. These revenue streams are technically available but not yet standardised for community batteries in Australian regulatory frameworks.

**5. Falling battery costs will improve the business case.** GenCost projects 2hr battery costs declining from A\$580/kWh (2025) to A\$306/kWh (2035) under current policies. At A\$400/kWh break-even (reached ~2028–2030), the battery becomes viable on arbitrage plus augmentation deferral without additional revenue streams.