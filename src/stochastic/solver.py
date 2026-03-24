"""
POMDP solver for battery dispatch under price uncertainty.

Solves the Bellman equation over (time, SoC, price_bin, belief)
using backward induction, with Bayesian belief updating.
"""

import numpy as np
import pandas as pd
from src.dp.battery import Battery
from src.stochastic.belief import (
    update_belief, nearest_belief, belief_update_from_transition)


class POMDPSolver:
    """
    Backward-induction POMDP solver for battery arbitrage
    under price regime uncertainty.

    State: (t, soc, price_bin, belief_idx)  
    Action: charge/discharge power (kW)
    """

    def __init__(self, battery: Battery, bin_mids, bin_edges, trans, marginal,
                 belief_grid, dt_hours=0.5, n_soc=81, n_actions=21,
                 dispatch_limit=None):
        """
        Args:
            battery: Battery instance
            bin_mids: price bin midpoints, shape (n_bins,)
            bin_edges: price bin edges, shape (n_bins+1,)
            trans: transition matrices, shape (n_regimes, 47, n_bins, n_bins)
            marginal: marginal distributions, shape (n_regimes, 48, n_bins)
            belief_grid: belief grid points, shape (n_beliefs, n_regimes)
            dt_hours: time step duration (0.5 hours)
            n_soc: number of SoC grid points
            n_actions: number of action grid points
            dispatch_limit: max charge/discharge power (kW)
        """
        self.battery = battery
        self.bin_mids = bin_mids
        self.bin_edges = bin_edges
        self.trans = trans
        self.marginal = marginal
        self.belief_grid = belief_grid
        self.dt = dt_hours

        self.n_bins = len(bin_mids)
        self.n_beliefs = len(belief_grid)
        self.n_regimes = trans.shape[0]
        self.T = 48

        # Detect momentum mode from trans shape
        self.use_momentum = (trans.ndim == 5)
        self.n_momentum = trans.shape[3] if self.use_momentum else 1

        # SoC grid
        self.n_soc = n_soc
        self.soc_grid = np.linspace(battery.soc_min, battery.soc_max, n_soc)

        # Action grid
        max_power = dispatch_limit if dispatch_limit else battery.kw_rated
        self.n_actions = n_actions
        self.action_grid = np.linspace(-max_power, max_power, n_actions)
        self.dispatch_limit = dispatch_limit

    
    def solve(self):
        """
        Solve the POMDP by backward induction.
        
        Returns:
            V: value function
               standard: shape (T+1, n_soc, n_bins, n_beliefs)
               momentum: shape (T+1, n_soc, n_bins, n_momentum, n_beliefs)
            policy: optimal action (same shape as V but T instead of T+1)
        """
        T = self.T
        n_soc = self.n_soc
        n_bins = self.n_bins
        n_beliefs = self.n_beliefs
        n_actions = self.n_actions
        n_regimes = self.n_regimes
        n_momentum = self.n_momentum
        use_momentum = self.use_momentum
        
        battery = self.battery
        dt = self.dt
        trans = self.trans
        belief_grid = self.belief_grid
        soc_grid = self.soc_grid
        action_grid = self.action_grid
        bin_mids = self.bin_mids

        # Value function and policy tables
        if use_momentum:
            from src.stochastic.tauchen import get_momentum_idx
            V = np.zeros((T + 1, n_soc, n_bins, n_momentum, n_beliefs))
            policy = np.zeros((T, n_soc, n_bins, n_momentum, n_beliefs))
        else:
            V = np.zeros((T+1, n_soc, n_bins, n_beliefs))
            policy = np.zeros((T, n_soc, n_bins, n_beliefs))

        # Backward induction: t = T - 1 down to 
        # for t:                          # 48 time steps (backward)
        #     for j:                        # 24 price bins
        #         for bi:                     # 18 belief points
        #         precompute Q_next, b'     # independent of action and SoC
        #         for si:                   # 81 SoC points
        #             get feasible actions
        #             for each action:        # ~21 actions
        #             compute reward
        #             compute future value  # sum over 24 next price bins
        #             track best
        for t in range(T - 1, -1, -1):
            if t % 10 == 0:
                print(f"Solving t = {t}...")

            for j in range(n_bins):
                # "The price I'm currently observing falls in bin j." 
                # This determines the reward (buy/sell at price \bar{p}_j​) 
                # and which row of the Tauchen transition matrix to use.
                price = bin_mids[j]

                # Momentum loop: 3 states if momentum, 1 dummy if not
                for mi in range(n_momentum):
                    for bi in range(n_beliefs):
                        # "My current belief about which regime today is." 
                        # This determines how I weight the n_regimes regime-specific transition matrices 
                        # and how the belief will update when I see the next price.
                        belief = belief_grid[bi]        # (n_regimes,)
                        

                        # --- Precompute next-price transitions ---
                        # Independent of action, depends only on (t, j, belief)
                        
                        # Q(j' | j, b, t) = sum_theta b(theta) * P_theta(j'|j,t)
                        # Updated belief b'(j') for each possible next price
                        # Nearest belief index for each j'

                        # Precompute for this (t, j, b) — independent of action
                        # For each next price bin j':
                        #     Q[j'] = sum over theta of b[theta] * trans[theta, t, j, j']
                        #     b'[j'] = belief_update(b, j', j, t)
                        #     b'_idx[j'] = nearest_belief(b'[j'])

                        if t < T - 1:
                            # Transition slice depends on momentum mode
                            if use_momentum:
                                trans_slice = trans[:, t, j, mi, :]     # (n_regimes, n_bins)
                            else:
                            # trans[theta, t, j, :] gives P_theta(j'|j, t)
                            # for all j' at once — shape (n_bins,)
                            # Stack across regimes: shape (n_regimes, n_bins)
                                trans_slice = trans[:, t, j, :]     # (n_regimes, n_bins)

                            # Q(j') = sum_theta b(theta) * P_theta(j'|j, t)
                            Q_next = belief @ trans_slice       # (n_bins,)

                            
                            # For each SoC grid point, compute the expected future
                            # value summed over all next price bins.
                            # future_by_soc[si] = sum_j' Q(j') * V[t+1, si, j', b'_idx(j')]

                            future_by_soc = np.zeros(n_soc)
                            for j_next in range(n_bins):
                                if Q_next[j_next] < 1e-12:
                                    # This transition is essential impossible
                                    continue

                                # b'(theta) ∝ b(theta) * P_theta(j'| j, t)
                                b_updated = belief_update_from_transition(
                                    belief, trans_slice[:, j_next]
                                )
                                
                                bi_next = nearest_belief(
                                    b_updated, belief_grid
                                )
                                
                                if use_momentum:
                                    m_next = get_momentum_idx(j_next, j)
                                    future_by_soc += (
                                        Q_next[j_next]
                                        * V[t+1, :, j_next, m_next, bi_next]
                                    )
                                
                                else:
                                    future_by_soc += (
                                        Q_next[j_next]
                                        * V[t + 1, :, j_next, bi_next]
                                    )

                        # --- Loop over SoC ---
                        for si in range(n_soc):
                            soc = soc_grid[si]

                            # Feasible actions
                            feasible = battery.feasible_actions(soc, dt, action_grid)
                            if len(feasible) == 0:
                                continue

                            # Rewards for all feasible actions (vectorised)
                            rewards = battery.reward(feasible, price, dt)

                            # Next SoC for all feasible actions (vectorised)
                            s_nexts = battery.next_soc(soc, feasible, dt)

                            if t == T - 1:
                                # Last period: no future value
                                best_idx = np.argmax(rewards)
                                if use_momentum:
                                    V[t, si, j, mi, bi] = rewards[best_idx]
                                    policy[t, si, j, mi, bi] = feasible[best_idx]
                                else:    
                                    V[t, si, j, bi] = rewards[best_idx]
                                    policy[t, si, j, bi] = feasible[best_idx]
                            else:
                                # Interpolate Future value for all actions at once
                                futures = np.interp(s_nexts, soc_grid, future_by_soc)

                                # Total values for each action
                                totals = rewards + futures 

                                best_idx = np.argmax(totals)
                                if use_momentum:
                                    V[t, si, j, mi, bi] = totals[best_idx]
                                    policy[t, si, j, mi, bi] = feasible[best_idx]
                                else:
                                    V[t, si, j, bi] = totals[best_idx]
                                    policy[t, si, j, bi] = feasible[best_idx]

        return V, policy 


    def simulate(self, prices, V, policy, b_minus1):
        """
        Forward simulation using the POMDP policy on actual prices.
        
        Args:
            prices: actual price array, length 48
            V: value function from solve()
            policy: policy from solve()
            b_minus1: initial belief before seeing any prices (prior)
        
        Returns:
            dict with: dispatch, soc, revenue, total_revenue,
                       beliefs (48 beliefs used for dispatch),
                       belief_trajectory (49 beliefs including b_{-1})
        """
        from src.stochastic.tauchen import get_bin_index, get_momentum_idx

        T = len(prices)
        battery = self.battery
        dt = self.dt
        soc_grid = self.soc_grid
        use_momentum = self.use_momentum

        dispatch = np.zeros(T)
        soc_trajectory = np.zeros(T + 1)
        revenue = np.zeros(T)
        belief_trajectory = np.zeros((T + 1, self.n_regimes))  # including b_{-1}
        beliefs_at_dispatch = np.zeros((T, self.n_regimes))

        # Initial SoC
        soc_trajectory[0] = battery.kwh_rated / 2
        belief_trajectory[0] = b_minus1.copy()

        for t in range(T):
            actual_price = prices[t]
            j_now = get_bin_index(actual_price, self.bin_edges)
            j_prev = get_bin_index(prices[t - 1], self.bin_edges) if t > 0 else None

            # --- Update belied (observe price, then dispatch) ---
            if use_momentum:
                if t == 0:
                    m_now = 1   # stable
                elif t == 1:
                    m_now = get_momentum_idx(j_now, j_prev)
                    m_prev = 1  # t=0 had no previous, so momentum was stable
                else:
                    j_prev_prev = get_bin_index(prices[t - 2], self.bin_edges)
                    m_prev = get_momentum_idx(j_prev, j_prev_prev)
                    m_now = get_momentum_idx(j_now, j_prev)

            if t == 0:
                b_t = update_belief(
                    b_minus1, j_now, j_prev, t,
                    self.trans, self.marginal
                )
            else:
                b_t = update_belief(
                    belief_trajectory[t], j_now, j_prev, t,
                    self.trans, self.marginal,
                    momentum=m_prev if use_momentum else None,
                )
            
            beliefs_at_dispatch[t] = b_t

            # --- Look up policy ---
            soc = soc_trajectory[t]
            bi = nearest_belief(b_t, self.belief_grid)

            # Interpolate action from policy
            if use_momentum:
                action = np.interp(
                    soc, soc_grid, policy[t, :, j_now, m_now, bi]
                )
            else:
                action = np.interp(
                    soc, soc_grid, policy[t, :, j_now, bi]
                )

            # Snap to nearest feasible action
            feasible = battery.feasible_actions(
                soc, dt, self.action_grid
            )
            if len(feasible) > 0:
                action = feasible[np.argmin(np.abs(feasible - action))]
            else:
                action = 0.0

            # --- Execute ---
            dispatch[t] = action
            soc_trajectory[t + 1] = battery.next_soc(soc, action, dt)
            soc_trajectory[t + 1] = max(
                battery.soc_min,
                min(battery.soc_max, float(soc_trajectory[t+1]))
            )
            revenue[t] = battery.reward(action, actual_price, dt)

            # Store belief for next period
            belief_trajectory[t + 1] = b_t

        return {
            'dispatch': dispatch,
            'soc': soc_trajectory,
            'revenue': revenue,
            'total_revenue': np.sum(revenue),
            'prices': prices,
            'beliefs': beliefs_at_dispatch,
            'belief_trajectory': belief_trajectory,
        }
    

