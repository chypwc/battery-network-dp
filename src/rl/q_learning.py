"""
Q(s,t,a) ⟵ Q(s,t,a) + α [ r + γ max_a' Q(s', t', a') - Q(s, t, a)]
"""

from src.rl.utils import initialise_q_from_dp_value, discretise_soc, save_q_table, load_q_table

import numpy as np



def train(env, n_episodes=500, n_soc_bins=40,
          alpha=0.1, gamma=1.0,
          epsilon_start=0.3, epsilon_end=0.01,
          Q_init=None):
    """
    Train tabular Q-learning agent.

    Args:
        env: CommunityBatteryEnv instance
        n_episodes: training episodes
        n_soc_bins: SoC discretisation bins
        alpha: learning rate
        gamma: discount factor (1.0 = no discounting)
        epsilon_start/end: exploration rate decay
        Q_init: initialised Q-table

    Returns:
        Q: trained Q-table, shape (n_soc_bins, 48, n_actions)
        history: list of per-episode stats
    """
    T = env.T
    n_actions = env.n_actions
    battery = env.battery

    # Use provided Q-table or start from zeros
    if Q_init is not None:
        Q = Q_init.copy()
    else:
        Q = np.zeros((n_soc_bins, T, n_actions))

    history = []

    for episode in range(n_episodes):
        # Decay epsilon linearly
        # epsilon = epsilon_start - (epsilon_start - epsilon_end) * episode / n_episodes
        
        # Exponential decay:
        # ε = ε_start × (ε_end / ε_start) ^ (episode / n_episodes)
        epsilon = epsilon_start * (epsilon_end / epsilon_start) ** (episode / n_episodes)

        state = env.reset()
        soc, t = state
        soc_idx = discretise_soc(soc, battery, n_soc_bins)

        episode_reward = 0
        episode_revenue = 0
        episode_violations = 0

        for step in range(T):
            # Epsilon-greedy action selection
            if np.random.random() < epsilon:
                action = np.random.randint(n_actions)
            else:
                action = np.argmax(Q[soc_idx, t, :])
            
            # Take action 
            next_state, reward, done, info = env.step(action)
            next_soc, next_t = next_state
            next_soc_idx = discretise_soc(next_soc, battery, n_soc_bins)

            # Q-learning update
            if done:
                target = reward
            else:
                target = reward + gamma * np.max(Q[next_soc_idx, next_t, :])

            # decays alpha from 0.1 to 0.01 over training — learns fast early, stabilises late
            alpha_t = alpha * (0.01 / alpha) ** (episode / n_episodes)
            Q[soc_idx, t, action] += alpha_t * (target - Q[soc_idx, t, action])

            # Track stats
            episode_reward += reward
            episode_revenue += info['revenue']
            episode_violations += info['violations']

            # Advance
            soc_idx = next_soc_idx
            t = next_t

        history.append({
            'episode': episode,
            'reward': episode_reward,
            'revenue': episode_revenue,
            'violations': episode_violations,
            'epsilon': epsilon,
        })

        # Print progress every 2500 episodes
        if (episode + 1) % 2500 == 0:
            # average over last 50 episodes
            avg_reward = np.mean([h['reward'] for h in history[-50:]])
            avg_violations = np.mean([h['violations'] for h in history[-50:]])
            print(f"  Episode {episode+1:>4}/{n_episodes}  "
                  f"avg_reward={avg_reward:>8.2f}  "
                  f"avg_violations={avg_violations:>5.1f}  "
                  f"epsilon={epsilon:.3f}")
            
    return Q, history


