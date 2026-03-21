# Policy Implications

## Summary of Evidence Base

This document draws on the project's full evidence base: 9 battery configurations tested on a single typical day (June 28), 366-day annual dispatch analysis using PyPSA LP and DP solvers, 5 representative days with full DP + RL training, NPV analysis under four revenue scenarios, and comparison of wholesale spot (Model A) vs retail TOU (Model B) business models. The configuration used for annual analysis is ±100 kW / 200 kWh unless stated otherwise.

---

## For Distribution Network Service Providers

### Dispatch limits should be set at ±50–80 kW for this feeder class

Below ±40 kW, the cable impedance physically prevents sufficient voltage correction regardless of battery capacity or dispatch algorithm. Above ±80 kW, higher dispatch power is feasible with RL but less efficient — the revenue gap to DP widens (up to 14%) and losses increase. The DNSP should specify the dispatch limit in the battery's connection agreement based on the feeder's cable impedance and voltage deficit.

### Network-aware dispatch should be a connection requirement

Revenue-maximising dispatch (DP or PyPSA) causes voltage violations on every single day of the year. The 366-day annual analysis found 3,021 violations under DP and 3,242 under PyPSA across the full year — an average of 8.3–8.9 violations per day. No day in 2024 was violation-free under unconstrained dispatch. If the DNSP permits unconstrained arbitrage, the battery degrades voltage quality for all customers on the feeder every day.

Requiring network-aware dispatch (as the RL agent demonstrates) eliminates all violations at a revenue cost of A$1,239/year — 3.2% of DP annual revenue. On representative days, the cost ranges from 0.7% on spike days to 7% on typical days. This is a reasonable trade for grid safety.

### Violations concentrate in evening peak and are worst on low-revenue days

The 366-day heatmap shows violations cluster between 17:00–21:00 (periods 34–42) when household demand peaks and the battery discharges aggressively. Low-revenue days actually have more violations per day (10.7) than high-revenue days (7.9) because the battery exhausts its stored energy faster on small spreads, hitting SoC limits and causing sustained high-power discharge that pushes voltages beyond limits.

This means DNSPs cannot assume that mild price days are safe for unconstrained dispatch. The opposite is true: low-spread days have the highest violation density.

### A single battery can protect the entire feeder, not just its own branch

The branch comparison shows that a battery on Branch A eliminates all 11 violations on both branches through junction voltage rise. The DNSP does not need one battery per branch. However, the spillover margin is thin (B4 sits only 0.1–0.2% above the 0.94 pu limit), so placement decisions should account for the worst-case bus on the opposite branch, not just the battery's own branch.

### RL dispatch reduces network losses by at least 4–14%

The oscillating evening strategy uses lower sustained current than DP's aggressive dispatch, reducing I²R losses. At ±100 kW / 400 kWh, RL saves 13.6 kWh/day in losses compared to DP. These figures are a lower bound from the current action/SoC grid resolution (33 actions, 81 SoC levels); finer discretisation for higher-capacity configurations would likely yield larger loss reductions through smoother dispatch profiles. The DNSP benefits from both fewer violations and lower loss costs. Under current tariff structures, these loss savings are not compensated to the battery operator — creating a positive externality that network tariff reform could internalise.

---

## For Battery Operators and Developers

### Smart dispatch substitutes for battery capacity

Without network-aware dispatch, DP requires ±50 kW / 400 kWh to achieve zero violations — a larger battery that avoids violations simply because it never needs to discharge aggressively enough to push voltages out of range. With RL's network-aware dispatch, ±50 kW / 200 kWh achieves the same zero violations by actively managing dispatch timing and power levels.

The practical implication for developers: RL-based dispatch control lets you deploy a 200 kWh battery (A$116,000 under GenCost 2025) instead of a 400 kWh battery (A$162,400) while meeting the same network obligations. The A$46,400 capital saving exceeds the revenue difference between the two sizes. The 200 kWh RL configuration earns 70–88% of the 200 kWh DP revenue, but at half the capital cost of the DP-safe 400 kWh configuration.

