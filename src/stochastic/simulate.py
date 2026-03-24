"""
Forward simulation of POMDP policy on all days.

Training data: configurable (default 2018-2023)
Test data: 2024
Compares standard vs momentum POMDP.
"""

import numpy as np
import pandas as pd
import time
import os


def simulate_all_days(solver, price_matrix, day_df, priors, V, policy,
                      label='POMDP'):
    """
    Run POMDP simulation on every valid day.
    """
    from src.dp.solver import DPSolver
    
    battery = solver.battery
    dp_solver = DPSolver(
        battery, n_soc=solver.n_soc,
        n_actions=solver.n_actions,
        dispatch_limit=solver.dispatch_limit
    )
    
    n_days = len(price_matrix)
    results = []
    
    start = time.time()
    
    for d in range(n_days):
        prices = price_matrix[d]
        
        if np.any(np.isnan(prices)):
            continue
        
        row = day_df.iloc[d]
        regime_idx = int(row['regime_idx'])
        day_type = row['day_type']
        date_str = str(row['date'])[:10]
        
        b_minus1 = priors[day_type]
        
        result_pomdp = solver.simulate(prices, V, policy, b_minus1)
        result_dp = dp_solver.solve(prices, initial_soc=battery.kwh_rated / 2)
        
        dp_rev = result_dp['total_revenue']
        pomdp_rev = result_pomdp['total_revenue']
        capture = (pomdp_rev / dp_rev * 100) if dp_rev != 0 else 0
        info_value = dp_rev - pomdp_rev
        
        beliefs = result_pomdp['beliefs']
        converge_period = None
        for t in range(48):
            if beliefs[t][regime_idx] >= 0.9:
                converge_period = t
                break
        
        final_correct = beliefs[47][regime_idx]
        
        results.append({
            'date': date_str,
            'regime_idx': regime_idx,
            'day_type': day_type,
            'dp_revenue': dp_rev,
            'pomdp_revenue': pomdp_rev,
            'capture_rate': capture,
            'info_value': info_value,
            'belief_converge_period': converge_period,
            'final_belief_correct': final_correct,
        })
        
        if (d + 1) % 50 == 0:
            elapsed = time.time() - start
            print(f"  [{label}] Day {d+1}/{n_days}  ({elapsed:.1f}s)")
    
    elapsed = time.time() - start
    print(f"  [{label}] Completed {len(results)} days in {elapsed:.1f}s")
    
    return pd.DataFrame(results)


def print_summary(results_df, label):
    """Print quick summary for a configuration."""
    total_dp = results_df['dp_revenue'].sum()
    total_pomdp = results_df['pomdp_revenue'].sum()
    total_info = total_dp - total_pomdp
    capture = total_pomdp / total_dp * 100 if total_dp > 0 else 0
    n_negative = (results_df['pomdp_revenue'] < 0).sum()
    median_converge = results_df['belief_converge_period'].dropna().median()
    n_never = results_df['belief_converge_period'].isna().sum()
    
    print(f"\n  [{label}]")
    print(f"    Annual Det DP:    ${total_dp:>10,.0f}")
    print(f"    Annual POMDP:     ${total_pomdp:>10,.0f}")
    print(f"    Annual info value:${total_info:>10,.0f}")
    print(f"    Capture rate:      {capture:>9.1f}%")
    print(f"    Negative days:     {n_negative:>9d}")
    print(f"    Median converge:   {median_converge:>8.0f}p ({median_converge*0.5:.1f}h)")
    print(f"    Never converge:    {n_never:>9d}")