def train_two_phase(env_phase1, env_phase2,
                    n_phase1=30000, n_phase2=20000,
                    n_soc_bins=40, dp_result=None,
                    epsilon_start=0.3, epsilon_end=0.005,
                    save_dir=None, label=None):

    if dp_result is not None:
        Q_init = np.zeros((n_soc_bins, env_phase1.T, env_phase1.n_actions))
        initialise_q_from_dp_value(Q_init, env_phase1, dp_result, n_soc_bins)
        print(f"  Q-table initialised from DP value function")
    else:
        Q_init = None

    # Phase 1
    print(f"  Phase 1: Refining arbitrage (penalty={env_phase1.penalty}, "
          f"{n_phase1} episodes)")
    Q, history1 = train(env_phase1, n_episodes=n_phase1,
                        n_soc_bins=n_soc_bins, Q_init=Q_init,
                        epsilon_start=epsilon_start, epsilon_end=0.05)

    phase1_rev = np.mean([h['revenue'] for h in history1[-50:]])
    phase1_viol = np.mean([h['violations'] for h in history1[-50:]])
    print(f"  Phase 1 result: revenue=${phase1_rev:.2f}, violations={phase1_viol:.1f}")

    # Save Phase 1 Q-table
    if save_dir and label:
        save_q_table(Q, f"{save_dir}/Q_phase1_{label}.npz", {
            'n_soc_bins': n_soc_bins,
            'n_actions': env_phase1.n_actions,
            'penalty': env_phase1.penalty,
            'n_episodes': n_phase1,
            'revenue': phase1_rev,
        })

    # Phase 2
    print(f"\n  Phase 2: Learning violation avoidance (penalty={env_phase2.penalty}, "
          f"{n_phase2} episodes)")
    Q, history2 = train(env_phase2, n_episodes=n_phase2,
                        n_soc_bins=n_soc_bins, Q_init=Q,
                        alpha=0.05,
                        epsilon_start=0.1, epsilon_end=epsilon_end)

    phase2_rev = np.mean([h['revenue'] for h in history2[-50:]])
    phase2_viol = np.mean([h['violations'] for h in history2[-50:]])
    print(f"  Phase 2 result: revenue=${phase2_rev:.2f}, violations={phase2_viol:.1f}")

    # Save Phase 2 Q-table
    if save_dir and label:
        save_q_table(Q, f"{save_dir}/Q_phase2_{label}.npz", {
            'n_soc_bins': n_soc_bins,
            'n_actions': env_phase2.n_actions,
            'penalty': env_phase2.penalty,
            'n_episodes': n_phase2,
            'revenue': phase2_rev,
            'violations': phase2_viol,
        })

    return Q, history1 + history2


if __name__ == "__main__":
    from src.dp.prices import load_day_prices
    from src.opendss.profiles import generate_load_profile, generate_solar_profile
    from src.rl.environment import CommunityBatteryEnv

    prices = load_day_prices('data/aemo/prices_typical_2024-06-28.csv')
    env = CommunityBatteryEnv(prices, generate_load_profile(), generate_solar_profile(), 
                              dispatch_limit=100, violation_penalty=5)

    print("Training Q-learning agent...")
    Q, history = train(env, n_episodes=3000, n_soc_bins=40)

    print(f"\nFinal 10 episodes:")
    for h in history[-10:]:
        print(f"  ep={h['episode']:>3}  reward={h['reward']:>8.2f}  "
              f"revenue={h['revenue']:>6.2f}  violations={h['violations']:>3}")
        
    # Extract greedy policy from trained Q-table
    print(f"\nLearned policy (greedy, from initial SoC=100):")
    soc = env.battery.kwh_rated / 2
    total_revenue = 0

    print(f"  {'t':<4} {'Price':>7} {'Action':>8} {'SoC':>8}")
    print(f"  {'--':<4} {'------':>7} {'------':>8} {'------':>8}")

    for t in range(env.T):
        soc_idx = discretise_soc(soc, env.battery, 40)
        action_idx = np.argmax(Q[soc_idx, t, :])
        action_kw = env.action_values[action_idx]

        # Check feasibility
        s_next = env.battery.next_soc(soc, action_kw, 0.5)
        if s_next < env.battery.soc_min or s_next > env.battery.soc_max:
            action_kw = 0.0
            s_next = soc

        revenue = float(env.battery.reward(action_kw, env.prices[t], 0.5))
        total_revenue += revenue

        a_str = f"{action_kw:+.0f}" if abs(action_kw) > 0.1 else "0"
        print(f"  {t:<4} ${env.prices[t]:>6.1f} {a_str:>8} {soc:>8.1f}")
        soc = float(s_next)

    print(f"  {'END':<4} {'':>7} {'':>8} {soc:>8.1f}")
    print(f"\n  Total revenue: ${total_revenue:.2f}")