"""
Bayesian belief updating for the POMDP battery dispatch.

The agent maintains a belief vector b over 5 price regimes,
updated each period using Tauchen transition likelihoods.
"""

import numpy as np
from src.stochastic.regime import N_REGIMES


def build_marginal_distributions(
        price_matrix: np.ndarray, day_regimes: np.ndarray,
        bin_edges: np.ndarray, n_regimes: int = N_REGIMES, 
        smooth_alpha: float = 0.1,
):
    """
    Estimate P_theta(j | t) — the marginal probability of price bin j
    at time step t under regime theta.
    
    Used for the first belief update at t=0 (no previous price).
    
    Args:
        price_matrix: array of shape (n_days, 48)
        day_regimes: array of length n_days, values 0 to n_regimes-1
        bin_edges: from build_price_grid()
        n_regimes: number of regimes
        smooth_alpha: Laplace smoothing
    
    Returns:
        marginal: array of shape (n_regimes, 48, n_bins)
                  marginal[theta, t, j] = P_theta(j | t)
    """
    from src.stochastic.tauchen import get_bin_index

    n_bins = len(bin_edges) - 1
    n_days = price_matrix.shape[0]

    counts = np.zeros((n_regimes, 48, n_bins))

    for d in range(n_days):
        theta = day_regimes[d]
        if np.any(np.isnan(price_matrix[d])):
            continue
        bins = get_bin_index(price_matrix[d], bin_edges)
        for t in range(48):
            counts[theta, t, bins[t]] += 1

    # Normalise with Laplace smoothing
    smoothed = counts + smooth_alpha
    row_sums = smoothed.sum(axis=2, keepdims=True)
    marginal = smoothed / row_sums

    return marginal


def belief_update_from_transition(belief, trans_slice_j_next, fallback=None):
    """
    Core belief update: b'(theta) ∝ b(theta) * P_theta(j' | j, t)
    
    Args:
        belief: current belief, shape (n_regimes,)
        trans_slice_j_next: P_theta(j' | j, t) for each theta, shape (n_regimes,)
        fallback: belief to use if normalisation fails
    
    Returns:
        updated belief, shape (n_regimes,)
    """
    b_new = belief * trans_slice_j_next
    b_sum = b_new.sum()
    if b_sum > 0:
        return b_new / b_sum
    
    # Fallback: if all likelihoods are zero, keep current belief
    return belief.copy()


def update_belief(b, j_now, j_prev, t, trans, marginal=None, momentum=None):
    """
    Bayesian belief update after observing price bin j_now at time t.
    
    If t == 0 (no previous price), uses marginal distribution P_theta(j | t).
    If t > 0, uses transition likelihood P_theta(j_now | j_prev, t-1).
    
    Note on time indexing:
        b_{-1} is the prior (from calendar, before any prices).
        b_0 is the first updated belief (after seeing p_0).
        b_t is the belief used for dispatch at period t.
        
        trans[theta, t, j, j'] is the transition from period t to t+1.
        So the transition that produces price at period t is
        trans[theta, t-1, j_prev, j_now].


    Args:
        b: current belief vector, shape (n_regimes,)
        j_now: current price bin index
        j_prev: previous price bin index (ignored if t == 0)
        t: current time step (0 to 47)
        trans: transition matrices, shape (n_regimes, 47, n_bins, n_bins)
        marginal: marginal distributions, shape (n_regimes, 48, n_bins)
                  Required if t == 0.
        momentum: momentum index at time t-1 (required if trans is 5D)
                  Ignored if t == 0.
    
    Returns:
        b_new: updated belief vector, shape (n_regimes,)
    """
    # n_regimes = len(b)

    if t == 0:
        # First observation: use marginal likelihood
        # P_theta (j_now | t=0)
        likelihoods = marginal[:, 0, j_now]
    else:
        if trans.ndim == 5:
            # Momentum trans: marginalise over momentum
            # trans[:, t-1, j_prev, momentum, j_now] has shape (n_regimes, )
            likelihoods = trans[:, t - 1, j_prev, momentum, j_now]
        else:
            # Subsequent observations: use transition likelihood
            # P_theta(j_now | j_prev, t-1)
            # trans[theta, t-1, j_prev, j_now] is the probability of 
            # transitioning to j_now from j_prev between t-1 and t
            likelihoods = trans[:, t - 1, j_prev, j_now]

    return belief_update_from_transition(b, likelihoods)


