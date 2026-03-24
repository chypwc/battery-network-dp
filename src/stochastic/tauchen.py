"""
Regime-specific Tauchen price transition matrices.

Estimates P_theta(j' | j, t) for each regime and time step,
using a common percentile-based price grid across all regimes.
"""

import numpy as np
import pandas as pd 
from src.stochastic.regime import N_REGIMES

N_MOMENTUM = 3
MOMENTUM_NAMES = ['falling', 'stable', 'rising']

def build_price_grid(all_prices: np.ndarray, n_bulk_bins: int=20, 
                     tail_edges: list | None = None):
    """
    Hybrid price grid: percentile-based for bulk prices,
    hand-placed for the upper tail.
    
    Args:
        all_prices: 2D array, shape (n_days, 48)
        n_bulk_bins: number of percentile-based bins for the bulk
        tail_edges: list of additional edge values for the upper tail
                    Default: [300, 500, 1000, 3000, 17500]
    
    Returns:
        bin_edges: array of length n_bins + 1 (strictly increasing)
        bin_mids: array of length n_bins (midpoint of each bin)
    """
    if tail_edges is None:
        tail_edges = [300, 500, 1000, 3000, 17500]

    flat = all_prices.flatten()
    flat = flat[~np.isnan(flat)]

    # Bulk: prices below the first tail edge
    tail_start = tail_edges[0]
    bulk_prices = flat[flat < tail_start]

    # Percentile-based edges for the buld: n_bulk_bins + 1 points from 0th to 100th
    pct_points = np.linspace(0, 100, n_bulk_bins + 1)    # If n_bins=20, pct_points = [0, 5, 10, 15, ..., 95, 100]
    bulk_edges = np.percentile(bulk_prices, pct_points)     

    # Extend edges slightly so no price falls outside
    bulk_edges[0] = flat.min() - 1

    # Combine: bulk edges (excluding the last, which is ~300) + tail edges
    # The last bulk edge should be tail_start
    bulk_edges[-1] = tail_start

    # Full edge array
    all_edges = np.concatenate([bulk_edges, tail_edges[1:]])

    # Extend upper bound
    all_edges[-1] = flat.max() + 1

    # Ensure strictly increasing (duplicates possible if many
    # prices are identical, e.g., many zeros)
    for i in range(1, len(all_edges)):
        if all_edges[i] <= all_edges[i-1]:
            all_edges[i] = all_edges[i-1] + 0.01
        
    # Midpoints: representative prices for each bin
    bin_mids = 0.5 * (all_edges[:-1] + all_edges[1:])

    return all_edges, bin_mids


def get_bin_index(price: float | np.ndarray, bin_edges: np.ndarray) -> int |  np.ndarray:
    """
    Map a price (scalar or array) to bin index.
    
    Bin j contains prices where bin_edges[j] <= price < bin_edges[j+1].
    
    Args:
        price: scalar or array
        bin_edges: array of length n_bins + 1
    
    Returns:
        integer bin index, 0 to n_bins - 1
    """
    # searchsorted finds the insertion position where price would fit to keep bin_edges sorted
    # Using side='right' ensures: prices equal to an edge go into the higher bin
    # Subtract 1 to get the bin index
    idx = np.searchsorted(bin_edges, price, side='right') - 1
    # largest valid bin index = n_bins − 1 = len(bin_edges) − 2
    idx = np.clip(idx, 0, len(bin_edges) - 2)
    return idx


def build_price_matrix(price_csv_path: str, day_df: np.ndarray):
    """
    Build a (n_days, 48) matrix of half-hour prices, aligned with day_df.
    
    Each row is one day's 48 half-hour prices in chronological order.
    Days without exactly 48 prices are marked invalid.
    
    Args:
        price_csv_path: path to nem_prices_NSW1_clean.csv
        day_df: output of regime.classify_days(), must have 'date' column
    
    Returns:
        price_matrix: array of shape (n_days, 48)
        valid_mask: boolean array of length n_days
    """
    price_df = pd.read_csv(price_csv_path)
    price_df['datetime'] = pd.to_datetime(price_df['datetime'])
    price_df['date'] = price_df['datetime'].dt.date
    
    dates = pd.to_datetime(day_df['date']).dt.date.values
    n_days = len(dates)
    price_matrix = np.full((n_days, 48), np.nan)
    valid_mask = np.zeros(n_days, dtype=bool)

    # Group prices by date for efficient lookup
    grouped = price_df.groupby('date')

    for i, date in enumerate(dates):
        if date in grouped.groups:
            day_prices = grouped.get_group(date)['price'].values
            if len(day_prices) == 48:
                price_matrix[i] = day_prices
                valid_mask[i] = True
            elif len(day_prices) > 48:
                # Take first 48 if there are extras
                price_matrix[i] = day_prices[:48]    
                valid_mask[i] = True
    
    return price_matrix, valid_mask


