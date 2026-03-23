"""
Regime classification for stochastic DP.

Classifies each day into 5 price regimes using k-means on
(log spread, log mean) of daily prices.
"""

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# Revenue boundaries (A$/day) - same as existing analysis
REGIME_NAMES = ['low', 'typical', 'high', 'vhigh', 'spike']
N_REGIMES = 5

def load_price_features(price_csv_path):
    """
    Load full-year prices and compute daily features.
    
    Args:
        price_csv_path: path to nem_prices_NSW1_clean.csv
    
    Returns:
        DataFrame with columns: date, mean_price, spread, max_price,
                                min_price, n_periods
    """
    df = pd.read_csv(price_csv_path)
    df['datetime'] = pd.to_datetime(df['datetime'])
    df['date'] = df['datetime'].dt.date
    
    daily = df.groupby('date').agg(
        mean_price=('price', 'mean'),
        max_price=('price', 'max'),
        min_price=('price', 'min'),
        n_periods=('price', 'size')
    ).reset_index()
    
    daily['spread'] = daily['max_price'] - daily['min_price']
    
    # Keep only complete days (48 half-hour periods)
    daily = daily[daily['n_periods'] == 48].reset_index(drop=True)
    daily['date'] = pd.to_datetime(daily['date'])
    
    return daily


def classify_days(
        price_csv_path: str, annual_results_path: str = None,
        n_regimes: int = N_REGIMES, random_state: int = 42):
    """
    Classify days into regimes using k-means on (log spread, log mean).
    
    Args:
        price_csv_path: path to nem_prices_NSW1_clean.csv
        annual_results_path: path to annual_dispatch_results.csv (optional,
                            for merging DP revenue into output)
        n_regimes: number of regimes
        random_state: k-means seed for reproducibility
    
    Returns:
        day_df: DataFrame with columns: date, mean_price, spread, 
                regime_idx, regime, day_type, is_weekday
                (plus dp_revenue if annual_results_path provided)
        kmeans_info: dict with scaler, kmeans model, and cluster stats
    """
    daily = load_price_features(price_csv_path)

    # --- Log-transform features ---
    # shift mean_price so log is defined (some days may have negative mean)
    shift = 0
    if daily['mean_price'].min() <= 0:
        shift = abs(daily['mean_price'].min()) + 1
    
    features = np.column_stack([                        # each column = one feature
        np.log1p(daily['spread'].values),               # log(1 + x)
        np.log1p(daily['mean_price'].values + shift)
    ])

    # --- Standardise ---
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)

    # --- K-means ---
    kmeans = KMeans(n_clusters=n_regimes, random_state=random_state, 
                    n_init=20)      # K‑means will run 20 separate initialisations
                                    # Each run starts with different random centroid positions

    labels = kmeans.fit_predict(features_scaled)

    # --- Sort clusters by spread (ascending) ---
    # So regime 0 = smallest spread, regime 4 = largest spread
    cluster_spreads = []
    
    # Compute mean spread for each cluster
    for c in range(n_regimes):
        mask = labels == c
        cluster_spreads.append(daily.loc[mask, 'spread'].mean())    # eg, cluster_spreads = [120, 15, 300, 45, 600]

    sort_order = np.argsort(cluster_spreads)                        # eg, sort_order = [1, 3, 0, 2, 4]
    label_map = {old: new for new, old in enumerate(sort_order)}    # eg, { 1: 0, 3: 1, 0: 2, 2: 3, 4: 4}
    sorted_labels = np.array([label_map[l] for l in labels] )       # eg, [2, 0, 3, 1, 4] represents [high, low, vhigh, typical, spike]

    # --- Build output DataFrame ---
    daily['regime_idx'] = sorted_labels
    daily['regime'] = daily['regime_idx'].map(dict(enumerate(REGIME_NAMES)))
    daily['is_weekday'] = daily['date'].dt.weekday < 5
    daily['day_type'] = np.where(daily['is_weekday'], 'weekday', 'weekend')

    # --- Merge DP revenue if available  ---
    if annual_results_path is not None:
        results = pd.read_csv(annual_results_path)
        results['date'] = pd.to_datetime(results['date'])
        daily = daily.merge(
            results[['date', 'dp_revenue']], on='date', how='left'
        )

    # --- Cluster info for inspection ---
    kmeans_info = {
        'scaler': scaler,
        'kmeans': kmeans,
        'shift': shift,
        'cluster_stats': []
    }

    for idx in range(n_regimes):
        mask = daily['regime_idx'] == idx
        subset = daily[mask]
        stats = {
            'regime': REGIME_NAMES[idx],
            'count': len(subset),
            'mean_price': subset['mean_price'].mean(),
            'mean_spread': subset['spread'].mean(),
            'min_spread': subset['spread'].min(),
            'max_spread': subset['spread'].max(),
        }
        if 'dp_revenue' in subset.columns:
            stats['mean_dp_revenue'] = subset['dp_revenue'].mean()
        kmeans_info['cluster_stats'].append(stats)
    
    columns = ['date', 'mean_price', 'spread', 'regime_idx', 'regime',
               'day_type', 'is_weekday']
    if 'dp_revenue' in daily.columns:
        columns.append('dp_revenue')
    
    return daily[columns], kmeans_info


