# Dispatch Profile Comparison: Spot RL vs TOU RL

## Overview

This document compares the dispatch strategies discovered by Q-learning under two business models: wholesale spot arbitrage (Model A) and retail TOU arbitrage (Model B). Both models achieve zero voltage violations across all configurations. The comparison reveals how the price signal shapes the dispatch pattern while the network physics impose the same constraints.

Three configurations are selected to illustrate different regimes:

| Config | Why selected |
|--------|-------------|
| ±50kW / 200kWh | Capacity-constrained: small battery, low power — forces aggressive energy management |
| ±80kW / 400kWh | Well-sized: sufficient energy and power — the "design point" configuration |
| ±100kW / 200kWh | Power-constrained: high power, small battery — extreme oscillation and overvoltage risk |

## Configuration 1: ±50kW / 200kWh (Capacity-Constrained)

| Metric | Spot RL | TOU RL |
|--------|:---:|:---:|
| Revenue | A\$26.47/day | A\$75.34/day |
| Violations | 0 | 0 |
| V_min | 0.9413 pu | 0.9416 pu |
| Losses | 56.5 kWh | 56.6 kWh |

### Side-by-Side Dispatch

```
Time   Spot    Spot RL          TOU     TOU RL           Phase of Day
       Price   kW    SoC        Price   kW    SoC
00:00   60    +20   100 → 110   319      0   100 → 100   Overnight
01:30   79    +45   110 → 131   319      0   100 → 100   Overnight
05:30   60      0   131 → 131   319     +5   100 → 102   Pre-morning
06:00  101    -10   131 → 126   319    +20   102 → 112   Morning violation
06:30  148    -50   126 →  99   319    +30   112 → 126   Morning violation
07:00  230    -50    99 →  73   485    -50   126 → 100   Morning peak
07:30  228    -50    73 →  47   485    -50   100 →  74   Morning peak
08:00  103    -50    47 →  21   485    -50    74 →  47   Morning peak
08:30   40    +20    21 →  30   485    -50    47 →  21   Morning peak
11:00   25    +50    30 →  54   176    +45    21 →  42   Solar soak
12:00  -13    +50    77 →  101  176    +45    64 →  85   Solar soak
14:00   36    +10   172 → 177   176    +50   154 → 178   Solar soak
16:30  163    -50   199 → 178   319     +5   196 → 199   Pre-evening
17:00  137    -50   178 → 146   485    -50   199 → 172   Evening peak
17:30  174    -50   146 → 120   485    +40   172 → 191   Evening peak (!)
18:00  145    -45   120 →  96   485    -50   191 → 165   Evening peak
19:30  105    -40    46 →  25   485    -50   113 →  86   Evening peak
20:00  107    +40    25 →  44   485    -50    86 →  60   Evening peak
20:30  105    -40    44 →  23   485    -50    60 →  34   Evening peak
21:00  106     -5    23 →  20   319    -20    34 →  23   Post-peak
```

### Key Differences

**Overnight charging.** Spot RL charges +20 kW at midnight (A\$60/MWh) and +45 kW at 01:30 (A\$79/MWh) — buying cheap overnight electricity to prepare for morning discharge. TOU RL idles overnight because shoulder rate (A\$290/MWh) is too expensive for pre-charging. It starts from the initial 50% SoC without adding energy.

**Morning violation window (06:00–06:30).** Spot RL discharges -10 kW at 06:00 — injecting power to lift voltage above 0.94 pu. TOU RL charges +20 kW at 06:00 and +30 kW at 06:30 — storing energy for the upcoming peak discharge. The charging current still lifts local bus voltage sufficiently (V_min = 0.9454 pu) because the battery is at the end of the feeder and power injection in either direction affects the local voltage positively.

**Morning peak discharge.** Spot RL discharges for 4 periods (06:30–08:00) as spot prices fall from A\$148 to A\$103. TOU RL discharges for 4 periods (07:00–08:30) because every period pays A\$485/MWh peak rate. TOU RL captures a full hour more of peak-rate discharge.