def build_transition_matrices(
        price_matrix: np.ndarray, day_regimes: np.ndarray,
        bin_edges: np.ndarray, n_regimes: int = N_REGIMES, 
        smooth_alpha: float = 0.1) -> np.ndarray:
    """
    Estimate P_theta(j' | j, t) for each regime and time step.
    
    For each regime, counts half-hour price bin transitions across
    all days in that regime, then normalises with Laplace smoothing.
    
    Args:
        price_matrix: array of shape (n_days, 48)
        day_regimes: array of length n_days, values 0 to n_regimes-1
        bin_edges: from build_price_grid(), length n_bins + 1
        n_regimes: number of regimes
        smooth_alpha: Laplace smoothing pseudocount
    
    Returns:
        trans: array of shape (n_regimes, 47, n_bins, n_bins)
               trans[theta, t, j, j'] = P_theta(j' | j, t)
    """
    n_bins = len(bin_edges) - 1
    n_steps = 47    # t = 0, ..., 46 (transitions to t+1)
    n_days = price_matrix.shape[0]

    # Count transitions
    counts = np.zeros((n_regimes, n_steps, n_bins, n_bins))

    for d in range(n_days):                 # iterate over each day
        theta = day_regimes[d]              # which regime is this day? 
        prices_today = price_matrix[d]      # 48 half-hour prices

        # Skip days with NaN
        if np.any(np.isnan(prices_today)):
            continue

        # Bin all 48 prices at once
        # bins is an array of 48 integers, each 0 to n_bins-1
        bins = get_bin_index(prices_today, bin_edges)

        # Count each transition
        for t in range(n_steps):            # t = 0, 1, ..., 46
            j = bins[t]                     # bin at time t
            j_next = bins[t + 1]            # bin at time t+1
            counts[theta, t, j, j_next] += 1

    # Normalise with Laplace smoothing
    smoothed = counts + smooth_alpha
    # Normalise over j'
    row_sums = smoothed.sum(axis=3, keepdims=True)
    # Safety: avoid division by zero (shouldn't happen with smoothing)
    row_sums[row_sums == 0] = 1
    trans = smoothed / row_sums

    return trans


def validate_transitions(
        trans: np.ndarray, bin_edges: np.ndarray,
        bin_mids: np.ndarray, day_regimes: np.ndarray, 
        regime_names: np.ndarray
):
    """
    Check transition matrices for correctness and sparsity.
    """
    n_regimes, n_steps, n_bins, _ = trans.shape     # trans[theta, t, j, j'] = P_theta(j' | j, t)

    print("=== Transition Matrix Validation ===\n")

    for theta in range(n_regimes):
        name = regime_names[theta]
        n_days_regime = (day_regimes == theta).sum()

        # Row sums should be 1.0. 
        # - axis=2 = sum over next‑bin j′
        row_sums = trans[theta].sum(axis=2)     # trans[theta] has shape (47, n_bins, n_bins)
        max_row_err = np.max(np.abs(row_sums - 1.0))

        # Self-transition: P(stay in same bin) 
        # On average, how sticky is this regime?
        self_trans = np.array([
            np.mean([trans[theta, t, j, j] for j in range(n_bins)])
            for t in range(n_steps)
        ]).mean()

        print(f"  {name:>8s}:  {n_days_regime:3d} days,  "
              f"row_sum_err = {max_row_err:.2e},  "
              f"mean self-transition = {self_trans:.3f}")
        
    # Price grid summary
    widths = np.diff(bin_edges)
    print(f"\n  Price grid: {n_bins} bins")
    print(f"  Range: [{bin_edges[0]:.1f}, {bin_edges[-1]:.1f}] A$/MWh")
    print(f"  Bin widths: min={widths.min():.1f}, "
          f"median={np.median(widths):.1f}, "
          f"max={widths.max():.1f} A$/MWh")
    
    # Print the grid
    print(f"\n  Bin edges:")
    for i in range(len(bin_mids)):
        print(f"    Bin {i:2d}: [{bin_edges[i]:>9.1f}, "
              f"{bin_edges[i+1]:>9.1f})  "
              f"mid = {bin_mids[i]:>9.1f}")
        