def build_belief_grid(priors, n_regimes=N_REGIMES):
    """
    Build a discrete grid of belief points on the simplex.
    
    Includes:
    - Pure beliefs (corners): 100% on one regime
    - Dominant beliefs at 90% confidence
    - Dominant beliefs at 70% confidence  
    - The weekday and weekend priors
    - Uniform belief
    
    Args:
        priors: dict with keys 'weekday' and 'weekend',
                each a length-5 array
        n_regimes: number of regimes
    
    Returns:
        belief_grid: array of shape (n_points, n_regimes)
        grid_labels: list of string labels for each point
    """
    beliefs = []
    labels = []

    # 1. Pure beliefs (corners of simplex)
    for theta in range(n_regimes):
        b = np.zeros(n_regimes)
        b[theta] = 1.0
        beliefs.append(b)
        labels.append(f'pure_{theta}')

    # 2. Dominant beliefs at 90% confidence
    #    b(theta) = 0.9, rest split equally: (1-0.9) / (n_regimes-1)
    #   e.g., [0.9, 0.025, 0.025, 0.025, 0.025]
    for theta in range(n_regimes):
        b = np.full(n_regimes, 0.1 / (n_regimes - 1))
        b[theta] = 0.9
        beliefs.append(b)
        labels.append(f'dom90_{theta}')

    # 3. Dominant beliefs at 70% confidence
    #    b(theta) = 0.7, rest split equally: (1-0.7) / (n_regimes-1)
    for theta in range(n_regimes):
        b = np.full(n_regimes, 0.3 / (n_regimes - 1))
        b[theta] = 0.7
        beliefs.append(b)
        labels.append(f'dom70_{theta}')

    # 4. Pairwise 50/50 mixtures between adjacent regimes
    # for i in range(n_regimes - 1):
    #     b = np.full(n_regimes, 0.02)
    #     remaining = 1.0 - 0.02 * (n_regimes - 2)
    #     b[i] = remaining / 2
    #     b[i + 1] = remaining / 2
    #     beliefs.append(b)
    #     labels.append(f'mix_{i}_{i+1}')

    # 5. priors
    beliefs.append(priors['weekday'].copy())
    labels.append('prior_weekday')
    beliefs.append(priors['weekend'].copy())
    labels.append('prior_weekend')

    # 6. Uniform
    beliefs.append(np.ones(n_regimes) / n_regimes)
    labels.append('uniform')

    beliefs_grid = np.array(beliefs)
    return beliefs_grid, labels


def nearest_belief(b, belief_grid):
    """
    Find the nearest grid point to belief b using L1 distance.
    
    Args:
        b: belief vector, shape (n_regimes,)
        belief_grid: array of shape (n_points, n_regimes)
    
    Returns:
        index: integer index into belief_grid
    """
    # d(b, b') = \sum_{\theta=0}^{4} |b(\theta) - b'(\theta)|
    distances = np.sum(np.abs(belief_grid - b), axis=1)
    return np.argmin(distances)