**Evening oscillation.** Spot RL oscillates at t=39–41: +40, -40, -5 kW. Each cycle loses ~A\$0.50 because charge price (A\$107) exceeds discharge price (A\$105). TOU RL oscillates earlier at t=35: +40 kW charge at A\$485/MWh peak, then sustains -50 kW discharge through t=36–41. The TOU oscillation is at peak rate, so the refill is expensive but the extended discharge earns it back.

**Net result.** TOU RL earns 2.8× more revenue (A\$75.34 vs A\$26.47) with nearly identical network performance (0 violations, same losses). The higher revenue comes from the wider TOU spread and longer peak windows, not from a fundamentally different strategy.

## Configuration 2: ±80kW / 400kWh (Well-Sized)

| Metric | Spot RL | TOU RL |
|--------|:---:|:---:|
| Revenue | A\$48.93/day | A\$144.82/day |
| Violations | 0 | 0 |
| V_min | 0.9413 pu | 0.9433 pu |
| Losses | 78.0 kWh | 77.2 kWh |

### Side-by-Side Dispatch

```
Time   Spot    Spot RL          TOU     TOU RL           Phase of Day
       Price   kW    SoC        Price   kW    SoC
00:00   60    +30   200 → 214   319    +30   200 → 214   Overnight
00:30   76      0   214 → 214   319    +10   214 → 219   Overnight
06:00  101    -10   214 → 209   319    -15   224 → 216   Morning violation
06:30  148    -80   209 → 167   319    +15   216 → 223   Morning violation
07:00  230    -80   167 → 125   485    -80   223 → 181   Morning peak
07:30  228    -80   125 →  83   485    -80   181 → 139   Morning peak
08:00  103    -75    83 →  43   485    -80   139 →  97   Morning peak
08:30   40    +80    43 →  81   485    -80    97 →  55   Morning peak
11:00   25    +75    95 → 131   176    +80    55 →  93   Solar soak
13:00  -14    +80   245 → 283   176    +80   207 → 245   Solar soak
14:30   37    +80   359 → 397   176    +80   321 → 359   Solar soak end
15:00   52      0   397 → 397   319    +45   359 → 380   Shoulder
16:00  113    -45   397 → 373   319      0   380 → 380   Pre-evening
16:30  163    -80   373 → 331   319     -5   380 → 377   Pre-evening
17:00  137    -80   331 → 289   485    -80   377 → 335   Evening peak
18:00  145    -80   247 → 205   485    -80   293 → 251   Evening peak
19:00  115    -80   163 → 121   485    -80   209 → 167   Evening peak
19:30  105    -40   121 → 100   485    -80   167 → 125   Evening peak
20:00  107    -65   100 →  66   485    -80   125 →  83   Evening peak
20:30  105    -45    66 →  42   485    -80    83 →  41   Evening peak
```

### Key Differences

**Morning discharge depth.** Spot RL discharges to SoC=43 kWh (near minimum) by 08:30, then refills +80 kW at A\$40/MWh. TOU RL discharges to SoC=55 kWh by 08:30 and doesn't refill — it goes straight to solar soak charging at 11:00. The TOU agent doesn't need the 08:30 refill because there's no cheap price to exploit; instead, it accepts a lower morning SoC and relies on the 8-period solar soak window to fully recharge.

**Solar soak charging.** Both charge at full power during midday. Spot RL starts slightly earlier (10:30) because spot prices drop below A\$50/MWh. TOU RL charges exclusively during the solar soak window (11:00–14:30) at A\$176/MWh. Spot RL gets some periods at negative prices (getting paid to charge), while TOU RL always pays A\$176/MWh.

**Pre-evening timing.** Spot RL starts discharging at 16:00 (A\$113/MWh) because the spot price is already profitable. TOU RL waits until 17:00 because shoulder rate (A\$290/MWh) is not worth discharging into — the same energy earns A\$485/MWh one hour later.

**Evening discharge pattern.** With 400 kWh capacity, both models sustain discharge through the full evening without oscillation. Spot RL reduces power at t=39 (-40 kW) and t=41 (-45 kW) to stay above 0.94 pu. TOU RL maintains -80 kW for all 8 evening periods (17:00–20:30) — the larger initial SoC from delayed discharge start provides enough energy for sustained full-power output.

