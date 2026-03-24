"""
Value of information analysis from POMDP simulation results.

Reads pomdp_annual_results.csv and produces summary statistics,
regime breakdowns, and key findings.
"""

import numpy as np
import pandas as pd


def load_results(results_path='data/stochastic/pomdp_annual_results.csv'):
    """Load POMDP simulation results."""
    df = pd.read_csv(results_path)
    df['date'] = pd.to_datetime(df['date'])
    return df


def regime_summary(df, regime_names):
    """Breakdown by regime."""
    print("\n=== Value of Information by Regime ===\n")
    print(f"  {'Regime':>8s}  {'Days':>5s}  {'DP/day':>8s}  {'POMDP/day':>9s}  "
          f"{'Capture':>8s}  {'Info/day':>8s}  {'Info Annual':>11s}  "
          f"{'Converge':>8s}")
    
    total_dp = 0
    total_pomdp = 0
    
    for idx in sorted(df['regime_idx'].unique()):
        mask = df['regime_idx'] == idx
        subset = df[mask]
        n_days = len(subset)
        
        dp_mean = subset['dp_revenue'].mean()
        pomdp_mean = subset['pomdp_revenue'].mean()
        capture = pomdp_mean / dp_mean * 100 if dp_mean != 0 else 0
        info_mean = subset['info_value'].mean()
        info_annual = subset['info_value'].sum()
        
        converge = subset['belief_converge_period'].dropna()
        converge_median = converge.median() if len(converge) > 0 else float('nan')
        
        name = regime_names[idx] if idx < len(regime_names) else f'r{idx}'
        
        total_dp += subset['dp_revenue'].sum()
        total_pomdp += subset['pomdp_revenue'].sum()
        
        print(f"  {name:>8s}  {n_days:5d}  ${dp_mean:>7.2f}  ${pomdp_mean:>8.2f}  "
              f"{capture:>7.1f}%  ${info_mean:>7.2f}  ${info_annual:>10.0f}  "
              f"{converge_median:>7.1f}p")
    
    total_info = total_dp - total_pomdp
    capture_total = total_pomdp / total_dp * 100 if total_dp != 0 else 0
    
    print(f"  {'':>8s}  {'':>5s}  {'':>8s}  {'':>9s}  "
          f"{'':>8s}  {'':>8s}  {'-'*11}  {'':>8s}")
    print(f"  {'TOTAL':>8s}  {len(df):5d}  {'':>8s}  {'':>9s}  "
          f"{capture_total:>7.1f}%  {'':>8s}  ${total_info:>10.0f}")
    
    return total_dp, total_pomdp


def day_type_summary(df):
    """Breakdown by weekday/weekend."""
    print("\n=== Value of Information by Day Type ===\n")
    print(f"  {'Type':>8s}  {'Days':>5s}  {'DP Annual':>10s}  "
          f"{'POMDP Annual':>12s}  {'Capture':>8s}  {'Info Annual':>11s}")
    
    for day_type in ['weekday', 'weekend']:
        mask = df['day_type'] == day_type
        subset = df[mask]
        dp_sum = subset['dp_revenue'].sum()
        pomdp_sum = subset['pomdp_revenue'].sum()
        capture = pomdp_sum / dp_sum * 100 if dp_sum != 0 else 0
        info_sum = dp_sum - pomdp_sum
        
        print(f"  {day_type:>8s}  {len(subset):5d}  ${dp_sum:>9.0f}  "
              f"${pomdp_sum:>11.0f}  {capture:>7.1f}%  ${info_sum:>10.0f}")


def convergence_summary(df, regime_names):
    """How fast does belief converge?"""
    print("\n=== Belief Convergence Speed ===\n")
    print(f"  {'Regime':>8s}  {'Days':>5s}  {'Median':>7s}  {'P25':>5s}  "
          f"{'P75':>5s}  {'Never':>6s}")
    
    for idx in sorted(df['regime_idx'].unique()):
        mask = df['regime_idx'] == idx
        subset = df[mask]
        converge = subset['belief_converge_period']
        
        n_total = len(subset)
        n_never = converge.isna().sum()
        converge_valid = converge.dropna()
        
        name = regime_names[idx] if idx < len(regime_names) else f'r{idx}'
        
        if len(converge_valid) > 0:
            print(f"  {name:>8s}  {n_total:5d}  {converge_valid.median():>6.0f}p  "
                  f"{converge_valid.quantile(0.25):>4.0f}p  "
                  f"{converge_valid.quantile(0.75):>4.0f}p  "
                  f"{n_never:>5d}")
        else:
            print(f"  {name:>8s}  {n_total:5d}  {'N/A':>7s}  {'':>5s}  "
                  f"{'':>5s}  {n_never:>5d}")


