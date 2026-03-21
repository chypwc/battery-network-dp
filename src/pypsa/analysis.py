"""
Analysis of full-year PyPSA dispatch results.

Reads the daily revenue CSV produced by optimise_year() and computes
annual statistics, seasonal breakdowns, and revenue distribution
metrics for the NPV model.
"""

import numpy as np
import pandas as pd 


def load_annual_results(
        csv_path: str = "data/pypsa/annual_revenue.csv") -> pd.DataFrame:
    """
    Load the annual revenue CSV and add derived columns.

    The CSV has columns: date, revenue, spread, min_price, max_price, mean_price
    We add: month, season, is_spike (revenue > A$500)
    """
    df = pd.read_csv(csv_path)
    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.month
    df["weekday"] = df["date"].dt.day_name()

    # Season (Australian): Summer=DJF, Autumn=MAM, Winter=JJA, Spring=SON
    season_map = {
        12: "Summer", 1: "Summer", 2: "Summer",
        3: "Autumn", 4: "Autumn", 5: "Autumn",
        6: "Winter", 7: "Winter", 8: "Winter",
        9: "Spring", 10: "Spring", 11: "Spring",
    }
    df["season"] = df["month"].map(season_map)

    # Flag spike days (revenue > $500)
    df["is_spike"] = df["revenue"] > 500

    return df


def compute_statistics(df: pd.DataFrame) -> dict:
    """
    Compute annual revenue statistics.

    Returns dict with:
        annual_total, mean_daily, median_daily, std_daily,
        p10, p25, p75, p90, min_daily, max_daily,
        num_days, num_spike_days,
        annual_excl_top5, annual_excl_top10, annual_excl_top20
    """
    rev = df["revenue"].values

    stats = {
        "num_days": len(rev),
        "annual_total": rev.sum(),
        "mean_daily": rev.mean(),
        "median_daily": np.median(rev),
        "std_daily": rev.std(),
        "p10": np.percentile(rev, 10),
        "p25": np.percentile(rev, 25),
        "p75": np.percentile(rev, 75),
        "p90": np.percentile(rev, 90),
        "min_daily": rev.min(),
        "max_daily": rev.max(),
        "num_spike_days": (rev > 500).sum(),
    }

    # Revenue excluding top N spike days
    sorted_rev = np.sort(rev)
    for n in [5, 10, 20]:
        remaining = sorted_rev[:-n] if n < len(sorted_rev) else sorted_rev
        stats[f"annual_excl_top{n}"] = remaining.sum()
        stats[f"mean_excl_top{n}"] = remaining.mean()

    return stats


def seasonal_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """
    Revenue breakdown by Australian season.

    Returns DataFrame with columns: season, days, total, mean, median
    Ordered: Summer, Autumn, Winter, Spring
    """
    grouped = df.groupby("season")["revenue"].agg(
        days="count",
        total="sum",
        mean="mean",
        median="median",
    )

    # Order by Australian seasons
    order = ["Summer", "Autumn", "Winter", "Spring"]
    grouped = grouped.reindex(order)

    return grouped


def monthly_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """Revenue breakdown by month."""
    grouped = df.groupby("month")["revenue"].agg(
        days="count",
        total="sum",
        mean="mean",
        median="median",
    )
    return grouped

def top_spike_days(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Return the top N revenue days."""
    return df.nlargest(n, "revenue")[
        ["date", "revenue", "spread", "max_price"]
    ].reset_index(drop=True)

def revenue_distribution_buckets(df: pd.DataFrame) -> pd.DataFrame:
    """
    Count days in revenue buckets.

    Buckets: <$10, $10-50, $50-100, $100-500, >$500
    """
    bins = [0, 10, 50, 100, 500, float("inf")]
    labels = ["< A$10", "A$10-50", "A$50-100", "A$100-500", "> A$500"]
    df = df.copy()

    # pd.cut returns a categorical series,
    #  set right=False, the intervals are left‑closed, right‑open:[a,b)
    df["bucket"] = pd.cut(df["revenue"], bins=bins, labels=labels, right=False)
    counts = df["bucket"].value_counts().reindex(labels)

    result = pd.DataFrame({
        "bucket": labels,
        "days": counts.values,
        "pct": (counts.values / len(df) * 100),
    })
    return result