def get_momentum_idx(j_now, j_prev):
    """
    Discretise price momentum into 3 categories. 
    Works with scalars or arrays.
    
    Args:
        j_now: current price bin index
        j_prev: previous price bin index
    
    Returns:
        0 = falling (dropped 2+ bins)
        1 = stable  (within 1 bin)
        2 = rising  (rose 2+ bins)
    """
    diff = np.asarray(j_now) - np.asarray(j_prev)
    result = np.ones_like(diff)          # default: stable (1)
    result[diff <= -2] = 0               # falling
    result[diff >= 2] = 2                # rising
    return int(result) if result.ndim == 0 else result


def build_momentum_transition_matrices(
        price_matrix, day_regimes, bin_edges,
        n_regimes=N_REGIMES, n_momentum=N_MOMENTUM,
        smooth_alpha=0.1,
):
    """
    Estimate P_theta(j' | j, m, t) for each regime, momentum, and time step.
    
    Args:
        price_matrix: (n_days, 48)
        day_regimes: (n_days,)
        bin_edges: (n_bins + 1,)
        n_regimes: number of regimes
        n_momentum: number of momentum bins (3)
        smooth_alpha: Laplace smoothing
    
    Returns:
        trans: shape (n_regimes, 47, n_bins, n_momentum, n_bins)
               trans[theta, t, j, m, j'] = P_theta(j' | j, m, t)
    """
    n_bins = len(bin_edges) - 1
    n_steps = 47
    n_days = price_matrix.shape[0]

    counts = np.zeros((n_regimes, n_steps, n_bins, n_momentum, n_bins))

    for d in range(n_days):
        theta = day_regimes[d]
        prices = price_matrix[d]
        if np.any(np.isnan(prices)):
            continue

        # Bin all 48 prices at once
        bins = get_bin_index(prices, bin_edges)     # shape (48,)

        # Momentum for all 47 transitions at once
        # m[t] momentum at time t, based on bins[t] - bins[t-1]
        # t=0: no previous price, default to stable (1)
        m = np.ones(n_steps, dtype=int)             # shape (47,) default stable
        m[1:] = get_momentum_idx(bins[1:-1], bins[:-2])     # t = 1..46

        # Current bin, next bin for all transitions
        # Current bin, next bin for all transitions
        j_all = bins[:-1]                           # shape (47,)  bins at t
        j_next_all = bins[1:]                       # shape (47,)  bins at t+1
        t_all = np.arange(n_steps)                  # shape (47,)  time indices
        
        # Increment counts using advanced indexing
        # counts[theta, t, j, m, j'] += 1 for all t at once
        np.add.at(
            counts,
            (theta, t_all, j_all, m, j_next_all),
            1
        )

        # Normalise: for each (theta, t, j, m), normalise over j'
    smoothed = counts + smooth_alpha
    row_sums = smoothed.sum(axis=4, keepdims=True)
    row_sums[row_sums == 0] = 1
    trans = smoothed / row_sums
    
    return trans