def distribution_summary(df):
    """Revenue distribution statistics."""
    print("\n=== Revenue Distribution ===\n")
    
    for metric, col in [('Det DP', 'dp_revenue'), ('POMDP', 'pomdp_revenue')]:
        vals = df[col]
        print(f"  {metric}:")
        print(f"    Mean:   ${vals.mean():>10.2f}")
        print(f"    Median: ${vals.median():>10.2f}")
        print(f"    Std:    ${vals.std():>10.2f}")
        print(f"    Min:    ${vals.min():>10.2f}")
        print(f"    Max:    ${vals.max():>10.2f}")
        print(f"    P10:    ${vals.quantile(0.10):>10.2f}")
        print(f"    P90:    ${vals.quantile(0.90):>10.2f}")
        print()
    
    info = df['info_value']
    print(f"  Info value:")
    print(f"    Mean:   ${info.mean():>10.2f}/day")
    print(f"    Median: ${info.median():>10.2f}/day")
    print(f"    Total:  ${info.sum():>10.0f}/year")


def key_findings(df, regime_names):
    total_dp = df['dp_revenue'].sum()
    total_pomdp = df['pomdp_revenue'].sum()
    total_info = total_dp - total_pomdp
    capture = total_pomdp / total_dp * 100

    # Split: ordinary vs extreme (top regime)
    max_regime = df['regime_idx'].max()
    ordinary_mask = df['regime_idx'] < max_regime
    extreme_mask = df['regime_idx'] == max_regime

    ordinary_info = df[ordinary_mask]['info_value'].sum()
    extreme_info = df[extreme_mask]['info_value'].sum()
    ordinary_dp = df[ordinary_mask]['dp_revenue'].sum()
    ordinary_pomdp = df[ordinary_mask]['pomdp_revenue'].sum()
    ordinary_capture = ordinary_pomdp / ordinary_dp * 100 if ordinary_dp > 0 else 0
    extreme_dp = df[extreme_mask]['dp_revenue'].sum()
    extreme_pomdp = df[extreme_mask]['pomdp_revenue'].sum()
    extreme_capture = extreme_pomdp / extreme_dp * 100 if extreme_dp > 0 else 0

    median_converge = df['belief_converge_period'].dropna().median()
    n_negative = (df['pomdp_revenue'] < 0).sum()

    print("\n" + "=" * 80)
    print("=== Key Statistics ===")
    print("=" * 80)
    print(f"""
  Annual revenue
    Deterministic DP (perfect foresight): ${total_dp:>10,.0f}
    POMDP (regime-aware, no foresight):   ${total_pomdp:>10,.0f}
    Value of perfect information:         ${total_info:>10,.0f}
    Capture rate:                          {capture:>9.1f}%

  Ordinary vs extreme days
    Ordinary ({ordinary_mask.sum()} days): ${ordinary_info:>8,.0f} info value, {ordinary_capture:.1f}% capture
    Extreme  ({extreme_mask.sum()} days):  ${extreme_info:>8,.0f} info value, {extreme_capture:.1f}% capture

  Belief convergence (periods to 90% on correct regime)
    Median: {median_converge:.0f} periods ({median_converge * 0.5:.1f} hours)
    All 366 days converge: {df['final_belief_correct'].min() >= 0.9}

  POMDP negative revenue days: {n_negative}
""")


if __name__ == '__main__':
    from src.stochastic.regime import REGIME_NAMES
    
    print("=== POMDP Value of Information Analysis ===\n")
    
    df = load_results()
    print(f"  Loaded {len(df)} days")
    
    regime_summary(df, REGIME_NAMES)
    day_type_summary(df)
    convergence_summary(df, REGIME_NAMES)
    distribution_summary(df)
    key_findings(df, REGIME_NAMES)