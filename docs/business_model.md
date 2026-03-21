# Business Models for Community Battery Operation

## Overview

A community battery's revenue depends on the **price signal** it responds to. This project evaluates two business models that represent the two main commercial frameworks for community batteries in Australia:

| | Model A: Wholesale Spot | Model B: Retail TOU |
|---|---|---|
| **Owner** | Market participant (retailer, aggregator, or DNSP) | Community group, body corporate, or third-party operator |
| **Registration** | Registered with AEMO as a market participant | Not registered with AEMO — operates behind the meter |
| **Price signal** | NEM spot price (changes every 5 minutes) | Retail TOU tariff (fixed, published annually by retailer) |
| **Revenue type** | Cash settlement with AEMO | Bill reduction for participating households |
| **Network tariff** | Pays separate network tariff to DNSP (Evoenergy) | Bundled in retail rate — no separate network payment |
| **Risk profile** | High revenue variance, spike-dependent | Zero variance, guaranteed daily revenue |

Both models use the same battery hardware, the same feeder, and the same DP/RL optimisation framework. Only the 48-element price vector changes.

---

## Model A: Wholesale Spot Arbitrage

### How It Works

The battery operator is registered as a NEM market participant. The battery buys electricity from the wholesale market when spot prices are low (typically midday during solar surplus) and sells when spot prices are high (morning and evening peaks). Revenue is the difference between selling price and buying price, minus efficiency losses and degradation.

```
Midday: spot = A$-14/MWh → battery charges (gets PAID to absorb power)
Evening: spot = A$230/MWh → battery discharges (sells at high price)
Revenue = (sell price − buy price) × energy − efficiency loss − degradation
```

### Price Signal

NEM spot prices for the ACT region (NSW1) are downloaded from AEMO's public data portal. Prices are recorded at 5-minute dispatch intervals and resampled to 30-minute settlement periods (the NEM settlement interval).

Price characteristics (calendar year 2024, 366 days):

| Statistic | Value |
|-----------|-------|
| Mean price | A\$96/MWh |
| Median price | A\$72/MWh |
| Range | -A\$100 to A\$17,500/MWh |
| Days with negative prices | ~20–30% of days (midday solar surplus) |
| Spike days (max > A\$5,000/MWh) | ~10/year |

The price is volatile and different every day. The optimal dispatch changes daily because the timing and magnitude of price peaks depend on weather, demand, generator availability, and renewable output.

### Revenue Characteristics

From the full-year PyPSA analysis (±100kW / 200kWh):

| Metric | Value |
|--------|------:|
| Annual total | A\$36,190 (PyPSA), A\$37,422 (RL estimated) |
| Mean daily | A\$98.88 |
| Median daily | A\$31.17 |
| P10 (pessimistic day) | A\$7.34 |
| P90 (good day) | A\$94.43 |
| Spike day contribution | 44% of annual from top 10 days |

The distribution is heavily right-skewed: most days earn A\$10–50, but 10 spike days contribute nearly half the annual revenue. Removing the top 10 spike days reduces annual revenue from A\$36,190 to A\$16,573.

### Who Uses This Model

