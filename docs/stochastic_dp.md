# Stochastic Dynamic Programming with Bayesian Belief Updating

## 1. Problem Statement

A community battery (200 kWh / ±100 kW) participates in the Australian NEM spot market, buying electricity when prices are low and selling when prices are high. The deterministic DP framework assumes the controller knows the entire day's 48 half-hour prices before dispatching. In practice, prices are revealed sequentially — the controller must decide how much to charge or discharge at each period without knowing future prices.

This extension formulates the dispatch problem as a **Partially Observable Markov Decision Process (POMDP)**. The agent does not know the day's price trajectory in advance. Instead, it maintains a probabilistic belief about which **price regime** the day belongs to, updating this belief as each new price is observed.

The **value of perfect information** is the revenue gap between the deterministic DP (perfect foresight) and the POMDP (no foresight), quantifying the monetary value of a perfect price forecast for battery arbitrage.

## 2. Price Regime Classification

### 2.1 Motivation

NEM spot prices exhibit distinct daily patterns. Some days are calm with narrow spreads of \$50–\$100; others feature extreme spikes exceeding \$10,000/MWh. Rather than modelling all days with a single stochastic process, we classify days into regimes with homogeneous within-day price dynamics. Each regime gets its own price transition model.

### 2.2 Features and Clustering

Each day $d$ is characterised by two features computed from its 48 half-hour prices $p_{d,0}, p_{d,1}, \ldots, p_{d,47}$:

$$\text{spread}_d = \max_t p_{d,t} - \min_t p_{d,t}$$

$$\text{mean}_d = \frac{1}{48}\sum_{t=0}^{47} p_{d,t}$$

Both features are right-skewed, so we apply a log transformation before clustering:

$$x_d = \bigl(\log(1 + \text{spread}_d),\; \log(1 + \text{mean}_d + s)\bigr)$$

where $s$ is a shift ensuring the argument is positive when some days have negative mean price. Features are standardised to zero mean and unit variance, then clustered using **k-means** with $k = 5$. Clusters are sorted by mean spread (ascending), so regime $r_0$ has the smallest spreads and $r_4$ has the largest.

### 2.3 Regime Prior

The prior belief $b_{-1}(\theta)$ — the probability of each regime before any prices are observed — is estimated from the training data, conditioned on weekday/weekend:

$$b_{-1}(\theta \mid d) = \frac{N(\theta, d) + \alpha}{\sum_{\theta'} \bigl(N(\theta', d) + \alpha\bigr)}$$

where $N(\theta, d)$ is the number of training days in regime $\theta$ with day type $d \in \lbrace\text{weekday}, \text{weekend}\rbrace$, and $\alpha = 0.5$ is Laplace smoothing to ensure no regime has zero prior probability.

The prior encodes calendar information: for example, high-spread days are predominantly weekdays, so the weekend prior assigns less weight to extreme regimes.

## 3. Tauchen Price Transition Model

### 3.1 Price Grid

Half-hour prices are discretised into $n_p = 24$ bins using a hybrid grid:

- **Bins 0–19**: percentile-based edges computed from all training prices below \$300/MWh. This places fine resolution (\$3–\$10 per bin) in the \$0–\$300 range where most arbitrage occurs.
- **Bins 20–23**: hand-placed tail bins at [\$300, \$500), [\$500, \$1,000), [\$1,000, \$3,000), [\$3,000, \$15,101).

Each price $p$ is mapped to a bin index $j$ such that $e_j \leq p < e_{j+1}$, where $e_0, e_1, \ldots, e_{24}$ are the bin edges. The bin midpoint $\bar{p}_j = (e_j + e_{j+1})/2$ serves as the representative price for reward computation.

### 3.2 Regime-Specific Transition Matrices

For each regime $\theta \in \lbrace 0,1,2,3,4 \rbrace$ and time step $t \in \lbrace 0,1,\ldots,46 \rbrace$, we estimate the transition probability:

$$P_\theta(j' \mid j, t) = \Pr(\text{price}_{t+1} \in \text{bin } j' \mid \text{price}_t \in \text{bin } j,\; \text{regime} = \theta)$$

