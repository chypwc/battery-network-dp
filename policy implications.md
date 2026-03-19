## Policy Implications

### For Distribution Network Service Providers

**Dispatch limits should be set at ±50–80 kW for this feeder class.** Below ±40 kW, the cable impedance physically prevents sufficient voltage correction regardless of battery capacity or dispatch algorithm. Above ±80 kW, higher dispatch power is feasible with RL but less efficient — the revenue gap to DP widens (up to 14%) and losses increase. The DNSP should specify the dispatch limit in the battery's connection agreement based on the feeder's cable impedance and voltage deficit.

**Network-aware dispatch should be a connection requirement.** Revenue-maximising DP dispatch causes 3–10 violations across most configurations. If the DNSP permits unconstrained arbitrage, the battery degrades voltage quality for all customers on the feeder. Requiring network-aware dispatch (as the RL agent demonstrates) eliminates violations at a revenue cost of less than 1% to 14% — a reasonable trade for grid safety.

**A single battery can protect the entire feeder, not just its own branch.** The branch comparison shows that a battery on Branch A eliminates all 11 violations on both branches through junction voltage rise. The DNSP does not need one battery per branch. However, the spillover margin is thin (B4 sits only 0.1–0.2% above the 0.94 pu limit), so placement decisions should account for the worst-case bus on the opposite branch, not just the battery's own branch.

**RL dispatch reduces network losses by 4–14%.** The oscillating evening strategy uses lower sustained current than DP's aggressive dispatch, reducing $I^2R$ losses. At ±100kW/400kWh, RL saves 13.6 kWh/day in losses compared to DP. The DNSP benefits from both fewer violations and lower loss costs. Under current tariff structures, these loss savings are not compensated to the battery operator — creating a positive externality that network tariff reform could internalise.

### For Battery Operators and Developers

**Battery sizing can be reduced with smart dispatch.** DP requires ±50kW/400kWh for 0 violations. RL achieves the same at ±50kW/200kWh — halving the required energy capacity. The 200 kWh battery earns 70–88% of the DP revenue while meeting all network obligations. For developers evaluating the business case, the capital cost reduction may outweigh the revenue reduction.

**The ±80kW/400kWh configuration offers the best revenue-feasibility trade-off.** It achieves 0 violations with RL revenue of A\$48.93/day — only A\$0.43/day (less than 1%) below the DP revenue. Among all tested configurations, this one maximises revenue while maintaining full network feasibility.

**The revenue cost of network safety is predictable.** Across all configurations, the RL revenue gap follows a consistent pattern: the gap decreases with battery capacity and increases with dispatch limit. This allows developers to estimate the network constraint cost for any configuration within the tested range.

### For Energy Policy and Regulation

**Community batteries provide network services that are currently uncompensated.** The battery eliminates 11 voltage violations per day and reduces losses by 4–14%, but the operator captures only arbitrage revenue. The DNSP and all feeder customers benefit from improved voltage quality and lower losses without paying for it. Regulatory frameworks should recognise and compensate this voltage support service — either through network support agreements, dynamic export tariffs, or inclusion of community batteries in the regulated asset base.

**The oscillating dispatch strategy has implications for battery degradation policy.** The RL agent's rapid charge/discharge cycling during evening peak increases throughput compared to DP's sustained discharge. While the degradation cost model (A\$0.02/kWh) captures average wear, rapid partial cycling may affect battery lifetime differently than deep cycles. Battery warranty terms and connection agreements should be evaluated against this dispatch pattern. More physically detailed degradation modelling (rain-flow counting on the SoC trajectory) is needed to quantify the impact.

**Reinforcement learning provides a practical tool for connection assessment.** Currently, DNSPs assess battery connection applications using static hosting capacity analysis. The DP + RL framework offers a more informative approach: DP finds the revenue upper bound, RL finds the network-feasible dispatch, and the gap quantifies the constraint cost. This information supports both the DNSP (what dispatch limit to impose) and the battery operator (what revenue to expect) in negotiating connection terms.