In Australia, Model A is typically operated by electricity retailers (e.g., Origin Energy's virtual power plant), aggregators (e.g., Reposit Power), or DNSPs with an unregulated subsidiary. The operator needs AEMO market registration, a trading desk or automated bidding system, and exposure to wholesale price risk.

---

## Model B: Retail TOU Arbitrage

### How It Works

The battery sits behind the meter of participating households and responds to the retail time-of-use tariff. It charges during the cheapest period (solar soak, 11am–3pm) and discharges during the most expensive periods (peaks, 7am–9am and 5pm–9pm). The "revenue" is the reduction in participants' electricity bills — they avoid buying expensive peak electricity by using stored solar soak energy.

```
Solar soak (11am–3pm): retail = 16.00 c/kWh → battery charges
Peak (5pm–9pm):        retail = 44.07 c/kWh → battery discharges
Saving = (peak rate − solar soak rate) × energy − efficiency loss − degradation
```

No electricity is traded with AEMO. The battery simply shifts energy consumption from expensive periods to cheap periods on the retail bill.

### Price Signal

The ActewAGL Home Daytime Economy tariff (from 1 July 2025, GST exclusive) defines three fixed price tiers:

| Period | Time (AEST) | Rate (c/kWh) | A\$/MWh | Half-hours |
|--------|-------------|:---:|:---:|:---:|
| Solar soak | 11am–3pm | 16.00 | 160 | 8 |
| Shoulder | 9pm–7am, 9am–11am, 3pm–5pm | 29.00 | 290 | 28 |
| Peak | 7am–9am, 5pm–9pm | 44.07 | 441 | 12 |

This tariff aligns with Evoenergy's proposed residential TOU network tariff (Code 017) under the Revised Tariff Structure Statement for the 2024–29 regulatory period. The tariff structure is designed to encourage load shifting away from peak periods — exactly what a community battery does.

The spread between solar soak and peak is A\$281/MWh (A\$441 − A\$160). This spread is wider than the typical spot day spread (median A\$213/MWh) and is **guaranteed every day** by the published tariff schedule.

### Revenue Characteristics

The TOU dispatch is the same every day because the tariff structure is fixed:

| Metric | Value |
|--------|------:|
| Daily revenue (RL, ±100kW/200kWh) | A\$81.56 |
| Annual revenue | A\$29,790 |
| Revenue variance | Zero |
| Predictability | Perfect — published tariff |

### Why the TOU Spread Is Wider Than Typical Spot

The retail peak rate (44.07 c/kWh = A\$441/MWh) is much higher than the typical wholesale spot peak (A\$100–300/MWh on a normal day) because it bundles wholesale energy cost, network charges (Evoenergy distribution + TransGrid transmission), retail margin, hedging costs, green certificate costs, and GST-exclusive regulatory levies.

The solar soak rate (16.00 c/kWh = A\$160/MWh) is set as the lowest retail tier to encourage midday consumption during solar surplus. Under spot pricing, midday prices can drop below zero (the battery gets **paid** to charge), but this only occurs on 20–30% of days. The TOU solar soak rate provides a floor — the battery always pays A\$160/MWh to charge, but the spread to peak is guaranteed.

### Who Uses This Model

Model B is used by community battery operators who are not AEMO market participants. Examples include community energy cooperatives (e.g., Yackandandah Community Energy), body corporate batteries in apartment buildings, and third-party operators who lease battery capacity to households. The operator needs an agreement with participating households, a retail electricity account with ActewAGL (or equivalent retailer), and a battery management system that can follow the TOU schedule.

---

## Comparison

### Revenue

| Metric | Model A (Spot) | Model B (TOU) |
|--------|------:|------:|
| Daily revenue — median day | A\$31 | A\$82 |
| Daily revenue — spike day | A\$1,500+ | A\$82 |
| Annual revenue (RL, network-safe) | A\$37,422 | A\$29,790 |
| Annual excl. top 10 spike days | ~A\$16,600 | A\$29,790 |
| Revenue variance | Very high (σ ≈ A\$380/day) | Zero |

Spot has higher expected annual revenue (A\$37,422 vs A\$29,790), but 44% of that depends on 10 unpredictable spike days. On the median day, TOU earns 2.6× more than spot (A\$82 vs A\$31).

### Risk

| Factor | Model A (Spot) | Model B (TOU) |
|--------|---|---|
| Price risk | Exposed to NEM volatility | None — fixed tariff |
| Spike dependence | 44% of annual revenue from 10 days | None |
| Regulatory risk | NEM rule changes can affect bidding | Tariff changes at annual review |
| Revenue floor (P10 day) | A\$7.34 | A\$81.56 |
| Bankability | Difficult — lenders can't underwrite volatile revenue | Strong — predictable cash flow |

### NPV (±100kW / 200kWh, Tier 1 — Arbitrage Only)

| | Model A (Spot) | Model B (TOU) |
|---|:---:|:---:|
| Capital cost | A\$116,000 | A\$116,000 |
| Annual revenue | A\$37,422 (incl. spikes) | A\$29,790 |
| NPV (20yr, 6.53%) | Depends on spike assumptions | **+A\$139,083** |
| Simple payback | ~3.1 yr (with spikes), ~8.7 yr (without) | 3.9 yr |

Under TOU, the NPV is strongly positive with no dependence on market conditions. Under spot, the NPV can be positive but requires spike days to recur annually.

### Which Model Is Better?

**For investment decisions: TOU.** The guaranteed daily revenue makes TOU the bankable choice. A community group raising funds for a battery can present a credible financial case to lenders.

**For maximum expected revenue: Spot.** If the operator can tolerate revenue volatility and has AEMO market access, spot provides higher expected returns — but with significant downside risk in years with fewer spike events.

**Optimal strategy: Hybrid.** The strongest position may be a dual-registered battery that earns TOU revenue as its baseline and switches to spot market bidding during declared price spike events (VoLL or administered pricing periods). This captures the TOU stability with spike upside. Implementing this requires both AEMO registration and retail meter arrangements — a more complex setup but potentially the highest risk-adjusted return.

---

## Implementation in This Project

Both models are implemented using the same codebase. The only difference is the price vector:

```python
from src.dp.prices import load_day_prices, build_tou_profile

# Model A: load real spot prices (different every day)
prices_spot = load_day_prices('data/aemo/prices_typical_2024-06-28.csv')

# Model B: construct TOU profile (same every day)
prices_tou = build_tou_profile()
```

The DP solver, Q-learning agent, OpenDSS network model, and NPV calculations are identical across models. This separation of price signal from optimisation algorithm is a deliberate design choice — it allows direct comparison of business models with all other factors held constant.

For dispatch profile comparisons between spot and TOU, see [docs/spot vs tou dispatch comparison.md](docs/spot%20vs%20tou%20dispatch%20comparison.md).

For NPV details, see [docs/npv_analysis.md](docs/npv_analysis.md).

For full-year revenue analysis, see [docs/full_year_dispatch_analysis.md](docs/full_year_dispatch_analysis.md).