def print_regime_comparison(std_df, mom_df, regime_names):
    """Print side-by-side regime breakdown."""
    print(f"\n{'='*90}")
    print(f"  {'Regime':>8s}  {'Days':>5s}  "
          f"{'Std Cap':>8s}  {'Mom Cap':>8s}  {'Diff':>6s}  "
          f"{'Std Conv':>8s}  {'Mom Conv':>8s}  "
          f"{'Std Info':>10s}  {'Mom Info':>10s}")
    print(f"{'='*90}")
    
    for idx in sorted(std_df['regime_idx'].unique()):
        s = std_df[std_df['regime_idx'] == idx]
        m = mom_df[mom_df['regime_idx'] == idx]
        
        name = regime_names[idx] if idx < len(regime_names) else f'r{idx}'
        n_days = len(s)
        
        s_cap = s['pomdp_revenue'].sum() / s['dp_revenue'].sum() * 100 if s['dp_revenue'].sum() > 0 else 0
        m_cap = m['pomdp_revenue'].sum() / m['dp_revenue'].sum() * 100 if m['dp_revenue'].sum() > 0 else 0
        diff = m_cap - s_cap
        
        s_conv = s['belief_converge_period'].dropna().median()
        m_conv = m['belief_converge_period'].dropna().median()
        
        s_info = s['info_value'].sum()
        m_info = m['info_value'].sum()
        
        s_conv_str = f"{s_conv:.0f}p" if not np.isnan(s_conv) else "N/A"
        m_conv_str = f"{m_conv:.0f}p" if not np.isnan(m_conv) else "N/A"
        
        print(f"  {name:>8s}  {n_days:5d}  "
              f"{s_cap:>7.1f}%  {m_cap:>7.1f}%  {diff:>+5.1f}%  "
              f"{s_conv_str:>8s}  {m_conv_str:>8s}  "
              f"${s_info:>9.0f}  ${m_info:>9.0f}")
    
    # Totals
    s_total_dp = std_df['dp_revenue'].sum()
    s_total_pomdp = std_df['pomdp_revenue'].sum()
    m_total_pomdp = mom_df['pomdp_revenue'].sum()
    s_cap_total = s_total_pomdp / s_total_dp * 100
    m_cap_total = m_total_pomdp / s_total_dp * 100
    diff_total = m_cap_total - s_cap_total
    
    print(f"  {'-'*88}")
    print(f"  {'TOTAL':>8s}  {len(std_df):5d}  "
          f"{s_cap_total:>7.1f}%  {m_cap_total:>7.1f}%  {diff_total:>+5.1f}%  "
          f"{'':>8s}  {'':>8s}  "
          f"${std_df['info_value'].sum():>9.0f}  ${mom_df['info_value'].sum():>9.0f}")