This is estimated by counting transitions across all training days in regime $\theta$:

$$\hat{P}_\theta(j' \mid j, t) = \frac{N_\theta(j, j', t) + \alpha}{\sum_{j''}\bigl(N_\theta(j, j'', t) + \alpha\bigr)}$$

where $N_\theta(j, j', t)$ counts how many training days in regime $\theta$ had the price in bin $j$ at period $t$ and bin $j'$ at period $t+1$. The smoothing parameter $\alpha = 0.1$ prevents zero probabilities that would permanently eliminate regimes during belief updating.

The resulting tensor has shape $(5, 47, 24, 24)$: 5 regimes × 47 time transitions × 24 current bins × 24 next bins.

The transition matrices are **time-dependent** because price dynamics differ by time of day: prices tend to drop at 11:00 (solar ramp), rise at 17:00 (evening peak), and remain stable overnight. A single time-averaged matrix would miss these patterns.

### 3.3 Marginal Distributions

For the first belief update at $t = 0$ (no previous price to condition on), we use regime-specific marginal distributions:

$$f_\theta(j \mid t) = \Pr(\text{price}_t \in \text{bin } j \mid \text{regime} = \theta)$$

estimated as the empirical frequency of each price bin at each time step across training days in regime $\theta$, with the same Laplace smoothing. The resulting array has shape $(5, 48, 24)$.

### 3.4 Day Type Conditioning

The Tauchen transition matrices $P_\theta(j' \mid j, t)$ do **not** condition on weekday/weekend. Given the regime $\theta$ and time step $t$, the day type provides no additional information about price dynamics:

$$P(p_t \mid \theta, d, t) = P(p_t \mid \theta, t)$$

Day type affects only the **prior** $b_{-1}(\theta \mid d)$, not the within-day transitions. This is the conditional independence assumption: day type helps predict the regime, and the regime determines the price dynamics.

## 4. Bayesian Belief Updating

### 4.1 The Belief Vector

The agent maintains a belief vector $b_t = \bigl(b_t(\theta)\bigr)_{\theta \in \Theta}$ at each period $t$, representing its probability estimate that today belongs to each regime. The belief satisfies:

$$\sum_{\theta} b_t(\theta) = 1, \quad b_t(\theta) \geq 0 \;\;\forall \theta$$

### 4.2 Notation and Timing

| Symbol | When | Content |
|--------|------|---------|
| $b_{-1}$ | Before day starts | Prior from calendar (weekday/weekend frequencies) |
| $b_0$ | At $t = 0$ | Updated with first price $p_0$ |
| $b_t$ | At $t$ | Updated with prices $p_0, \ldots, p_t$ |

At each period $t$, the agent first **observes** $p_t$, then **updates** to $b_t$, then **dispatches** using $b_t$.

### 4.3 Derivation from Bayes' Theorem

For any two events $A$ and $B$, the definition of conditional probability gives:

$$\Pr(A \mid B) = \frac{\Pr(B \mid A) \cdot \Pr(A)}{\Pr(B)}$$

Let $A = \lbrace\text{regime} = \theta\rbrace$ and $B = \lbrace\text{observed price transition } j_{t-1} \to j_t\rbrace$, with all previous observations as background. Then:

$$b_t(\theta) = \frac{P_\theta(j_t \mid j_{t-1}, t-1) \cdot b_{t-1}(\theta)}{\sum_{\theta'} P_{\theta'}(j_t \mid j_{t-1}, t-1) \cdot b_{t-1}(\theta')}$$

Since the denominator is the same for all $\theta$:

$$\boxed{b_t(\theta) \propto b_{t-1}(\theta) \times P_\theta(j_t \mid j_{t-1}, t-1)}$$

The likelihood $P_\theta(j_t \mid j_{t-1}, t-1)$ is a direct lookup in the Tauchen transition matrix.

At $t = 0$, there is no previous price, so the marginal distribution is used:

$$b_0(\theta) \propto b_{-1}(\theta) \times f_\theta(j_0 \mid t = 0)$$

### 4.4 Belief Grid

The POMDP value function is indexed by the belief vector. Since belief is continuous on the 4-dimensional simplex, we discretise it to a finite grid of 18 representative points:

| Type | Points | Description |
|------|--------|-------------|
| Pure beliefs | 5 | Corners of the simplex: 100% on one regime |
| Dominant 90% | 5 | 90% on one regime, 2.5% on each other |
| Dominant 70% | 5 | 70% on one regime, 7.5% on each other |
| Weekday prior | 1 | Empirical regime frequencies for weekdays |
| Weekend prior | 1 | Empirical regime frequencies for weekends |
| Uniform | 1 | Equal probability across all regimes |

During backward induction, when a Bayesian update produces a belief not matching any grid point, the nearest point is found using $L_1$ distance (total variation):

$$\text{nearest}(b') = \arg\min_{b_k \in \text{grid}} \sum_\theta \lvert b'(\theta) - b_k(\theta) \rvert$$

## 5. POMDP Bellman Equation

### 5.1 State Space

At each period $t$, the agent's state is:

| Variable | Symbol | Range | Description |
|----------|--------|-------|-------------|
| Time | $t$ | $\lbrace 0, 1, \ldots, 47 \rbrace$ | Half-hour period |
| Battery SoC | $s$ | $[s_{\min}, s_{\max}]$ | State of charge (kWh), discretised to 81 points |
| Price bin | $j$ | $\lbrace 0, 1, \ldots, 23 \rbrace$ | Current observed price bin |
| Belief | $b$ | 18 grid points | Probability distribution over regimes |

Total state space: $48 \times 81 \times 24 \times 18 = 1{,}679{,}616$ states.

### 5.2 Action Space

The action $a$ is the battery charge/discharge power in kW, discretised to 47 evenly spaced values from $-100$ kW (full discharge) to $+100$ kW (full charge).

### 5.3 Bellman Equation

The value function satisfies:

$$V_t(s, j, b) = \max_{a \in \mathcal{A}(s)} \left[ r(s, a, \bar{p}_j) + \sum_{j'=0}^{n_p - 1} Q(j' \mid j, b, t) \cdot V_{t+1}\bigl(s', j', b'(j')\bigr) \right]$$

where:

**Immediate reward** (same as deterministic DP, using bin midpoint price):

$$r(s, a, \bar{p}_j) = -\frac{\bar{p}_j}{1000} \cdot a \cdot \Delta t - c_{\text{deg}} \cdot |a| \cdot \Delta t$$

**Next SoC** (deterministic given action):

$$s' = \begin{cases} s + \eta_c \cdot a \cdot \Delta t & \text{if } a \geq 0 \text{ (charging)} \\\ s + a \cdot \Delta t / \eta_d & \text{if } a < 0 \text{ (discharging)} \end{cases}$$

**Belief-weighted transition probability** over next price bin:

$$Q(j' \mid j, b, t) = \sum_\theta b(\theta) \cdot P_\theta(j' \mid j, t)$$

**Updated belief** for each possible next price $j'$:

$$b'(\theta \mid j') = \frac{b(\theta) \cdot P_\theta(j' \mid j, t)}{\sum_{\theta'} b(\theta') \cdot P_{\theta'}(j' \mid j, t)}$$

**Terminal condition**: $V_{48}(s, j, b) = 0$ for all $s, j, b$.

### 5.4 Computational Approach

The Bellman equation is solved by backward induction from $t = 47$ to $t = 0$. A key optimisation precomputes the expected future value for all SoC grid points outside the action loop.

For each $(t, j, b)$, define:

$$F(s_i) = \sum_{j'} Q(j') \cdot V_{t+1}\bigl(s_i, j', b'(j')\bigr)$$

where $s_i$ is the $i$-th SoC grid point. This array is computed once per $(t, j, b)$ by looping over $j'$ and accumulating. Then for each action $a$:

$$V_t(s, j, b) = \max_a \left[ r(s, a, \bar{p}_j) + F(s') \right]$$

where $F(s')$ is interpolated from the precomputed array. This reduces the per-action work from $O(n_p)$ to $O(1)$, yielding a **30× speedup** (from 940s to 31s).

## 6. Data

### 6.1 Training Data (2018–2023)

Tauchen transition matrices and regime classification are estimated from 6 years of AEMO NEM spot prices for the NSW1 region (which covers the ACT), totalling 2,191 complete days.

| Year | Days | Mean Price (\$/MWh) | Median Spread | Days with spread > \$1,000 |
|------|------|---------------------|---------------|----------------------------|
| 2018 | 365 | \$97 | \$93 | 3 |
| 2019 | 365 | \$80 | \$102 | 3 |
| 2020 | 366 | \$60 | \$76 | 15 |
| 2021 | 365 | \$73 | \$130 | 29 |
| 2022 | 365 | \$183 | \$214 | 20 |
| 2023 | 365 | \$96 | \$222 | 19 |

Source: AEMO aggregated price and demand data, 5-minute dispatch intervals resampled to 30-minute settlement periods.

### 6.2 Test Data (2024)

The POMDP policy is evaluated on 366 days from 2024, which were **not used** in training. This is a true out-of-sample test — the Tauchen matrices reflect historical patterns from 2018–2023, and the controller encounters 2024 prices without prior exposure.

2024 had the highest volatility in the dataset (mean spread \$818, 36 days with spread > \$1,000), providing a challenging test of the regime-based approach.

### 6.3 Regime Distribution on 2024 Test Days

Regime classification of 2024 test days uses the k-means model trained on 2018–2023:

| Regime | Test Days | Mean DP Revenue | Description |
|--------|-----------|-----------------|-------------|
| $r_0$ | 22 | \$11/day | Flat, minimal arbitrage |
| $r_1$ | 71 | \$63/day | Moderate variation |
| $r_2$ | 32 | \$21/day | Low-mean, low-spread |
| $r_3$ | 206 | \$36/day | Typical with some peaks |
| $r_4$ | 35 | \$742/day | Extreme spreads, spikes |

## 7. Results

### 7.1 Configuration

| Parameter | Value |
|-----------|-------|
| Battery | 200 kWh / ±100 kW, $\eta_c = \eta_d = 0.95$, 10% reserve |
| Regimes | 5 (k-means on log spread × log mean) |
| Training data | 2018–2023 (2,191 days, out-of-sample) |
| Test data | 2024 (366 days) |
| Price bins | 24 (20 percentile-based + 4 tail) |
| SoC grid | 81 points |
| Action grid | 47 points (±100 kW) |
| Belief grid | 18 points on the simplex |
| Laplace smoothing | $\alpha = 0.1$ (transitions), $\alpha = 0.5$ (priors) |
| Solve time | 27 seconds |

### 7.2 Annual Value of Perfect Information

| Metric | Value |
|--------|-------|
| Deterministic DP revenue (perfect foresight) | \$38,681/year |
| POMDP revenue (regime-aware, no foresight) | \$23,403/year |
| Value of perfect information | \$15,277/year |
| Annual capture rate | 60.5% |

### 7.3 Breakdown by Regime

| Regime | Days | DP/day | POMDP/day | Capture | Info/day | Info Annual | Median Convergence |
|--------|------|--------|-----------|---------|----------|-------------|-------------------|
| $r_0$ | 22 | \$11 | \$0.4 | 3.4% | \$11 | \$236 | 22 periods (11h) |
| $r_1$ | 71 | \$63 | \$36 | 57.0% | \$27 | \$1,916 | 6 periods (3h) |
| $r_2$ | 32 | \$21 | \$3 | 15.7% | \$18 | \$566 | 13 periods (6.5h) |
| $r_3$ | 206 | \$36 | \$19 | 52.0% | \$17 | \$3,514 | 10 periods (5h) |
| $r_4$ | 35 | \$742 | \$484 | 65.2% | \$258 | \$9,046 | 32 periods (16h) |
| **Total** | **366** | | | **60.5%** | | **\$15,277** | **13 periods (6.5h)** |

### 7.4 Breakdown by Day Type

| Day Type | Days | DP Annual | POMDP Annual | Capture | Info Annual |
|----------|------|-----------|--------------|---------|-------------|
| Weekday | 262 | \$34,111 | \$24,222 | 71.0% | \$9,889 |
| Weekend | 104 | \$4,570 | \$2,479 | 54.3% | \$2,091 |

### 7.5 Belief Convergence

The Bayesian belief identifies the correct regime (reaching 90% probability) at the following speeds:

| Regime | Median | P25 | P75 | Never Converge |
|--------|--------|-----|-----|----------------|
| $r_0$ | 22 periods | 14 | 36 | 14 of 22 days |
| $r_1$ | 6 periods | 4 | 10 | 18 of 71 days |
| $r_2$ | 13 periods | 8 | 18 | 5 of 32 days |
| $r_3$ | 10 periods | 4 | 19 | 18 of 206 days |
| $r_4$ | 32 periods | 16 | 36 | 29 of 35 days |

67 of 366 test days never converge to the correct regime. The Tauchen matrices trained on 2018–2023 do not recognise 2024's novel price patterns for those days.

### 7.6 Revenue Distribution

| Statistic | Det DP | POMDP |
|-----------|--------|-------|
| Mean | \$105.69/day | \$63.94/day |
| Median | \$37.97/day | \$20.08/day |
| Std | \$384.40 | \$245.32 |
| Min | \$4.02 | −\$6.80 |
| Max | \$4,748.80 | \$3,297.16 |
| P10 | \$16.84 | \$1.58 |
| P90 | \$102.73 | \$63.50 |

25 days have negative POMDP revenue — the agent's hedging strategy costs more in degradation than it earns on low-spread days.

## 8. Findings

### 8.1 A regime-aware controller captures 60.5% of perfect-foresight revenue

The POMDP controller earns \$23,403/year compared to \$38,681/year with perfect foresight. The \$15,277/year gap is the value of knowing exact intra-day price timing.

### 8.2 Capture rate increases with price spread

Regimes with larger price spreads achieve higher capture rates. On extreme days ($r_4$), the POMDP captures 65.2% — knowing "this is a high-volatility day" is enough to exploit the large spread, even without knowing exact timing. On low-spread days ($r_0$), even small timing errors lose most of the available revenue (3.4% capture).

### 8.3 Regime non-stationarity is the dominant limitation

67 of 366 test days never converge to the correct regime. This is the primary driver of the out-of-sample performance gap. When the same model is trained and tested on 2024 data (in-sample), the capture rate rises to 69.0%. The 8.5 percentage point gap quantifies the cost of regime non-stationarity, or equivalently, the value of annual model retraining.

### 8.4 Momentum does not help out-of-sample

An extended model conditioning Tauchen transitions on price momentum (falling/stable/rising) was tested. Despite momentum-conditional matrices showing meaningful KL divergence from unconditional matrices within the training data (KL ≈ 0.5 for falling/rising), the momentum extension reduced the annual capture rate from 60.5% to 56.7% out-of-sample. The 3× larger state space splits already sparse training data into thinner slices, increasing estimation noise that outweighs the signal.

### 8.5 Weekday controllers outperform weekend controllers

Weekday capture rate (71.0%) exceeds weekend (54.3%). Weekday price patterns are more regular (driven by predictable demand cycles), making the Tauchen transition model more accurate. Weekend prices are more variable relative to their lower spreads.

## 9. Architecture

```
src/stochastic/
├── regime.py      — K-means day classification on (log spread, log mean)
├── tauchen.py     — Price grid, transition matrices, momentum extension
├── belief.py      — Bayesian belief update, belief grid, convergence tests
├── solver.py      — POMDP backward induction and forward simulation
├── simulate.py    — Full-year simulation comparing configurations
└── analysis.py    — Value of information breakdown and summary statistics
```

All modules reuse the existing `Battery` class from `src/dp/battery.py` and the `DPSolver` from `src/dp/solver.py` for deterministic DP comparison.