if __name__ == '__main__':
    from src.stochastic.regime import classify_days, REGIME_NAMES, N_REGIMES
    
    # --- Load data ---
    day_df, kmeans_info = classify_days(
        price_csv_path='data/aemo/nem_prices_NSW1_2018_2023_clean.csv',
        annual_results_path='data/pypsa/annual_dispatch_results.csv'
    )
    
    # --- Build price matrix ---
    price_matrix, valid_mask = build_price_matrix(
        'data/aemo/nem_prices_NSW1_2018_2023_clean.csv', day_df
    )
    print(f"Valid days: {valid_mask.sum()} / {len(valid_mask)}")
    
    price_matrix = price_matrix[valid_mask]
    day_regimes = day_df['regime_idx'].values[valid_mask]
    
    # --- Build price grid ---
    bin_edges, bin_mids = build_price_grid(price_matrix, n_bulk_bins=20)
    
    # --- Build standard transition matrices ---
    print("\n=== Standard Transition Matrices ===")
    trans = build_transition_matrices(
        price_matrix, day_regimes, bin_edges,
        n_regimes=N_REGIMES, smooth_alpha=0.1
    )
    print(f"  Shape: {trans.shape}")
    validate_transitions(trans, bin_edges, bin_mids, day_regimes, REGIME_NAMES)
    
    # --- Build momentum transition matrices ---
    print("\n=== Momentum Transition Matrices ===")
    trans_m = build_momentum_transition_matrices(
        price_matrix, day_regimes, bin_edges,
        n_regimes=N_REGIMES, smooth_alpha=0.1
    )
    print(f"  Shape: {trans_m.shape}")
    
    # Validate momentum matrices
    n_regimes, n_steps, n_bins, n_momentum, _ = trans_m.shape
    
    # Check row sums
    row_sums = trans_m.sum(axis=4)
    max_err = np.max(np.abs(row_sums - 1.0))
    print(f"  Row sum error: {max_err:.2e}")
    
    # Self-transition by momentum state
    print(f"\n  Mean self-transition by momentum:")
    print(f"  {'Regime':>8s}  {'Falling':>8s}  {'Stable':>8s}  {'Rising':>8s}")
    for theta in range(N_REGIMES):
        name = REGIME_NAMES[theta] if theta < len(REGIME_NAMES) else f'r{theta}'
        self_trans = []
        for mi in range(n_momentum):
            st = np.mean([
                trans_m[theta, t, j, mi, j]
                for t in range(n_steps)
                for j in range(n_bins)
            ])
            self_trans.append(st)
        print(f"  {name:>8s}  {self_trans[0]:>8.3f}  {self_trans[1]:>8.3f}  "
              f"{self_trans[2]:>8.3f}")
    
    # Count observations per momentum state
    print(f"\n  Transition counts by momentum (before smoothing):")
    print(f"  {'Regime':>8s}  {'Falling':>8s}  {'Stable':>8s}  {'Rising':>8s}  {'Total':>8s}")
    
    # Recount to check distribution
    n_days = price_matrix.shape[0]
    m_counts = np.zeros((N_REGIMES, n_momentum))
    for d in range(n_days):
        theta = day_regimes[d]
        if np.any(np.isnan(price_matrix[d])):
            continue
        bins = get_bin_index(price_matrix[d], bin_edges)
        m = np.ones(47, dtype=int)
        m[1:] = get_momentum_idx(bins[1:-1], bins[:-2])
        for mi in range(n_momentum):
            m_counts[theta, mi] += (m == mi).sum()
    
    for theta in range(N_REGIMES):
        name = REGIME_NAMES[theta] if theta < len(REGIME_NAMES) else f'r{theta}'
        total = m_counts[theta].sum()
        print(f"  {name:>8s}  {m_counts[theta, 0]:>8.0f}  "
              f"{m_counts[theta, 1]:>8.0f}  {m_counts[theta, 2]:>8.0f}  "
              f"{total:>8.0f}")
    
    # Compare: does momentum-conditional differ from unconditional?
    print(f"\n  Divergence: momentum-conditional vs unconditional")
    print(f"  (KL divergence averaged over regimes, time steps, price bins)")
    print(f"  {'Regime':>8s}  {'Falling':>10s}  {'Stable':>10s}  {'Rising':>10s}")
    
    for theta in range(N_REGIMES):
        name = REGIME_NAMES[theta] if theta < len(REGIME_NAMES) else f'r{theta}'
        kl_by_m = []
        for mi in range(n_momentum):
            kl_sum = 0
            count = 0
            for t in range(n_steps):
                for j in range(n_bins):
                    p = trans_m[theta, t, j, mi, :]   # momentum-conditional
                    q = trans[theta, t, j, :]          # unconditional
                    # KL(p || q), avoiding log(0)
                    mask = (p > 1e-10) & (q > 1e-10)
                    if mask.sum() > 0:
                        kl = np.sum(p[mask] * np.log(p[mask] / q[mask]))
                        kl_sum += kl
                        count += 1
            kl_avg = kl_sum / count if count > 0 else 0
            kl_by_m.append(kl_avg)
        print(f"  {name:>8s}  {kl_by_m[0]:>10.4f}  {kl_by_m[1]:>10.4f}  "
              f"{kl_by_m[2]:>10.4f}")