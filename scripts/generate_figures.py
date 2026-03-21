"""
Generate publication-quality figures for the README.

Creates three graphs:
  1. Annual revenue histogram (366 days) — shows spike-driven distribution
  2. Three-method dispatch comparison (PyPSA vs DP vs RL on typical day)
  3. Violations heatmap (366 days × 48 periods) — structural violation pattern

Usage:
    python generate_figures.py

Requires:
    - data/pypsa/annual_revenue.csv (from run_pypsa_annual.py)
    - data/pypsa/annual_dispatch_results.csv (from run_annual_dispatch.py)
    - OpenDSS + src modules (for dispatch comparison)

Output:
    - docs/figures/revenue_histogram.png
    - docs/figures/dispatch_comparison.png
    - docs/figures/violations_heatmap.png
"""

import os
import logging
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

logging.getLogger("pypsa").setLevel(logging.ERROR)
logging.getLogger("linopy").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", category=FutureWarning)

os.makedirs("docs/figures", exist_ok=True)

# Consistent style
plt.rcParams.update({
    "font.family": "serif",
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.labelsize": 10,
    "figure.dpi": 150,
    "savefig.dpi": 200,
})

COLOURS = {
    "pypsa": "#2196F3",   # blue
    "dp": "#FF9800",      # orange
    "rl": "#4CAF50",      # green
    "tou": "#9C27B0",     # purple
    "price": "#757575",   # grey
    "spike": "#F44336",   # red
    "violation": "#D32F2F",
    "safe": "#E8F5E9",
}


# ============================================================
# Figure 1: Annual Revenue Histogram
# ============================================================

def plot_revenue_histogram():
    """366-day revenue distribution with key markers."""
    print("Generating revenue histogram...")

    df = pd.read_csv("data/pypsa/annual_revenue.csv")
    revenues = df["revenue"].values

    fig, ax = plt.subplots(figsize=(8, 4))

    # Histogram — clip at A$200 for readability, show spike count separately
    clipped = np.clip(revenues, 0, 200)
    n_spikes = (revenues > 200).sum()

    ax.hist(clipped, bins=40, color=COLOURS["pypsa"], alpha=0.7,
            edgecolor="white", linewidth=0.5)

    # Key vertical lines
    median_rev = np.median(revenues)
    mean_rev = revenues.mean()
    tou_daily = 81.56

    ax.axvline(median_rev, color=COLOURS["dp"], linewidth=2, linestyle="--",
               label=f"Median: A${median_rev:.0f}/day")
    ax.axvline(tou_daily, color=COLOURS["tou"], linewidth=2, linestyle="-.",
               label=f"TOU daily: A${tou_daily:.0f}/day")
    ax.axvline(mean_rev, color=COLOURS["spike"], linewidth=2, linestyle=":",
               label=f"Mean: A${mean_rev:.0f}/day (incl. spikes)")

    # Spike annotation
    ax.annotate(
        f"{n_spikes} days > A$200\n(up to A${revenues.max():,.0f})\n→ 44% of annual revenue",
        xy=(195, 5), fontsize=8,
        bbox=dict(boxstyle="round,pad=0.3", facecolor="#FFF3E0", edgecolor=COLOURS["spike"]),
        ha="right",
    )

    ax.set_xlabel("Daily Revenue (A$)")
    ax.set_ylabel("Number of Days")
    ax.set_title("Spot Revenue Distribution — 366 Days (2024 AEMO NSW1, ±100kW/200kWh)")
    ax.legend(loc="upper right", fontsize=9)
    ax.set_xlim(-5, 210)

    fig.tight_layout()
    fig.savefig("docs/figures/revenue_histogram.png")
    plt.close()
    print("  Saved: docs/figures/revenue_histogram.png")


# ============================================================
# Figure 2: Three-Method Dispatch Comparison
# ============================================================