def test_belief_convergence(price_matrix, day_regimes, day_df,
                             bin_edges, trans, marginal, priors,
                             regime_names, n_test=3):
    """
    Test that beliefs converge to the correct regime on known days.
    
    For a few days from each regime, run the Bayesian update through
    all 48 periods and check that the final belief concentrates on
    the correct regime.
    
    Args:
        price_matrix: (n_days, 48) array
        day_regimes: regime index per day
        day_df: DataFrame with date, regime info
        bin_edges: price bin edges
        trans: transition matrices (n_regimes, 47, n_bins, n_bins)
        marginal: marginal distributions (n_regimes, 48, n_bins)
        priors: dict with 'weekday' and 'weekend' priors
        regime_names: list of regime name strings
        n_test: number of days to test per regime
    """
    from src.stochastic.tauchen import get_bin_index
    n_regimes = trans.shape[0]
    
    print("=== Belief Convergence Test ===\n")
    print(f"  {'Regime':>8s}  {'Date':>12s}  {'DayType':>8s}  "
          f"{'Periods to 90%':>14s}  {'Final belief':>40s}")
    
    for theta in range(n_regimes):
        # Get days in this regime
        mask = day_regimes == theta
        regime_days = np.where(mask)[0]

        if len(regime_days) == 0:
            continue

        # Test up to n_test days
        test_indices = regime_days[:n_test]

        for d in test_indices:
            prices = price_matrix[d]
            if np.any(np.isnan(prices)):
                continue

            bins = get_bin_index(prices, bin_edges)

            # Determine day type for prior
            is_weekday = day_df.iloc[d]['is_weekday']
            day_type = 'weekday' if is_weekday else 'weekend'
            date_str = str(day_df.iloc[d]['date'])[:10]

            # Run belief update through all periods
            b = priors[day_type].copy()
            periods_to_90 = None

            for t in range(48):
                j_now = bins[t]
                j_prev = bins[t-1] if t > 0 else None
                b = update_belief(b, j_now, j_prev, t, trans, marginal)

                # Check if correct regime exceeds 90%
                if periods_to_90 is None and b[theta] >= 0.9:
                    periods_to_90 = t + 1

            # Format final belief
            belief_str = '  '.join(f'{x:.3f}' for x in b)
            periods_str = str(periods_to_90) if periods_to_90 is not None else '>48'

            print(f"  {regime_names[theta]:>8s}  {date_str:>12s}  "
                  f"{day_type:>8s}  {periods_str:>14s}  "
                  f"[{belief_str}]")
            

if __name__ == '__main__':
    from src.stochastic.regime import classify_days, compute_priors, REGIME_NAMES, N_REGIMES
    from src.stochastic.tauchen import (build_price_matrix, build_price_grid,
                                         build_transition_matrices)
    
    # --- Load data ---
    day_df, kmeans_info = classify_days(
        price_csv_path='data/aemo/nem_prices_NSW1_2021_2023_clean.csv',
        annual_results_path='data/pypsa/annual_dispatch_results.csv'
    )
    priors = compute_priors(day_df)
    
    # --- Build price data ---
    price_matrix, valid_mask = build_price_matrix(
        'data/aemo/nem_prices_NSW1_2021_2023_clean.csv', day_df
    )
    price_matrix = price_matrix[valid_mask]
    day_regimes = day_df['regime_idx'].values[valid_mask]
    day_df_valid = day_df[valid_mask].reset_index(drop=True)
    
    # --- Build Tauchen ---
    bin_edges, bin_mids = build_price_grid(price_matrix, n_bulk_bins=20)
    trans = build_transition_matrices(
        price_matrix, day_regimes, bin_edges,
        n_regimes=N_REGIMES, smooth_alpha=0.1
    )
    
    # --- Build marginal distributions ---
    marginal = build_marginal_distributions(
        price_matrix, day_regimes, bin_edges,
        n_regimes=N_REGIMES, smooth_alpha=0.1
    )
    print(f"Marginal distributions shape: {marginal.shape}")
    
    # --- Build belief grid ---
    belief_grid, grid_labels = build_belief_grid(priors)
    print(f"Belief grid: {len(belief_grid)} points")
    for i, (b, label) in enumerate(zip(belief_grid, grid_labels)):
        b_str = '  '.join(f'{x:.3f}' for x in b)
        print(f"  {i:2d}: [{b_str}]  ({label})")
    
    # --- Test nearest belief ---
    print("\n=== Nearest Belief Test ===")
    test_b = priors['weekday']
    idx = nearest_belief(test_b, belief_grid)
    print(f"  Query:   [{' '.join(f'{x:.3f}' for x in test_b)}]")
    print(f"  Nearest: [{' '.join(f'{x:.3f}' for x in belief_grid[idx])}]"
          f"  ({grid_labels[idx]})")
    
    # --- Test belief convergence ---
    print()
    test_belief_convergence(
        price_matrix, day_regimes, day_df_valid,
        bin_edges, trans, marginal, priors,
        REGIME_NAMES, n_test=3
    )