if __name__ == '__main__':
    import time
    import sys
    import os
    from src.dp.battery import Battery
    from src.dp.solver import DPSolver
    from src.dp.prices import load_day_prices, extract_day, load_and_clean
    from src.stochastic.regime import (classify_days, compute_priors, 
                                        REGIME_NAMES, N_REGIMES)
    from src.stochastic.tauchen import (build_price_matrix, build_price_grid,
                                         build_transition_matrices, get_bin_index)
    from src.stochastic.belief import (build_marginal_distributions,
                                        build_belief_grid)
    from src.stochastic.tauchen import build_momentum_transition_matrices

    # --- Build momentum transition matrices ---
    USE_MOMENTUM = True  # toggle this to compare

    # --- Logging ---
    os.makedirs('data/stochastic', exist_ok=True)
    log_file = open('data/stochastic/pomdp_test_output.log', 'w')
    
    class Tee:
        def __init__(self, *files):
            self.files = files
        def write(self, text):
            for f in self.files:
                f.write(text)
                f.flush()
        def flush(self):
            for f in self.files:
                f.flush()
    
    sys.stdout = Tee(sys.stdout, log_file)

    # --- Setup ---
    battery = Battery(kwh_rated=200, kw_rated=100)
    
    day_df, kmeans_info = classify_days(
        price_csv_path='data/aemo/nem_prices_NSW1_2018_2023_clean.csv',
        annual_results_path='data/pypsa/annual_dispatch_results.csv'
    )
    priors = compute_priors(day_df)
    
    price_matrix, valid_mask = build_price_matrix(
        'data/aemo/nem_prices_NSW1_2018_2023_clean.csv', day_df
    )
    price_matrix_valid = price_matrix[valid_mask]
    day_regimes = day_df['regime_idx'].values[valid_mask]
    
    bin_edges, bin_mids = build_price_grid(price_matrix_valid, n_bulk_bins=20)
        
    trans = build_transition_matrices(
        price_matrix_valid, day_regimes, bin_edges,
        n_regimes=N_REGIMES, smooth_alpha=0.1
    )
    marginal = build_marginal_distributions(
        price_matrix_valid, day_regimes, bin_edges,
        n_regimes=N_REGIMES, smooth_alpha=0.1
    )
    belief_grid, grid_labels = build_belief_grid(priors)

    print(f"=== POMDP Test Suite ===")
    print(f"  N_REGIMES: {N_REGIMES}")
    print(f"  Regime names: {REGIME_NAMES}")
    print(f"  Belief grid: {len(belief_grid)} points")
    print(f"  Price bins: {len(bin_mids)}")
    print(f"  Transition matrices: {trans.shape}")

    # --- Solve POMDP ---
    N_ACTIONS = 47
    N_SOC = 81

    if USE_MOMENTUM:
        trans_m = build_momentum_transition_matrices(
            price_matrix_valid, day_regimes, bin_edges,
            n_regimes=N_REGIMES, smooth_alpha=0.1
        )
        print(f"  Momentum transition matrices: {trans_m.shape}")
        solver_trans = trans_m
    else:
        solver_trans = trans

    print(f"\n=== Solving POMDP (n_soc={N_SOC}, n_actions={N_ACTIONS}) ===")
    solver = POMDPSolver(
        battery=battery,
        bin_mids=bin_mids,
        bin_edges=bin_edges,
        trans=solver_trans,
        marginal=marginal,
        belief_grid=belief_grid,
        n_soc=N_SOC,
        n_actions=N_ACTIONS,
        dispatch_limit=100
    )
    
    start = time.time()
    V, policy = solver.solve()
    elapsed = time.time() - start
    print(f"  Solve time: {elapsed:.1f} seconds")
    print(f"  V shape: {V.shape}")
    print(f"  Policy shape: {policy.shape}")

    # --- Deterministic DP solver (for comparison) ---
    dp_solver = DPSolver(battery, n_soc=N_SOC, n_actions=N_ACTIONS, 
                          dispatch_limit=100)

    # --- Representative days ---
    representative_days = {
        'low':     ('2024-02-24', 'data/aemo/prices_low_2024-02-24.csv'),
        'typical': ('2024-06-28', 'data/aemo/prices_typical_2024-06-28.csv'),
        'high':    ('2024-06-25', 'data/aemo/prices_high_2024-06-25.csv'),
        'vhigh':   ('2024-05-03', 'data/aemo/prices_very_high_2024-05-03.csv'),
        'spike':   ('2024-02-29', 'data/aemo/prices_spike_2024-02-29.csv'),
    }

    # Check which files exist
    available_days = {}
    for name, (date, path) in representative_days.items():
        if os.path.exists(path):
            available_days[name] = (date, path)
        else:
            print(f"  Warning: {path} not found, skipping {name}")

    # If representative day CSVs don't exist, extract from full-year data
    if len(available_days) == 0:
        print("\n  No representative day CSVs found. Extracting from full-year data...")
        full_prices = load_and_clean(
            [f'data/aemo/nem_prices_NSW1_clean.csv']
        )
        # Use days from the regime classification
        for regime_idx in range(min(N_REGIMES, 5)):
            mask = day_df['regime_idx'] == regime_idx
            regime_days = day_df[mask].sort_values('dp_revenue')
            if len(regime_days) > 0:
                # Pick the median day
                mid = len(regime_days) // 2
                date = regime_days.iloc[mid]['date']
                date_str = str(date)[:10]
                prices = extract_day(full_prices, date_str)
                if prices is not None and len(prices) == 48:
                    name = REGIME_NAMES[regime_idx]
                    available_days[name] = (date_str, prices)

    # --- Run on all available days ---
    print(f"\n{'='*80}")
    print(f"=== Value of Perfect Information: Representative Days ===")
    print(f"{'='*80}")
    
    results_table = []

    for name, (date, path_or_prices) in available_days.items():
        # Load prices
        if isinstance(path_or_prices, str):
            prices = load_day_prices(path_or_prices)
        else:
            prices = path_or_prices

        # Determine day type
        date_dt = pd.to_datetime(date) if isinstance(date, str) else date
        is_weekday = date_dt.weekday() < 5
        day_type = 'weekday' if is_weekday else 'weekend'
        b_minus1 = priors[day_type]

        # POMDP simulation
        result_pomdp = solver.simulate(prices, V, policy, b_minus1)
        
        # Deterministic DP
        result_dp = dp_solver.solve(prices, initial_soc=100)

        # Capture rate
        capture = (result_pomdp['total_revenue'] / result_dp['total_revenue'] * 100 
                   if result_dp['total_revenue'] != 0 else 0)
        info_value = result_dp['total_revenue'] - result_pomdp['total_revenue']

        results_table.append({
            'name': name,
            'date': date,
            'day_type': day_type,
            'dp_revenue': result_dp['total_revenue'],
            'pomdp_revenue': result_pomdp['total_revenue'],
            'capture_rate': capture,
            'info_value': info_value,
        })

        # Print detail for each day
        print(f"\n--- {name.upper()} day: {date} ({day_type}) ---")
        print(f"  Det DP revenue:  ${result_dp['total_revenue']:>10.2f}")
        print(f"  POMDP revenue:   ${result_pomdp['total_revenue']:>10.2f}")
        print(f"  Capture rate:    {capture:>10.1f}%")
        print(f"  Info value:      ${info_value:>10.2f}")
        
        # Belief convergence
        beliefs = result_pomdp['beliefs']
        for t in [0, 3, 6, 12, 24]:
            if t < len(beliefs):
                b = beliefs[t]
                b_max = b.max()
                b_regime = b.argmax()
                b_str = '  '.join(f'{x:.3f}' for x in b)
                print(f"  t={t:2d}: [{b_str}]  max={b_max:.3f} (r{b_regime})")

        # Period-by-period for typical and spike
        if name in ['typical', 'spike']:
            print(f"\n  Period-by-period:")
            print(f"  {'t':>3s}  {'Price':>8s}  {'DP_kW':>7s}  {'DP_rev':>7s}  "
                  f"{'PO_kW':>7s}  {'PO_rev':>7s}")
            for t in range(48):
                print(f"  {t:3d}  {prices[t]:8.1f}  "
                      f"{result_dp['dispatch'][t]:+7.1f}  "
                      f"{result_dp['revenue'][t]:7.2f}  "
                      f"{result_pomdp['dispatch'][t]:+7.1f}  "
                      f"{result_pomdp['revenue'][t]:7.2f}")

    # --- Summary table ---
    print(f"\n{'='*80}")
    print(f"=== Summary: Value of Perfect Information ===")
    print(f"{'='*80}")
    print(f"\n  {'Day':>8s}  {'Date':>12s}  {'Type':>8s}  {'Det DP':>10s}  "
          f"{'POMDP':>10s}  {'Capture':>8s}  {'Info Value':>10s}")
    print(f"  {'-'*8}  {'-'*12}  {'-'*8}  {'-'*10}  "
          f"{'-'*10}  {'-'*8}  {'-'*10}")
    
    for r in results_table:
        print(f"  {r['name']:>8s}  {r['date']:>12s}  {r['day_type']:>8s}  "
              f"${r['dp_revenue']:>9.2f}  ${r['pomdp_revenue']:>9.2f}  "
              f"{r['capture_rate']:>7.1f}%  ${r['info_value']:>9.2f}")

    # --- Annual estimate ---
    # Using your existing day counts per revenue bucket
    day_counts = {
        'low': 51, 'typical': 227, 'high': 52, 'vhigh': 26, 'spike': 10
    }

    print(f"\n=== Estimated Annual Value of Information ===\n")
    total_dp_annual = 0
    total_pomdp_annual = 0
    
    print(f"  {'Day':>8s}  {'Days/yr':>7s}  {'DP/day':>8s}  {'POMDP/day':>9s}  "
          f"{'DP Annual':>10s}  {'POMDP Annual':>12s}  {'Info Annual':>11s}")
    
    for r in results_table:
        name = r['name']
        if name in day_counts:
            n_days = day_counts[name]
            dp_annual = r['dp_revenue'] * n_days
            pomdp_annual = r['pomdp_revenue'] * n_days
            info_annual = r['info_value'] * n_days
            total_dp_annual += dp_annual
            total_pomdp_annual += pomdp_annual
            
            print(f"  {name:>8s}  {n_days:>7d}  ${r['dp_revenue']:>7.2f}  "
                  f"${r['pomdp_revenue']:>8.2f}  ${dp_annual:>9.0f}  "
                  f"${pomdp_annual:>11.0f}  ${info_annual:>10.0f}")

    total_info = total_dp_annual - total_pomdp_annual
    capture_annual = total_pomdp_annual / total_dp_annual * 100 if total_dp_annual > 0 else 0
    
    print(f"  {'':>8s}  {'':>7s}  {'':>8s}  {'':>9s}  {'-'*10}  {'-'*12}  {'-'*11}")
    print(f"  {'TOTAL':>8s}  {'366':>7s}  {'':>8s}  {'':>9s}  "
          f"${total_dp_annual:>9.0f}  ${total_pomdp_annual:>11.0f}  "
          f"${total_info:>10.0f}")
    print(f"\n  Annual capture rate: {capture_annual:.1f}%")
    print(f"  Annual value of perfect information: ${total_info:,.0f}")

    # --- Restore stdout ---
    sys.stdout = sys.__stdout__
    log_file.close()
    print(f"Output saved to data/stochastic/pomdp_test_output.log")