def compute_priors(day_df: pd.DataFrame, smooth_alpha=0.5) -> dict:
    """
    Compute regime prior probabilities conditional on day type.
    Laplace Smoothing: 
        Pretend you observed a tiny bit of every category, 
        even if the actual count was zero.

    \hat{p}_i = (c_i + α ) / ( N + α K}
    - c_i = count of category i
    - N = total observations
    - K = number of categories
    - α  = smoothing constant (often 1, 0.5, or 0.1)

    Args:
        day_df: output of classify_days()
        
    Returns:
        dict with keys 'weekday' and 'weekend', each a length-5 array
        summing to 1
    """
    priors = {}

    for day_type in ['weekday', 'weekend']:
        mask = day_df['day_type'] == day_type
        subset = day_df[mask]
        total = len(subset)

        counts = np.zeros(5)
        for idx in range(5):
            counts[idx] = (subset['regime_idx'] == idx).sum()

        # Laplace smoothing: add alpha to each count
        counts += smooth_alpha
        priors[day_type] = counts / total

    return priors


def summary(day_df, priors, kmeans_info):
    """Print regime classification summary."""
    print("=== Regime Classification (K-Means on log spread x log mean) ===\n")
    
    # Cluster statistics
    print("Regime statistics:")
    print(f"  {'Regime':>8s}  {'Days':>5s}  {'Mean Price':>10s}  "
          f"{'Mean Spread':>11s}  {'Spread Range':>16s}", end='')
    if 'mean_dp_revenue' in kmeans_info['cluster_stats'][0]:
        print(f"  {'Mean DP Rev':>11s}", end='')
    print()
    
    for stats in kmeans_info['cluster_stats']:
        print(f"  {stats['regime']:>8s}  {stats['count']:5d}  "
              f"${stats['mean_price']:9.1f}  "
              f"${stats['mean_spread']:10.1f}  "
              f"[${stats['min_spread']:.0f}–${stats['max_spread']:.0f}]",
              end='')
        if 'mean_dp_revenue' in stats:
            print(f"  ${stats['mean_dp_revenue']:10.1f}", end='')
        print()
    
    # Weekday/weekend breakdown
    print(f"\nWeekday/weekend breakdown:")
    for idx, name in enumerate(REGIME_NAMES):
        count = (day_df['regime_idx'] == idx).sum()
        weekday = ((day_df['regime_idx'] == idx) & day_df['is_weekday']).sum()
        weekend = count - weekday
        print(f"  {name:>8s}: {count:3d} days  "
              f"({weekday:3d} weekday, {weekend:3d} weekend)")
    
    total = len(day_df)
    wd = day_df['is_weekday'].sum()
    we = total - wd
    print(f"\n  Total: {total} days  ({wd} weekday, {we} weekend)")
    
    # Priors
    print("\nRegime priors P(regime | day_type):")
    print(f"  {'Regime':>8s}  {'Weekday':>8s}  {'Weekend':>8s}")
    for idx, name in enumerate(REGIME_NAMES):
        print(f"  {name:>8s}  {priors['weekday'][idx]:8.3f}  "
              f"{priors['weekend'][idx]:8.3f}")


if __name__ == '__main__':
    day_df, kmeans_info = classify_days(
        price_csv_path='data/aemo/nem_prices_NSW1_clean.csv',
        annual_results_path='data/pypsa/annual_dispatch_results.csv'
    )
    priors = compute_priors(day_df)
    summary(day_df, priors, kmeans_info)
    typical = day_df[day_df['regime_idx'] == 1]
    print("Typical days with spread > $500:")
    print(typical[typical['spread'] > 500][['date', 'mean_price', 'spread', 'dp_revenue']])