if __name__ == '__main__':
    import sys
    from src.dp.battery import Battery
    from src.stochastic.regime import (classify_days, compute_priors,
                                        REGIME_NAMES, N_REGIMES)
    from src.stochastic.tauchen import (build_price_matrix, build_price_grid,
                                         build_transition_matrices,
                                         build_momentum_transition_matrices)
    from src.stochastic.belief import (build_marginal_distributions,
                                        build_belief_grid)
    from src.stochastic.solver import POMDPSolver
    
    os.makedirs('data/stochastic', exist_ok=True)
    
    # --- Logging ---
    log_file = open('data/stochastic/pomdp_momentum_comparison.log', 'w')
    
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
    
    # === Configuration ===
    TRAIN_CSV = 'data/aemo/nem_prices_NSW1_2018_2023_clean.csv'
    TEST_CSV = 'data/aemo/nem_prices_NSW1_clean.csv'  # 2024
    ANNUAL_RESULTS = 'data/pypsa/annual_dispatch_results.csv'
    N_ACTIONS = 47
    N_SOC = 81
    
    print(f"=== POMDP Momentum Comparison ===")
    print(f"  Training: {TRAIN_CSV}")
    print(f"  Testing:  {TEST_CSV}")
    print(f"  N_REGIMES: {N_REGIMES}")
    print(f"  N_ACTIONS: {N_ACTIONS}")
    
    battery = Battery(kwh_rated=200, kw_rated=100)
    
    # === Build training data ===
    print(f"\n--- Building training data ---")
    train_day_df, kmeans_info = classify_days(
        price_csv_path=TRAIN_CSV,
        annual_results_path=None
    )
    train_priors = compute_priors(train_day_df)
    
    train_price_matrix, train_valid = build_price_matrix(TRAIN_CSV, train_day_df)
    train_price_matrix = train_price_matrix[train_valid]
    train_regimes = train_day_df['regime_idx'].values[train_valid]
    print(f"  Training days: {train_valid.sum()}")
    
    bin_edges, bin_mids = build_price_grid(train_price_matrix, n_bulk_bins=20)
    
    # Standard transitions
    trans_std = build_transition_matrices(
        train_price_matrix, train_regimes, bin_edges,
        n_regimes=N_REGIMES, smooth_alpha=0.1
    )
    print(f"  Standard trans: {trans_std.shape}")
    
    # Momentum transitions
    trans_mom = build_momentum_transition_matrices(
        train_price_matrix, train_regimes, bin_edges,
        n_regimes=N_REGIMES, smooth_alpha=0.1
    )
    print(f"  Momentum trans: {trans_mom.shape}")
    
    # Marginal (shared)
    marginal = build_marginal_distributions(
        train_price_matrix, train_regimes, bin_edges,
        n_regimes=N_REGIMES, smooth_alpha=0.1
    )
    
    belief_grid, grid_labels = build_belief_grid(train_priors)
    print(f"  Belief grid: {len(belief_grid)} points")
    
    # === Classify test days ===
    print(f"\n--- Classifying test days ---")
    from src.stochastic.regime import load_price_features
    
    test_daily = load_price_features(TEST_CSV)
    
    scaler = kmeans_info['scaler']
    kmeans_model = kmeans_info['kmeans']
    shift = kmeans_info['shift']
    
    test_features = np.column_stack([
        np.log1p(test_daily['spread'].values),
        np.log1p(test_daily['mean_price'].values + shift)
    ])
    test_features_scaled = scaler.transform(test_features)
    test_labels = kmeans_model.predict(test_features_scaled)
    
    cluster_spreads = [s['mean_spread'] for s in kmeans_info['cluster_stats']]
    sort_order = np.argsort(cluster_spreads)
    label_map = {old: new for new, old in enumerate(sort_order)}
    test_labels_sorted = np.array([label_map[l] for l in test_labels])
    
    test_daily['regime_idx'] = test_labels_sorted
    test_daily['regime'] = test_daily['regime_idx'].map(dict(enumerate(REGIME_NAMES)))
    test_daily['is_weekday'] = test_daily['date'].dt.weekday < 5
    test_daily['day_type'] = np.where(test_daily['is_weekday'], 'weekday', 'weekend')
    
    if os.path.exists(ANNUAL_RESULTS):
        results_2024 = pd.read_csv(ANNUAL_RESULTS)
        results_2024['date'] = pd.to_datetime(results_2024['date'])
        test_daily = test_daily.merge(
            results_2024[['date', 'dp_revenue']], on='date', how='left'
        )
    
    test_price_matrix, test_valid = build_price_matrix(TEST_CSV, test_daily)
    test_price_matrix = test_price_matrix[test_valid]
    test_daily_valid = test_daily[test_valid].reset_index(drop=True)
    print(f"  Test days: {len(test_daily_valid)}")
    
    # === Solve and simulate: STANDARD ===
    print(f"\n{'='*60}")
    print(f"=== Configuration 1: Standard (no momentum) ===")
    print(f"{'='*60}")
    
    solver_std = POMDPSolver(
        battery=battery, bin_mids=bin_mids, bin_edges=bin_edges,
        trans=trans_std, marginal=marginal, belief_grid=belief_grid,
        n_soc=N_SOC, n_actions=N_ACTIONS, dispatch_limit=100
    )
    
    start = time.time()
    V_std, policy_std = solver_std.solve()
    print(f"  Solve time: {time.time() - start:.1f}s")
    
    results_std = simulate_all_days(
        solver_std, test_price_matrix, test_daily_valid,
        train_priors, V_std, policy_std, label='Standard'
    )
    results_std.to_csv('data/stochastic/pomdp_annual_standard.csv', index=False)
    print_summary(results_std, 'Standard')
    
    # === Solve and simulate: MOMENTUM ===
    print(f"\n{'='*60}")
    print(f"=== Configuration 2: Momentum ===")
    print(f"{'='*60}")
    
    solver_mom = POMDPSolver(
        battery=battery, bin_mids=bin_mids, bin_edges=bin_edges,
        trans=trans_mom, marginal=marginal, belief_grid=belief_grid,
        n_soc=N_SOC, n_actions=N_ACTIONS, dispatch_limit=100
    )
    
    start = time.time()
    V_mom, policy_mom = solver_mom.solve()
    print(f"  Solve time: {time.time() - start:.1f}s")
    
    results_mom = simulate_all_days(
        solver_mom, test_price_matrix, test_daily_valid,
        train_priors, V_mom, policy_mom, label='Momentum'
    )
    results_mom.to_csv('data/stochastic/pomdp_annual_momentum.csv', index=False)
    print_summary(results_mom, 'Momentum')
    
    # === Side-by-side comparison ===
    print(f"\n{'='*90}")
    print(f"=== Regime-by-Regime Comparison: Standard vs Momentum ===")
    print_regime_comparison(results_std, results_mom, REGIME_NAMES)
    
    # === Day-by-day comparison ===
    print(f"\n=== Days where momentum helps most ===")
    merged = results_std[['date', 'regime_idx', 'dp_revenue']].copy()
    merged['std_revenue'] = results_std['pomdp_revenue']
    merged['mom_revenue'] = results_mom['pomdp_revenue']
    merged['diff'] = merged['mom_revenue'] - merged['std_revenue']
    
    print(f"\n  Top 10 days where momentum improves revenue:")
    top = merged.nlargest(10, 'diff')
    print(f"  {'Date':>12s}  {'Regime':>6s}  {'DP':>8s}  {'Std':>8s}  "
          f"{'Mom':>8s}  {'Diff':>8s}")
    for _, row in top.iterrows():
        print(f"  {row['date']:>12s}  r{int(row['regime_idx'])}     "
              f"${row['dp_revenue']:>7.2f}  ${row['std_revenue']:>7.2f}  "
              f"${row['mom_revenue']:>7.2f}  ${row['diff']:>+7.2f}")
    
    print(f"\n  Top 10 days where momentum hurts revenue:")
    bottom = merged.nsmallest(10, 'diff')
    print(f"  {'Date':>12s}  {'Regime':>6s}  {'DP':>8s}  {'Std':>8s}  "
          f"{'Mom':>8s}  {'Diff':>8s}")
    for _, row in bottom.iterrows():
        print(f"  {row['date']:>12s}  r{int(row['regime_idx'])}     "
              f"${row['dp_revenue']:>7.2f}  ${row['std_revenue']:>7.2f}  "
              f"${row['mom_revenue']:>7.2f}  ${row['diff']:>+7.2f}")
    
    # Overall stats
    print(f"\n  Day-level statistics:")
    print(f"    Days momentum helps:  {(merged['diff'] > 0.01).sum()}")
    print(f"    Days momentum hurts:  {(merged['diff'] < -0.01).sum()}")
    print(f"    Days no difference:   {((merged['diff'] >= -0.01) & (merged['diff'] <= 0.01)).sum()}")
    print(f"    Mean diff: ${merged['diff'].mean():+.2f}/day")
    print(f"    Total diff: ${merged['diff'].sum():+,.0f}/year")
    
    # --- Restore stdout ---
    sys.stdout = sys.__stdout__
    log_file.close()
    print(f"Output saved to data/stochastic/pomdp_momentum_comparison.log")