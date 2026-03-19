# Methods: Battery Dispatch Optimisation

This document provides the mathematical formulation for the two dispatch optimisation methods used in this project: dynamic programming (DP) and Q-learning. For results and key findings, see the [README](../README.md) and [DP vs RL Findings](dp_vs_rl_findings.md).

## Dynamic Programming Solver

### Bellman Equation

The optimal battery dispatch is found by backward induction over the value function:

$$V_t(s) = \max_{a \in \mathcal{A}(s,t)} \left[ r(s, a, p_t) + V_{t+1}(s') \right], \quad t = T{-}1, \ldots, 0$$

with terminal condition $V_T(s) = 0$ for all $s$.

| Symbol | Code | Meaning |
|--------|------|---------|
| $t$ | `t` | Time step (0 = 00:00, ..., 47 = 23:30) |
| $s$ | `soc` | State of charge (kWh) |
| $a$ | `action_kw` | Charge (+kW) or discharge (−kW) |
| $p_t$ | `prices[t]` | NEM spot price (A\$/MWh) |
| $s'$ | `s_next` | SoC after action $a$ |
| $V_t(s)$ | `V[t][i]` | Max future revenue from state $s$ at time $t$ |

### State Transition

The battery's state of charge evolves differently for charging and discharging due to conversion losses:

$$s' = \begin{cases} s + \eta_c \cdot a \cdot \Delta t & \text{if } a \geq 0 \text{ (charging)} \\\\ s + \dfrac{a}{\eta_d} \cdot \Delta t & \text{if } a < 0 \text{ (discharging)} \end{cases}$$

When charging, the grid delivers $a \cdot \Delta t$ kWh but only $\eta_c \cdot a \cdot \Delta t$ reaches the battery (the rest is lost as heat). When discharging, the battery must release $|a| \cdot \Delta t / \eta_d$ kWh internally to deliver $|a| \cdot \Delta t$ to the grid. Parameters: $\eta_c = \eta_d = 0.95$, $\Delta t = 0.5$ h.

### Reward Function

$$r(s, a, p_t) = -\frac{p_t}{1000} \cdot a \cdot \Delta t - c_{\text{deg}} \cdot |a| \cdot \Delta t$$

The first term is arbitrage revenue. When charging ($a > 0$), the battery buys electricity at price $p_t$, producing a cost (negative reward). When discharging ($a < 0$), the battery sells electricity, producing income (positive reward). The division by 1000 converts the price from A\$/MWh to A\$/kWh. The second term is battery degradation cost ($c_{\text{deg}} = 0.02$ A\$/kWh throughput), representing the shortened battery lifetime from cycling.

### Feasible Action Set

$$\mathcal{A}(s, t) = \lbrace a \in [-\bar{a}, \bar{a}] \mid s_{\min} \leq s' \leq s_{\max} \rbrace$$

Actions are bounded by the dispatch limit $\bar{a}$ (kW) and by the requirement that the next SoC stays within the battery's operating range: $s_{\min} = 0.1 \times E_{\text{rated}}$ (10% reserve) to $s_{\max} = E_{\text{rated}}$ (full capacity).

### Discretisation

The SoC and action spaces are discretised into $n_s$ and $n_a$ evenly spaced grid points. The value function at off-grid states is obtained by linear interpolation of $V_{t+1}$. Total computation per solve: $T \times n_s \times n_a$ evaluations (typically 48 x 81 x 81 = 315,000, runs in under a second).

### Price Data

Real AEMO NSW1 spot prices (the ACT falls within the NSW1 NEM region). Data is downloaded from AEMO's public aggregated price and demand portal at 5-minute dispatch resolution, then resampled to 30-minute settlement periods by averaging six consecutive dispatch prices.

## Network Verification (OpenDSS)

At each half-hour time step, OpenDSS solves a snapshot power flow with updated load multipliers, solar multipliers, and battery dispatch. The solver returns per-phase bus voltages (pu), total circuit losses (kW), and transformer apparent power loading (%).

Voltage limits follow AS 61000.3.100 for 230V supply: 0.94–1.10 pu (216V–253V). A violation is counted when any phase at any LV bus falls outside this range.

## Feedback Loop (DP + OpenDSS)

The integration layer coordinates the DP solver and OpenDSS model. The unconstrained DP dispatch may cause voltage violations when run through OpenDSS (e.g., the battery empties too early, leaving the evening peak unsupported). The feedback loop adds network constraints to the DP and re-solves:

```
constraints ← None

for iteration = 1 to max_iterations:

    if constraints is None:
        dispatch ← DP.solve(prices)
    else:
        dispatch ← DP.solve_constrained(prices, constraints)

    violations ← OpenDSS.check(dispatch, load_profile, solar_profile)

    if violations = 0:
        return dispatch                        ← converged

    if violations unchanged from last iteration:
        return dispatch                        ← battery capacity limit reached

    constraints ← generate_constraints(violations, battery)

return dispatch
```

The loop converges when all voltages are within limits, or stabilises when the battery's energy capacity is physically insufficient to cover all violation periods.

### Network-Constrained Feasible Set

When constraints are active, the DP's feasible action set is restricted:

$$\mathcal{A}_c(s, t) = \lbrace a \in \mathcal{A}(s,t) \mid a \leq a_{\min}^{\text{dis}}(t), a \leq a_{\max}^{\text{chg}}(t), s' \geq s_{\min}^{\text{net}}(t{+}1) \rbrace$$

| Constraint | Source | Purpose |
|------------|--------|---------|
| $a_{\min}^{\text{dis}}(t) < 0$ | Undervoltage at period $t$ | Force minimum discharge power |
| $a_{\max}^{\text{chg}}(t)$ | Overvoltage at period $t$ | Limit charging power |
| $s_{\min}^{\text{net}}(t{+}1)$ | Future undervoltage periods | Preserve energy for later discharge |

The minimum discharge power at each violation period is determined by binary search in OpenDSS: test discharge levels from 10 to 100 kW and find the smallest that lifts $V_{\min}$ above 0.94 pu. When the total energy required to cover all violations exceeds the battery's usable capacity, the constraint generator prioritises the latest block (evening peak) where violations are most severe.

### Feedback Loop Limitations

The feedback loop provides marginal improvement over unconstrained DP (typically reducing violations from 4 to 3) because the binding constraint is battery energy capacity, not dispatch strategy. The loop correctly identifies this and stabilises. The heuristic constraints cannot discover strategies that are revenue-suboptimal at individual time steps — notably the oscillating evening strategy that Q-learning finds.

## Q-Learning

### Motivation

The DP solver maximises revenue but has no knowledge of network voltage. Violations are only detected afterward, and the feedback loop's heuristic constraints cannot discover strategies that are revenue-suboptimal but network-optimal. Q-learning addresses this by embedding the network response directly into the reward signal.

### Environment

The agent interacts with a Gymnasium-style environment wrapping the OpenDSS network model. At each time step $t$, the agent observes state $(s_t, t)$ where $s_t$ is the battery SoC, selects a discrete action $a_t$ (charge/discharge power), and the environment returns the next state, reward, and termination flag.

The environment calls OpenDSS at each step to solve power flow with the current load, solar, and battery dispatch. Voltage violations are counted across all LV bus phases.

### Reward Function

$$r_t = r_{\text{arb}}(s_t, a_t, p_t) - \lambda \cdot n_{\text{viol},t}$$

where $r_{\text{arb}}$ is the arbitrage reward (identical to the DP reward function), $\lambda$ is the violation penalty weight, and $n_{\text{viol},t}$ is the number of bus phases with voltage outside the 0.94–1.10 pu range at time $t$.

### Q-Learning Update

The agent maintains a Q-table $Q(s, t, a)$ indexed by discretised SoC bin, time step, and action index. After each transition:

$$Q(s_t, t, a_t) \leftarrow Q(s_t, t, a_t) + \alpha_t \left[ r_t + \gamma \max_{a'} Q(s_{t+1}, t{+}1, a') - Q(s_t, t, a_t) \right]$$

where $\gamma = 1.0$ (no discounting over the finite horizon) and both the learning rate $\alpha_t$ and exploration rate $\epsilon_t$ decay exponentially over training episodes:

$$\alpha_t = \alpha_0 \cdot (0.01 / \alpha_0)^{e / N}$$

$$\epsilon_t = \epsilon_0 \cdot (\epsilon_{\text{end}} / \epsilon_0)^{e / N}$$

where $e$ is the current episode and $N$ is the total number of episodes.

### Action Selection

The agent uses $\epsilon$-greedy action selection: with probability $\epsilon_t$, select a uniformly random action; otherwise, select $\arg\max_a Q(s_t, t, a)$.

When the selected action is infeasible (would violate SoC bounds), the environment snaps to the nearest feasible action rather than clipping to idle. This ensures the agent learns the value of boundary actions rather than receiving zero reward for infeasible attempts.

### Two-Phase Training

A single penalty value cannot simultaneously encourage arbitrage exploration and violation avoidance. Training proceeds in two phases:

| | Phase 1: Arbitrage | Phase 2: Network Safety |
|---|---|---|
| Objective | Learn profitable dispatch | Refine for voltage feasibility |
| Penalty $\lambda$ | 0 | 5.0 – 10.0 |
| OpenDSS calls | None (skip_network=True) | Every time step |
| Q-table init | DP value function $V_t(s)$ | Phase 1 output |
| Epsilon | 0.3 to 0.05 | 0.1 to 0.001 |
| Alpha | 0.1 to 0.01 | 0.05 to 0.01 |
| Episodes | 30,000 – 50,000 | 50,000 – 100,000 |

**Phase 1** uses penalty=0 and skips OpenDSS calls entirely (`skip_network=True`), running approximately 100x faster than Phase 2. The Q-table is initialised from the DP value function: for each SoC bin and time step, the DP's optimal action receives a Q-value equal to the interpolated value $V_t(s)$, and neighbouring actions receive 80% of that value. This gives the agent a strong arbitrage foundation without requiring hundreds of thousands of exploration episodes.

**Phase 2** enables OpenDSS and introduces the violation penalty. The agent starts with a profitable strategy from Phase 1 and makes targeted adjustments at violation periods. Lower initial epsilon (0.1) protects the good arbitrage strategy while allowing exploration at critical evening periods. Lower initial alpha (0.05) ensures Phase 2 updates don't overwrite the profitable midday charging strategy learned in Phase 1.

### Q-Table Initialisation from DP Value Function

The DP solver returns the full value function $V_t(s)$ and optimal policy $\pi_t(s)$ at every grid point. The Q-table is initialised by interpolating these onto the RL's SoC bins:

```
For each SoC bin s_idx = 0, ..., n_bins-1:
    For each time step t = 0, ..., 47:
        soc = soc_min + s_idx / (n_bins - 1) * (soc_max - soc_min)
        v_value = interpolate(V[t], dp_soc_grid, soc)
        dp_action = interpolate(policy[t], dp_soc_grid, soc)
        action_idx = nearest(env.action_values, dp_action)
        Q[s_idx, t, action_idx] = v_value
        Q[s_idx, t, nearby_actions] = 0.8 * v_value
```

This initialisation fills the Q-table at every state, not just along the DP's trajectory. The agent knows the value of being at any SoC at any time step before training begins, which prevents the exploration problem observed in cold-start training.

### Training Hyperparameters

| Parameter | ±50kW configs | ±80kW configs | ±100kW configs |
|-----------|:---:|:---:|:---:|
| SoC bins | 80 | 80 | 100–120 |
| Actions | 21 (5kW steps) | 33 (5kW steps) | 33 (6kW steps) |
| Phase 1 episodes | 50,000 | 30,000–50,000 | 50,000 |
| Phase 2 episodes | 50,000 | 80,000 | 100,000 |
| Phase 2 penalty $\lambda$ | 5.0 | 5.0 | 10.0 |
| Phase 2 epsilon end | 0.001 | 0.001 | 0.001 |

Higher dispatch limits require more actions (finer power resolution), more SoC bins (each action moves more kWh), more Phase 2 episodes (wider action space to explore), and higher penalty (more severe violations to overcome).