**No oscillation needed.** This is the key finding for the well-sized configuration: with 400 kWh, neither model needs the oscillation strategy. The battery has enough energy to sustain discharge through the entire evening while maintaining voltage above 0.94 pu. The revenue cost of network safety is minimal — A\$0.43/day for spot, A\$0.40/day for TOU.

## Configuration 3: ±100kW / 200kWh (Power-Constrained)

| Metric | Spot RL | TOU RL |
|--------|:---:|:---:|
| Revenue | A\$36.31/day | A\$81.56/day |
| Violations | 0 | 0 |
| V_min | 0.9406 pu | 0.9406 pu |
| Losses | 68.6 kWh | 64.8 kWh |

### Side-by-Side Dispatch

```
Time   Spot    Spot RL          TOU     TOU RL           Phase of Day
       Price   kW    SoC        Price   kW    SoC
00:00   60    +50   100 → 124   319      0   100 → 100   Overnight
01:00   75      0   124 → 124   319    +50   100 → 148   Overnight
01:30   79      0   124 → 124   319    +12   148 → 153   Overnight
04:00   62    +25   127 → 139   319      0   174 → 174   Overnight
05:30   60   +100   139 → 186   319     +6   183 → 186   Pre-morning
06:00  101    -12   186 → 180   319    +12   186 → 192   Morning violation
06:30  148    -94   180 → 130   319    +12   192 → 198   Morning violation
07:00  230   -100   130 →  78   485    -50   198 → 172   Morning peak
07:30  228   -100    78 →  25   485   -100   172 → 119   Morning peak
08:00  103     -6    25 →  22   485    -94   119 →  70   Morning peak
08:30   40      0    22 →  22   485    -94    70 →  20   Morning peak
10:30   44    +88    22 →  63   319    +12    23 →  29   Pre-solar
11:00   25     -6    63 →  60   176    +88    29 →  71   Solar soak
12:00  -13    +81    96 → 134   176    +81    71 → 109   Solar soak
14:00   36      0   199 → 199   176    +81   154 → 192   Solar soak
16:30  163   -100   199 → 147   319      0   198 → 198   Pre-evening
17:00  137    -38   147 → 127   485    -50   198 → 172   Evening peak
17:30  174    -94   127 →  78   485   -100   172 → 119   Evening peak
18:00  145    -50    78 →  52   485    -50   119 →  93   Evening peak
18:30  135    -44    52 →  28   485    -38    93 →  73   Evening peak
19:00  115    +38    28 →  46   485    -44    73 →  50   Evening peak
19:30  105    -38    46 →  26   485    -50    50 →  24   Evening peak
20:00  107    +38    26 →  44   485    +38    24 →  42   Evening peak (!)
20:30  105    -38    44 →  24   485    -38    42 →  22   Evening peak
```

### Key Differences

**Overnight pre-charging.** Spot RL charges +50 kW at midnight (A\$60/MWh) and +100 kW at 05:30 (A\$60/MWh), reaching SoC=186 kWh — nearly full. TOU RL spreads charging across the night in small increments (+50, +50, +12, +19, +12, +12, +19, +6 kW) at shoulder rate (A\$290/MWh), also reaching SoC=186 kWh. The TOU agent distributes charging more evenly to avoid high instantaneous current that would increase losses.

**Morning violation approach.** Spot RL discharges -12 kW at 06:00 (V_min = 0.9423). TOU RL charges +12 kW at 06:00 and +12 kW at 06:30 (V_min = 0.9423). Both achieve identical minimum voltage at the violation window despite opposite power directions. This confirms that at the end-of-feeder bus, both charging and small discharging can provide sufficient local voltage support.

**Morning peak intensity.** Spot RL uses full -100 kW for two periods (07:00–07:30) then stops because the battery is nearly empty (SoC=25 kWh) and spot prices drop to A\$103. TOU RL starts conservatively at -50 kW (07:00), then ramps to -100 kW (07:30) and sustains -94 kW through 08:30 — draining to SoC=20 kWh. TOU RL extracts more energy during morning peak because every period pays the same A\$485/MWh, so there's no reason to stop early.

**Evening oscillation.** Both models oscillate, but TOU RL needs fewer cycles because it starts discharging later:

Spot RL begins evening discharge at t=33 (16:30, A\$163/MWh) — one period before peak — hitting -100 kW immediately. By t=38 (19:00), the battery is at SoC=28 kWh and needs 2 oscillation cycles (+38, -38, +38, -38 kW at t=38–41) to maintain voltage support through the remaining evening periods. Each cycle is revenue-negative — charging at A\$115/MWh and discharging at A\$105/MWh loses ~A\$0.40.

TOU RL waits until t=34 (17:00, A\$485/MWh peak) to start discharging because the pre-peak shoulder rate (A\$319/MWh) is not worth discharging into. That one extra period of stored energy means TOU RL reaches t=39 (19:30) with enough reserves that only 1 oscillation cycle is needed (+38 kW charge at t=40, -38 kW discharge at t=41). The oscillation cost is only the round-trip efficiency loss (~A\$0.73) because both charge and discharge occur at the same A\$485/MWh peak rate.

The delayed discharge start is economically motivated — TOU RL holds energy because shoulder-rate discharge is suboptimal. But this patience accidentally reduces the need for oscillation, demonstrating how the TOU price structure naturally aligns better with network constraints than the volatile spot price profile.

**Minimum voltage.** Both models reach V_min = 0.9406 pu — the tightest margin across all configurations. At ±100kW with only 200 kWh, the agents are operating at the physical limit of what the battery can provide for voltage support. Any further reduction in capacity or increase in dispatch limit would likely make zero violations unachievable.

## Cross-Configuration Summary

### Revenue Comparison

| Config | Spot RL | TOU RL | TOU/Spot | Revenue Driver |
|--------|:---:|:---:|:---:|------------|
| ±50kW / 200kWh | A\$26.47 | A\$75.34 | 2.8× | Wider spread, longer peaks |
| ±80kW / 400kWh | A\$48.93 | A\$144.82 | 3.0× | Full 8-period evening discharge at peak rate |
| ±100kW / 200kWh | A\$36.31 | A\$81.56 | 2.2× | Morning peak fully captured under TOU |

The TOU advantage is largest (3.0×) for well-sized batteries that can sustain full-power discharge through the entire evening peak window. It is smallest (2.2×) for power-constrained batteries where both models sacrifice significant revenue for voltage support.

### Dispatch Strategy Comparison

| Aspect | Spot RL | TOU RL |
|--------|---------|--------|
| Overnight | Charges at low spot prices (A\$60–80/MWh) | Either idles or charges at shoulder (A\$290/MWh) |
| Morning violation fix | Small discharge (-10 to -12 kW) | Small charge (+12 to +30 kW) |
| Morning peak | 2–3 periods, stops when prices drop | 4 periods at full power (uniform peak rate) |
| Midday charging | Targets negative/low spot prices | Charges during solar soak window (11am–3pm) |
| Pre-evening | Starts at first high spot price (~16:00) | Waits for peak window (17:00) |
| Evening discharge | Variable power, follows spot price curve | Sustained power, all periods pay equally |
| Oscillation trigger | Revenue-negative, pure voltage support | Revenue-neutral (same peak rate for charge and discharge) |
| Oscillation cycles | More cycles (early discharge depletes battery sooner) | Fewer cycles (delayed start preserves energy longer) |
| Oscillation cost | ~A\$0.40–0.50/cycle (spot spread loss) | ~A\$0.73/cycle (efficiency loss only) |

### Why the Same Network Constraints Produce Different Dispatches

The voltage physics are identical — the same current through the same cables produces the same voltage drop regardless of the price signal. Both RL agents learn the same fundamental constraint: "at t=39 (19:30), if the battery is below ~25 kWh, the feeder voltage will drop below 0.94 pu."

The difference is how they prepare for this constraint. Spot RL has cheap overnight and negative-price midday energy, so it can afford to discharge aggressively in the morning (high spot prices) and oscillate cheaply in the evening (low spot prices). TOU RL has no cheap energy — shoulder and solar soak rates are both substantial costs — so it manages energy more conservatively, spreading charging across the night and relying on the full 8-period solar soak window to rebuild energy reserves.

The result is that TOU RL's dispatch is more predictable and more evenly distributed across time, while spot RL's dispatch is more opportunistic and concentrated at price extremes. Both achieve zero violations, demonstrating that the Q-learning framework adapts its strategy to the economic environment while satisfying the same network constraints.