def plot_dispatch_comparison():
    """PyPSA vs DP vs RL dispatch on the typical day."""
    print("Generating dispatch comparison...")

    from src.dp.battery import Battery
    from src.dp.solver import DPSolver
    from src.dp.prices import load_day_prices
    from src.opendss.profiles import generate_load_profile, generate_solar_profile
    from src.pypsa.dispatch import optimise_day as pypsa_optimise
    from src.rl.environment import CommunityBatteryEnv
    from src.rl.utils import discretise_soc

    prices = load_day_prices("data/aemo/prices_typical_2024-06-28.csv")
    battery = Battery(kwh_rated=200, kw_rated=100)
    load_profile = generate_load_profile()
    solar_profile = generate_solar_profile()

    # --- PyPSA ---
    pypsa_result = pypsa_optimise(prices, capacity_kwh=200, power_kw=100)
    pypsa_dispatch = -pypsa_result["dispatch_kw"]  # flip sign: PyPSA uses +discharge, DP uses +charge
    pypsa_soc = pypsa_result["soc_kwh"]  # 48 elements, end-of-period SoC

    # --- DP ---
    solver = DPSolver(battery, dispatch_limit=100, n_soc=81, n_actions=33)
    dp_result = solver.solve(prices, initial_soc=100)
    dp_dispatch = dp_result["dispatch"]

    # DP SoC trajectory (end-of-period)
    dp_soc = np.zeros(48)
    soc = 100.0
    for t in range(48):
        soc = float(battery.next_soc(soc, dp_dispatch[t], 0.5))
        soc = max(battery.soc_min, min(battery.soc_max, soc))
        dp_soc[t] = soc

    # --- RL: replay Q-table through environment, record SoC ---
    Q = np.load("data/q_tables/Q_phase2_100kW_200kWh.npz")["Q"]
    n_soc_bins = Q.shape[0]  # 100

    env = CommunityBatteryEnv(
        prices, load_profile, solar_profile,
        dispatch_limit=100, violation_penalty=10.0,
        battery_kwh=200, n_actions=33, skip_network=True)

    rl_dispatch = np.zeros(48)
    rl_soc = np.zeros(48)
    state = env.reset()
    soc, t_idx = state
    for step in range(48):
        soc_idx = discretise_soc(soc, env.battery, n_soc_bins)
        action_idx = np.argmax(Q[soc_idx, t_idx, :])
        next_state, reward, done, info = env.step(action_idx)
        rl_dispatch[step] = info["action_kw"]
        soc, t_idx = next_state
        rl_soc[step] = soc  # end-of-period SoC from environment

    # Revenue labels
    pypsa_rev = pypsa_result["revenue"]
    dp_rev = dp_result["total_revenue"]
    rl_rev = sum(float(battery.reward(rl_dispatch[t], prices[t], 0.5))
                 for t in range(48))

    # Time axis
    times = [f"{t//2:02d}:{(t%2)*30:02d}" for t in range(48)]
    x = np.arange(48)
    tick_positions = list(range(0, 48, 4))
    tick_labels = [times[i] for i in tick_positions]

    # --- Create figure: 3 panels + right margin for legends ---
    fig = plt.figure(figsize=(12, 8.5))

    # Leave right margin for legends
    gs = fig.add_gridspec(3, 1, height_ratios=[1, 1.5, 1],
                          hspace=0.4)
    ax_price = fig.add_subplot(gs[0])
    ax_dispatch = fig.add_subplot(gs[1], sharex=ax_price)
    ax_soc = fig.add_subplot(gs[2], sharex=ax_price)

    # --- Panel 1: Prices ---
    ax_price.fill_between(x, prices, alpha=0.2, color=COLOURS["price"])
    ax_price.plot(x, prices, color=COLOURS["price"], linewidth=1.5)
    ax_price.set_ylabel("Price\n(A$/MWh)")
    ax_price.set_title(
        "Three-Method Dispatch Comparison — Typical Day "
        "(2024-06-28, ±100kW / 200kWh)")
    ax_price.axhline(0, color="black", linewidth=0.5, alpha=0.3)
    plt.setp(ax_price.get_xticklabels(), visible=False)

    # --- Panel 2: Dispatch ---
    ax_dispatch.step(x, pypsa_dispatch, where="mid", color=COLOURS["pypsa"],
                     linewidth=1.5, alpha=0.8, label="PyPSA (continuous LP)")
    ax_dispatch.step(x, dp_dispatch, where="mid", color=COLOURS["dp"],
                     linewidth=1.5, alpha=0.8, label="DP (discrete)")
    ax_dispatch.step(x, rl_dispatch, where="mid", color=COLOURS["rl"],
                     linewidth=2.0, label="RL (network-safe)")
    ax_dispatch.axhline(0, color="black", linewidth=0.5, alpha=0.3)
    ax_dispatch.set_ylabel("Battery Power (kW)\n+ charge / − discharge")
    plt.setp(ax_dispatch.get_xticklabels(), visible=False)

    # Highlight evening oscillation zone
    ax_dispatch.axvspan(36, 42, alpha=0.08, color=COLOURS["rl"])
    ax_dispatch.annotate(
        "RL oscillation\n(voltage support)",
        xy=(39, -80), fontsize=7, ha="center",
        color=COLOURS["rl"], fontstyle="italic")

    # --- Panel 3: SoC ---
    ax_soc.plot(x, pypsa_soc[:48], color=COLOURS["pypsa"], linewidth=1.5,
                alpha=0.8, label="PyPSA")
    ax_soc.plot(x, dp_soc, color=COLOURS["dp"], linewidth=1.5,
                alpha=0.8, label="DP")
    ax_soc.plot(x, rl_soc, color=COLOURS["rl"], linewidth=2.0,
                label="RL")
    ax_soc.axhline(20, color=COLOURS["violation"], linewidth=1,
                   linestyle=":", alpha=0.5, label="Min SoC (DP/PyPSA)")
    ax_soc.set_ylabel("SoC (kWh)")
    ax_soc.set_xlabel("Time of Day")
    ax_soc.set_ylim(0, 210)
    ax_soc.set_yticks([0, 20, 50, 100, 150, 200])

    ax_soc.set_xticks(tick_positions)
    ax_soc.set_xticklabels(tick_labels, rotation=45, ha="right", fontsize=8)

    # Legend between dispatch and SoC panels
    lines_d, labels_d = ax_dispatch.get_legend_handles_labels()
    lines_s, labels_s = ax_soc.get_legend_handles_labels()
    all_lines = lines_d + [lines_s[-1]]   # 3 method lines + min SoC line
    all_labels = labels_d + [labels_s[-1]]
    fig.legend(all_lines, all_labels,
               loc="center", bbox_to_anchor=(0.5, 0.33),
               ncol=4, fontsize=9, frameon=True)

    fig.savefig("docs/figures/dispatch_comparison.png")
    plt.close()
    print(f"  Saved: docs/figures/dispatch_comparison.png")
    print(f"  Revenues — PyPSA: A${pypsa_rev:.2f}, DP: A${dp_rev:.2f}, RL: A${rl_rev:.2f}")


