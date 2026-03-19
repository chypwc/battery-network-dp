import numpy as np

def discretise_soc(soc, battery, n_bins=40):
    """
    Map continuous SoC to bin index 0..n_bins-1.

    Maps continuous SoC (e.g., 127.3 kWh) to a bin index (e.g., 23 out of 40).
    The Q-table needs integer indices.
    """
    # Clip to valid range
    soc = max(battery.soc_min, min(battery.soc_max, soc))
    # Normalise to [0, 1], then scale to bin index
    frac = (soc - battery.soc_min) / (battery.soc_max - battery.soc_min)
    idx = int( frac * (n_bins - 1))  # index up to n_bins - 1
    return min(idx, n_bins - 1)  # safely cap

def initialise_q_from_dp_value(Q, env, dp_result, n_soc_bins=80):
    """
    Initialise Q-table from DP value function and policy.
    
    For each (soc_bin, t), set Q[soc_bin, t, dp_action] = V_t(soc).
    This gives the agent exact knowledge of the DP's optimal strategy.
    The agent then refines in Phase 2 to avoid violations.
    """
    battery = env.battery
    V = dp_result['value_function']     # shape (T+1, dp_n_soc)
    policy = dp_result['policy']        # shape (T, dp_n_soc)
    dp_soc_grid = np.linspace(battery.soc_min, battery.soc_max, V.shape[1])

    for t in range(env.T):
        for s_idx in range(n_soc_bins):
            # Map RL soc_bin to continuous SoC
            frac = s_idx / (n_soc_bins - 1)
            soc = battery.soc_min + frac * (battery.soc_max - battery.soc_min)

            # Interpolate DP value and policy at this SoC
            v_value = np.interp(soc, dp_soc_grid, V[t])
            dp_action = np.interp(soc, dp_soc_grid, policy[t])

            # Find nearest RL action index
            action_idx = np.argmin(np.abs(env.action_values - dp_action))

            # Set Q-value = DP value for the optimal action
            Q[s_idx, t, action_idx] = v_value

            # Set neighboring actions to slightly lower values
            # so the agent prefers the DP action but knows alternatives exist
            for offset in [-1, 1]:
                neighbor_action = action_idx + offset
                if 0 <= neighbor_action < env.n_actions:
                    Q[s_idx, t, neighbor_action] = max(Q[s_idx, t, neighbor_action], 
                                                        v_value * 0.8)



# def initialise_q_from_dp(Q, env, dp_dispatch, n_soc_bins=40):
#     battery = env.battery
#     soc = battery.kwh_rated / 2

#     for t in range(env.T):
#         soc_idx = discretise_soc(soc, battery, n_soc_bins)

#         dp_action = dp_dispatch[t]
#         action_idx = np.argmin(np.abs(env.action_values - dp_action))

#         # Use remaining DP revenue as the seed value
#         # This approximates the true Q-value at this (state, time, action)
#         remaining_revenue = sum(
#             float(battery.reward(dp_dispatch[k], env.prices[k], env.dt))
#             for k in range(t, env.T)
#         )
#         seed_value = max(remaining_revenue, 1.0)

#         Q[soc_idx, t, action_idx] = seed_value

#         for offset in [-2, -1, 1, 2]:
#             neighbor = soc_idx + offset
#             if 0 <= neighbor < n_soc_bins:
#                 Q[neighbor, t, action_idx] = seed_value * 0.8

#         s_next = battery.next_soc(soc, dp_action, env.dt)
#         soc = float(max(battery.soc_min, min(battery.soc_max, s_next)))

    
# def extract_dispatch(Q, env, n_soc_bins):
#     """
#     Extract greedy policy from Q-table as a 48-element dispatch array.

#     Simulates forward from initial SoC, picking argmax Q at each step.
#     Same format as DPSolver.solve()['dispatch'].
#     """
#     dispatch = np.zeros(env.T)
#     soc = env.battery.kwh_rated / 2

#     for t in range(env.T):
#         soc_idx = discretise_soc(soc, env.battery, n_soc_bins)
#         action_idx = np.argmax(Q[soc_idx, t, :])
#         action_kw = env.action_values[action_idx]

#         # Check feasibility - same as environment
#         # clip to idel if action violate SoC bounds 
#         s_next = env.battery.next_soc(soc, action_kw, env.dt)
#         if s_next < env.battery.soc_min or s_next > env.battery.soc_max:
#             action_kw = 0.0
#             s_next = soc

#         dispatch[t] = action_kw
#         soc = float(s_next)

#     return dispatch


def extract_dispatch(Q, env, n_soc_bins=40):
    """
    Extract greedy policy by running through the environment.
    This ensures feasibility snap and OpenDSS consistency.
    """
    dispatch = np.zeros(env.T)
    state = env.reset()
    soc, t = state

    for step in range(env.T):
        soc_idx = discretise_soc(soc, env.battery, n_soc_bins)
        action_idx = np.argmax(Q[soc_idx, t, :])

        next_state, reward, done, info = env.step(action_idx)
        dispatch[step] = info['action_kw']

        soc, t = next_state

    return dispatch


def print_training_summary(history):
    """Print final training statistics."""
    n = len(history)
    last_50 = history[-50:] if n >= 50 else history

    avg_reward = np.mean([h['reward'] for h in last_50])
    avg_revenue = np.mean([h['revenue'] for h in last_50])
    avg_violations = np.mean([h['violations'] for h in last_50])
    zero_pct = sum(1 for h in last_50 if h['violations'] == 0) / len(last_50) * 100

    print(f"  Episodes trained:        {n}")
    print(f"  Avg reward (last 50):    {avg_reward:.2f}")
    print(f"  Avg revenue (last 50):   ${avg_revenue:.2f}")
    print(f"  Avg violations (last 50): {avg_violations:.1f}")
    print(f"  Zero-violation episodes:  {zero_pct:.0f}%")


def save_q_table(Q, filepath, metadata=None):
    """Save Q-table and metadata to .npz file."""
    save_dict = {'Q': Q}
    if metadata:
        for key, value in metadata.items():
            save_dict[key] = np.array(value)
    np.savez_compressed(filepath, **save_dict)
    print(f"  Q-table saved: {filepath} (shape {Q.shape})")


def load_q_table(filepath):
    """Load Q-table and metadata from .npz file."""
    data = np.load(filepath, allow_pickle=True)
    Q = data['Q']
    metadata = {key: data[key].item() for key in data.files if key != 'Q'}
    print(f"  Q-table loaded: {filepath} (shape {Q.shape})")
    return Q, metadata