### The ±80 kW / 400 kWh configuration offers the best single-day revenue-feasibility trade-off

It achieves zero violations with RL revenue of A$48.93/day — only A$0.43/day (less than 1%) below the DP revenue. Among all tested configurations, this one maximises revenue while maintaining full network feasibility.

### Annual revenue is dominated by rare spike days

The 366-day analysis reveals extreme revenue concentration: 10 spike days (2.7% of the year) contribute A$15,772 — 42% of estimated annual RL revenue. An operator planning a wholesale spot business case must decide how to treat spike revenue.

The four NPV scenarios illustrate the range (±100 kW / 200 kWh, Tier 1 costs):

| Scenario | Annual Revenue | NPV | Payback |
|----------|------:|------:|------:|
| Spot — top line (incl all spikes) | A$37,422 | +A$214,013 | 3.3 yr |
| TOU — guaranteed daily | A$29,790 | +A$139,083 | 3.9 yr |
| Spot — bottom line (excl top 20 spikes) | A$13,303 | −A$22,779 | 10.0 yr |
| Spot — single typical day × 365 | A$13,249 | −A$23,268 | 8.9 yr |

The top-line spot NPV assumes 2024's spike pattern recurs every year. The bottom-line excludes the 20 most volatile days and represents stable, repeatable revenue. The gap between these two — A$237,000 in NPV — is the value of spike days, and it is not bankable.

### The revenue cost of network safety is predictable and small

Across all configurations, the RL revenue gap follows a consistent pattern: the gap decreases with battery capacity and increases with dispatch limit. On representative days:

| Price regime | DP Revenue | RL Revenue | Safety cost |
|---|------:|------:|------:|
| Low (51 days/yr) | A$9.57 | A$5.70 | 40.4% |
| Typical (227 days/yr) | A$32.87 | A$30.59 | 7.0% |
| High (52 days/yr) | A$69.24 | A$66.04 | 4.6% |
| Very high (26 days/yr) | A$279.90 | A$276.66 | 1.2% |
| Spike (10 days/yr) | A$1,588.45 | A$1,577.25 | 0.7% |

The absolute cost is A$2–11/day regardless of price level. The percentage cost drops sharply as revenue increases because the voltage constraint bites at the same physical limit every day, while revenue scales with prices. On spike days — the days that matter most for annual revenue — the constraint cost is negligible.

---

## For Energy Policy and Regulation

### The TOU business model dominates spot on a risk-adjusted basis

The full-year analysis provides the clearest comparison between the two business models:

| Metric | Spot (Model A) | TOU (Model B) |
|--------|------:|------:|
| Daily revenue (median) | A$31 | A$82 |
| Daily revenue (mean) | A$99 | A$82 |
| Annual total | A$36,190 (PyPSA) | A$29,790 |
| Revenue variance | σ = A$388/day | Zero |
| Revenue if top 10 spikes don't recur | A$16,573 | A$29,790 |
| NPV (Tier 1, 200 kWh) | −A$23,268 to +A$214,013 | +A$139,083 |

On a typical day, TOU earns 2.6× more than spot. Spot's annual total exceeds TOU only because of 10 spike days. A battery operator choosing spot over TOU is betting A$16,000/year of guaranteed revenue against the chance of earning A$20,000+ from spike days. In 2024, this bet paid off. In a mild year with fewer spikes, it would not.

For lenders and project financiers, TOU's zero-variance revenue stream is substantially more bankable. The TOU spread (A$281/MWh between solar soak and peak under ActewAGL's Home Daytime Economy tariff) is guaranteed by the published retail tariff, while the spot spread varies 50× day to day.

### Community batteries provide network services that are currently uncompensated

The battery eliminates 3,000+ voltage violations per year and reduces losses by at least 4–14%, but the operator captures only arbitrage revenue. The DNSP and all feeder customers benefit from improved voltage quality and lower losses without paying for it.

The quantified annual value of these services:

- Voltage violation elimination: 3,021 violations/year removed (DP baseline), enabling AS 61000.3.100 compliance across the entire feeder
- Loss reduction: at least 4–14% of I²R losses (lower bound from current grid resolution), worth approximately A$500–2,000/year at current network tariffs
- Hosting capacity uplift: the battery enables additional rooftop solar connection without voltage violations

Regulatory frameworks should recognise and compensate this voltage support service — either through network support agreements, dynamic export tariffs, or inclusion of community batteries in the regulated asset base.

### The hybrid spot + TOU strategy deserves regulatory attention

The business models document identifies a potential hybrid approach: earn TOU arbitrage on guaranteed daily spreads, then bid into the spot market during extreme price events. This would capture the TOU floor (A$29,790/year) plus a portion of spike revenue. However, this requires either a retailer willing to offer a TOU-spot hybrid contract, or regulatory arrangements that allow the battery to switch between behind-the-meter and wholesale market participation.

Current NEM rules and connection agreements do not cleanly support this dual-mode operation. The Australian Energy Market Commission should consider whether community battery connection frameworks need updating to enable hybrid business models that maximise both private revenue and network value.

### The oscillating dispatch strategy has implications for battery degradation policy

The RL agent's rapid charge/discharge cycling during evening peak (±6 to ±44 kW oscillations over 5–10 periods) increases throughput compared to DP's sustained discharge. While the degradation cost model (A$0.02/kWh) captures average wear, rapid partial cycling may affect battery lifetime differently than deep cycles.

Battery warranty terms and connection agreements should be evaluated against this dispatch pattern. More physically detailed degradation modelling (rain-flow counting on the SoC trajectory) is needed to quantify the impact. If oscillating dispatch significantly accelerates degradation, the network-safe revenue would need to be reduced by the additional wear cost — narrowing the gap between RL and TOU further.

### Reinforcement learning provides a practical tool for connection assessment

Currently, DNSPs assess battery connection applications using static hosting capacity analysis. The DP + RL framework offers a more informative approach:

1. **DP** finds the revenue upper bound (unconstrained dispatch)
2. **OpenDSS** identifies where and when violations occur
3. **RL** finds the network-feasible dispatch that maximises revenue subject to voltage limits
4. The gap between DP and RL quantifies the constraint cost

This information supports both the DNSP (what dispatch limit to impose) and the battery operator (what revenue to expect) in negotiating connection terms. The representative day methodology — testing across low, typical, high, very high, and spike price regimes — ensures the assessment covers the full range of operating conditions.

### Price volatility risk should inform battery storage policy design

The 366-day analysis demonstrates that NEM spot price volatility creates a fundamental challenge for community battery investment. The key statistics:

- 54% of annual PyPSA revenue comes from 10 days
- The median daily spot revenue (A$31) is 2.6× lower than the mean (A$99)
- Spot revenue varies 50× between the worst and best days

This volatility argues for policy mechanisms that reduce revenue risk for battery operators: contracts for difference that guarantee a floor revenue, capacity payments that compensate availability rather than dispatch, or regulated returns through the RAB that de-risk investment entirely.

Without such mechanisms, rational investors will either demand higher returns (increasing the cost of community battery deployment) or choose TOU business models that bypass wholesale market risk entirely — potentially missing the network services that only spot-market-dispatched batteries can provide during system stress events.

---

## Future Research Directions

The following extensions would strengthen the policy evidence base:

- **Stochastic DP** with price uncertainty: quantify the value of perfect information and the cost of forecast errors
- **Multi-year revenue analysis** across 2020–2024 to assess year-to-year spike frequency variability
- **Detailed degradation modelling** (rain-flow counting) to test whether RL oscillation accelerates wear beyond the A$0.02/kWh assumption
- **Multiple feeder archetypes** to generalise the violation density and constraint cost findings beyond this single 32-house feeder
- **FCAS revenue stacking** to quantify additional revenue from frequency control services during the periods when the battery is otherwise idle
- **Co-optimisation** embedding power flow equations directly in the DP state space (state = SoC × voltage) for a theoretically clean network-constrained optimisation