# ============================================================
# Figure 3: Violations Heatmap (366 days × 48 periods)
# ============================================================

def plot_violations_heatmap():
    """
    Heatmap of DP violations across the year.
    Requires running: python run_annual_violations_heatmap.py first
    to generate the per-period violation data.

    If per-period data isn't available, generates a simplified version
    from the daily totals.
    """
    print("Generating violations heatmap...")

    from src.dp.battery import Battery
    from src.dp.solver import DPSolver
    from src.dp.prices import load_and_clean, extract_day
    from src.opendss.profiles import generate_load_profile, generate_solar_profile
    from src.opendss.feeders import FEEDER_32
    from src.integration import timeseries

    battery = Battery(kwh_rated=200, kw_rated=100)
    solver = DPSolver(battery, dispatch_limit=100, n_soc=81, n_actions=33)
    load_profile = generate_load_profile()
    solar_profile = generate_solar_profile()
    dss_file = FEEDER_32["dss_file"]

    # Load price data
    filepaths = [f"data/aemo/PRICE_AND_DEMAND_2024{m:02d}_NSW1.csv" for m in range(1, 13)]
    df = load_and_clean(filepaths)
    df["date"] = df["datetime"].dt.date
    counts = df.groupby("date").size()
    complete_days = sorted(counts[counts == 48].index)

    # Build violation matrix: days × periods
    # Each cell = 1 if violation at that period, 0 otherwise
    n_days = len(complete_days)
    viol_matrix = np.zeros((n_days, 48))
    dates = []

    for i, date in enumerate(complete_days):
        prices = extract_day(df, str(date))
        if prices is None or len(prices) < 48:
            continue

        dp_result = solver.solve(prices[:48], initial_soc=100)
        dp_dispatch = dp_result["dispatch"]

        df_ts = timeseries.run(
            dp_dispatch, load_profile, solar_profile,
            FEEDER_32, dss_file, battery_enabled=True, battery=battery)

        # Check violations at each period
        for t in range(48):
            row = df_ts.iloc[t]
            v_min = row["v_min"] if "v_min" in df_ts.columns else row.get("bus_v_min_pu", 1.0)
            v_max = row["v_max"] if "v_max" in df_ts.columns else row.get("bus_v_max_pu", 1.0)
            if v_min < 0.94 or v_max > 1.10:
                viol_matrix[i, t] = 1

        dates.append(str(date))

        if (i + 1) % 50 == 0:
            print(f"    {i+1}/{n_days} days...")

    # Create heatmap
    fig, ax = plt.subplots(figsize=(12, 6))

    # Custom colormap: white = no violation, red = violation
    from matplotlib.colors import ListedColormap
    cmap = ListedColormap([COLOURS["safe"], COLOURS["violation"]])

    im = ax.imshow(viol_matrix, aspect="auto", cmap=cmap,
                   interpolation="nearest", vmin=0, vmax=1)

    # X-axis: time of day
    time_labels = [f"{t//2:02d}:00" for t in range(0, 48, 4)]
    ax.set_xticks(range(0, 48, 4))
    ax.set_xticklabels(time_labels, rotation=45, ha="right", fontsize=8)
    ax.set_xlabel("Time of Day")

    # Y-axis: months
    month_starts = []
    month_labels = []
    for i, d in enumerate(dates):
        day = int(d.split("-")[2])
        month = int(d.split("-")[1])
        if day == 1 or i == 0:
            month_starts.append(i)
            month_names = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            month_labels.append(month_names[month])

    ax.set_yticks(month_starts)
    ax.set_yticklabels(month_labels, fontsize=9)
    ax.set_ylabel("Month (2024)")

    ax.set_title("DP Dispatch Voltage Violations — 366 Days × 48 Periods (±100kW/200kWh)\n"
                 "Red = voltage violation (V < 0.94 or V > 1.10 pu). "
                 f"Total: {int(viol_matrix.sum())} violations across {n_days} days.",
                 fontsize=10)

    fig.tight_layout()
    fig.savefig("docs/figures/violations_heatmap.png")
    plt.close()
    print(f"  Saved: docs/figures/violations_heatmap.png")
    print(f"  Total violations: {int(viol_matrix.sum())}")


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  Generating README Figures")
    print("=" * 60)

    # Figure 1: always possible (just needs CSV)
    plot_revenue_histogram()

    # Figure 2: needs PyPSA + DP + RL dispatch
    try:
        plot_dispatch_comparison()
    except Exception as e:
        print(f"  Skipped dispatch comparison: {e}")

    # Figure 3: needs DP + OpenDSS for 366 days (~36 min)
    import sys
    if "--with-heatmap" in sys.argv:
        plot_violations_heatmap()
    else:
        print("\n  Violations heatmap skipped (slow: ~36 min).")
        print("  Run with --with-heatmap to generate it.")

    print("\nDone. Add to README with:")
    print('  ![Revenue Distribution](docs/figures/revenue_histogram.png)')
    print('  ![Dispatch Comparison](docs/figures/dispatch_comparison.png)')
    print('  ![Violations Heatmap](docs/figures/violations_heatmap.png)')