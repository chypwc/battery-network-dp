"""
Community Battery DP Optimiser (Layer 2)
========================================
Finds the optimal charge/discharge schedule for a community battery
by solving the Bellman equation backward in time, then simulating
forward to produce a dispatch schedule for OpenDSS.

Bellman equation:
    V_t(s) = max_a [ r(s, a, p_t) + V_{t+1}(s') ]

where:
    s   = state of charge (kWh)
    a   = action: charge (+kW) or discharge (-kW)
    p_t = electricity spot price at time t ($/MWh)
    s'  = next state after action a
    r   = immediate reward (revenue from arbitrage)
    V_t = value function (maximum future revenue from state s at time t)

The DP solver:
    1. Discretises the state space (SoC levels) and action space
    2. Solves backward from the last time step to the first
    3. At each (t, s), finds the action that maximises reward + future value
    4. Simulates forward using the optimal policy to produce a dispatch schedule
"""

import numpy as np
import pandas as pd
import math
import csv
import glob
import os


class Battery:
    """
    Physical model of a community battery.

    Parameters match the OpenDSS Storage element:
        New Storage.CommunityBatt Bus1=brA phases=3 kV=0.4
        ~ kWRated=100 kWhRated=200 kWhStored=100
        ~ %EffCharge=95 %EffDischarge=95
        ~ %reserve=10 %IdlingkW=0.5
    """

    def __init__(
        self,
        kwh_rated=200,      # total energy capacity (kWh)
        kw_rated=100,       # max charge/discharge power (kW)
        eff_charge=0.95,    # charging efficiency η_c
        eff_discharge=0.95, # discharging efficiency η_d
        reserve_pct=10,     # minimum SoC (% of capacity)
        degradation=0.02,   # degradation cost ($/kWh throughput)
    ):
        self.kwh_rated = kwh_rated
        self.kw_rated = kw_rated
        self.eta_c = eff_charge
        self.eta_d = eff_discharge
        self.soc_min = kwh_rated * reserve_pct / 100  # 20 kWh
        self.soc_max = kwh_rated                       # 200 kWh
        self.degradation = degradation

    def next_soc(self, soc, action_kw, dt_hours):
        """
        Compute next state of charge after an action.

        Physics:
            Charging:    s' = s + η_c × P × Δt
                         (not all grid power reaches the battery)
            Discharging: s' = s - P × Δt / η_d
                         (battery must discharge more than what's delivered)

        Args:
            soc: current state of charge (kWh)
            action_kw: charge (+) or discharge (-) power (kW)
            dt_hours: time step duration (hours), e.g. 0.5 for 30 min

        Returns:
            next_soc: state of charge after action (kWh)
        """
        if action_kw >= 0:
            # Charging: energy stored = η_c × power × time
            next_s = soc + self.eta_c * action_kw * dt_hours
        else:
            # Discharging: energy removed = power × time / η_d
            # (must remove more from battery than delivered to grid)
            next_s = soc + action_kw * dt_hours / self.eta_d
            # Note: action_kw < 0, so this subtracts from soc
        return next_s

    def feasible_actions(self, soc, dt_hours, action_grid):
        """
        Filter actions to only those physically feasible.

        Constraints:
            1. |action| ≤ kw_rated           (power rating limit)
            2. soc_min ≤ s' ≤ soc_max        (capacity limits)

        Args:
            soc: current SoC (kWh)
            dt_hours: time step (hours)
            action_grid: array of candidate actions (kW)

        Returns:
            list of feasible actions (kW)
        """
        feasible = []
        for a in action_grid:
            # Check power rating
            if abs(a) > self.kw_rated:
                continue
            # Check next SoC stays within bounds
            s_next = self.next_soc(soc, a, dt_hours)
            if self.soc_min <= s_next <= self.soc_max:
                feasible.append(a)
        return feasible

    def reward(self, action_kw, price, dt_hours):
        """
        Compute immediate reward (revenue) for an action.

        Revenue model:
            r = -price × action × Δt - degradation × |action| × Δt

        Sign convention:
            action > 0 (charging):    we BUY electricity → cost = price × action × Δt
            action < 0 (discharging): we SELL electricity → revenue = price × |action| × Δt

        The negative sign on the first term makes this work:
            Charging:    r = -price × (+P) × Δt = negative (we pay)
            Discharging: r = -price × (-P) × Δt = positive (we earn)

        Degradation cost:
            Every kWh of throughput shortens battery life.
            Typical: $0.02/kWh throughput for Li-ion.

        Args:
            action_kw: charge (+) or discharge (-) power (kW)
            price: spot price ($/MWh)
            dt_hours: time step (hours)

        Returns:
            reward in dollars
        """
        # Convert price from $/MWh to $/kWh: divide by 1000
        price_kwh = price / 1000

        # Revenue from energy: negative means cost, positive means income
        energy_revenue = -price_kwh * action_kw * dt_hours

        # Degradation cost: always negative (reduces reward)
        deg_cost = self.degradation * abs(action_kw) * dt_hours

        return energy_revenue - deg_cost


class DPSolver:
    """
    Backward-induction dynamic programming solver.

    Algorithm:
        1. Create value function table V[t][s] = 0 for all t, s
        2. From t = T-1 down to t = 0:
            For each state s in soc_grid:
                For each feasible action a:
                    Compute: s' = next_soc(s, a)
                    Compute: r = reward(a, price[t])
                    Look up: V_{t+1}(s') by interpolation
                    Compute: total = r + V_{t+1}(s')
                Store: V_t(s) = max over all a of total
                Store: policy_t(s) = argmax a of total
        3. Simulate forward from initial SoC using stored policy
    """

    def __init__(self, battery, dt_hours=0.5):
        """
        Args:
            battery: Battery instance
            dt_hours: time step in hours (0.5 = 30 minutes)
        """
        self.battery = battery
        self.dt = dt_hours

        # Discretise state space: SoC levels from soc_min to soc_max
        # 21 levels → steps of 10 kWh for a 200 kWh battery
        self.n_soc = 41
        self.soc_grid = np.linspace(
            battery.soc_min, battery.soc_max, self.n_soc
        )

        # Discretise action space: from -kw_rated to +kw_rated
        # Steps of 5 kW → 41 actions for a 100 kW battery
        self.n_actions = 41
        self.action_grid = np.linspace(
            # -battery.kw_rated, battery.kw_rated, self.n_actions
            -50, 50, self.n_actions
        )

    def _interp_value(self, value_array, soc):
        """
        Linearly interpolate the value function at a non-grid SoC.

        Because the next SoC after an action may not land exactly
        on a grid point (e.g. SoC=67.5 when grid has 60 and 70),
        we interpolate between the two nearest grid points.

        Args:
            value_array: V_{t+1}[s] array of length n_soc
            soc: the SoC value to look up

        Returns:
            interpolated value
        """
        return np.interp(soc, self.soc_grid, value_array)

    def solve(self, prices, initial_soc=None):
        """
        Solve the DP and return optimal dispatch schedule.

        Args:
            prices: array of spot prices ($/MWh), one per time step.
                    Length T determines the planning horizon.
            initial_soc: starting SoC in kWh (default: 50% capacity)

        Returns:
            dict with:
                'dispatch': array of optimal actions (kW) per time step
                'soc': array of SoC trajectory (kWh)
                'revenue': array of revenue per time step ($)
                'total_revenue': total revenue over horizon ($)
                'value_function': V[t][s] table
                'policy': optimal action at each (t, s)
        """
        if initial_soc is None:
            initial_soc = self.battery.kwh_rated / 2  # 50%

        T = len(prices)
        b = self.battery
        dt = self.dt

        # Allocate value function and policy tables
        # V[t][i] = max future revenue from soc_grid[i] at time t
        # policy[t][i] = optimal action (kW) from soc_grid[i] at time t
        V = np.zeros((T + 1, self.n_soc))
        policy = np.zeros((T, self.n_soc))

        # Terminal condition: V_T(s) = 0 for all s
        # (no value remaining after the last time step)
        # Already zero from np.zeros

        # ============================================================
        # BACKWARD PASS: fill V and policy from t=T-1 down to t=0
        # ============================================================
        # This is the core of the Bellman recursion:
        #   V_t(s) = max_a [ r(s, a, p_t) + V_{t+1}(s') ]
        # ============================================================

        for t in range(T - 1, -1, -1):
            price = prices[t]

            for i, soc in enumerate(self.soc_grid):
                best_value = -np.inf
                best_action = 0

                # Try all feasible actions from this state
                feasible = b.feasible_actions(soc, dt, self.action_grid)

                for a in feasible:
                    # Transition: compute next SoC
                    s_next = b.next_soc(soc, a, dt)

                    # Immediate reward
                    r = b.reward(a, price, dt)

                    # Future value (interpolated)
                    v_future = self._interp_value(V[t + 1], s_next)

                    # Total value = immediate + future
                    total = r + v_future

                    if total > best_value:
                        best_value = total
                        best_action = a

                V[t][i] = best_value
                policy[t][i] = best_action

        # ============================================================
        # FORWARD PASS: simulate optimal trajectory from initial SoC
        # ============================================================

        dispatch = np.zeros(T)
        soc_trajectory = np.zeros(T + 1)
        revenue = np.zeros(T)

        soc_trajectory[0] = initial_soc

        for t in range(T):
            soc = soc_trajectory[t]

            # Look up optimal action by interpolating the policy
            # (initial SoC may not be exactly on a grid point)
            action = np.interp(soc, self.soc_grid, policy[t])

            # Snap to nearest feasible action
            feasible = b.feasible_actions(soc, dt, self.action_grid)
            if feasible:
                action = min(feasible, key=lambda a: abs(a - action))
            else:
                action = 0  # no feasible action — idle

            dispatch[t] = action
            soc_trajectory[t + 1] = b.next_soc(soc, action, dt)
            revenue[t] = b.reward(action, prices[t], dt)

        return {
            'dispatch': dispatch,
            'soc': soc_trajectory,
            'revenue': revenue,
            'total_revenue': np.sum(revenue),
            'value_function': V,
            'policy': policy,
            'prices': prices,
        }


def generate_price_profile(profile='typical_summer'):
    """
    Generate a synthetic 24-hour price profile (48 half-hour periods).

    Based on typical NEM NSW1 (ACT) patterns.
    In the full project, replace with real AEMO data.

    Returns:
        prices: array of 48 spot prices in $/MWh
    """
    # Hours 0–47 (half-hourly: index 0 = 00:00, index 1 = 00:30, ...)
    T = 48
    prices = np.zeros(T)

    if profile == 'typical_summer':
        # Typical summer day in ACT (NSW1 region):
        # - Low overnight: $30–50/MWh
        # - Solar surplus midday: $10–30/MWh (sometimes negative)
        # - Evening peak 17:00–20:00: $100–200/MWh
        # - High shoulder 07:00–09:00: $60–80/MWh
        for i in range(T):
            hour = i / 2  # convert index to hour of day
            if hour < 5:          # 00:00–05:00 (overnight)
                prices[i] = 35 + np.random.normal(0, 5)
            elif hour < 7:        # 05:00–07:00 (early morning)
                prices[i] = 50 + np.random.normal(0, 8)
            elif hour < 9:        # 07:00–09:00 (morning shoulder)
                prices[i] = 70 + np.random.normal(0, 10)
            elif hour < 15:       # 09:00–15:00 (solar surplus)
                prices[i] = 20 + np.random.normal(0, 10)
            elif hour < 17:       # 15:00–17:00 (afternoon transition)
                prices[i] = 60 + np.random.normal(0, 15)
            elif hour < 20:       # 17:00–20:00 (evening peak)
                prices[i] = 150 + np.random.normal(0, 30)
            elif hour < 22:       # 20:00–22:00 (evening shoulder)
                prices[i] = 70 + np.random.normal(0, 10)
            else:                 # 22:00–24:00 (late night)
                prices[i] = 40 + np.random.normal(0, 5)

        # Ensure no negative prices (can happen in reality, but keep simple)
        prices = np.maximum(prices, 5)

    elif profile == 'spike_day':
        # Day with extreme evening price spike (summer heatwave)
        for i in range(T):
            hour = i / 2
            if hour < 5:
                prices[i] = 40
            elif hour < 9:
                prices[i] = 60
            elif hour < 15:
                prices[i] = 15  # low solar surplus
            elif hour < 17:
                prices[i] = 80
            elif hour < 20:
                prices[i] = 500  # extreme spike
            elif hour < 22:
                prices[i] = 100
            else:
                prices[i] = 45

    return prices


def export_dispatch_for_opendss(dispatch, kw_rated, filename='dp_optimal_dispatch.csv'):
    """
    Write dispatch schedule as OpenDSS Loadshape multipliers.

    OpenDSS Storage convention:
        positive multiplier → discharging (injecting to grid)
        negative multiplier → charging (absorbing from grid)

    Our DP convention:
        positive action → charging
        negative action → discharging

    So we negate and normalise: mult = -action / kw_rated

    Args:
        dispatch: array of actions from DP solver (kW)
        kw_rated: battery rated power (kW)
        filename: output CSV path
    """
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        for action in dispatch:
            # Negate: DP charging (+) → OpenDSS charging (-)
            # Normalise: divide by rated power to get [-1, 1]
            mult = -action / kw_rated
            writer.writerow([f"{mult:.4f}"])

    print(f"  Dispatch exported to {filename}")


def print_results(result, dt_hours=0.5):
    """Print formatted results from the DP solver."""

    dispatch = result['dispatch']
    soc = result['soc']
    revenue = result['revenue']
    prices = result['prices']
    T = len(dispatch)

    print(f"\n{'='*75}")
    print(f"  DP OPTIMISER RESULTS")
    print(f"{'='*75}")

    print(f"\n  Battery: {soc[0]:.0f} kWh initial → {soc[-1]:.0f} kWh final")
    print(f"  Total revenue: ${result['total_revenue']:.2f}")
    print(f"  Planning horizon: {T} periods ({T * dt_hours:.0f} hours)")

    # Summary statistics
    charge_energy = sum(a * dt_hours for a in dispatch if a > 0)
    discharge_energy = sum(-a * dt_hours for a in dispatch if a < 0)
    idle_periods = sum(1 for a in dispatch if a == 0)

    print(f"\n  Energy charged:    {charge_energy:.1f} kWh")
    print(f"  Energy discharged: {discharge_energy:.1f} kWh")
    print(f"  Idle periods:      {idle_periods} of {T}")

    # Average buy/sell prices
    buy_prices = [prices[t] for t in range(T) if dispatch[t] > 0]
    sell_prices = [prices[t] for t in range(T) if dispatch[t] < 0]
    if buy_prices:
        print(f"  Avg buy price:     ${np.mean(buy_prices):.1f}/MWh")
    if sell_prices:
        print(f"  Avg sell price:    ${np.mean(sell_prices):.1f}/MWh")

    # Detailed schedule
    print(f"\n  {'Time':<8} {'Price':>8} {'Action':>10} {'SoC':>8} {'Revenue':>10}")
    print(f"  {'':8} {'($/MWh)':>8} {'(kW)':>10} {'(kWh)':>8} {'($)':>10}")
    print(f"  {'-'*8} {'-'*8} {'-'*10} {'-'*8} {'-'*10}")

    for t in range(T):
        hour = t * dt_hours
        h = int(hour)
        m = int((hour - h) * 60)
        time_str = f"{h:02d}:{m:02d}"

        action = dispatch[t]
        if action > 0.1:
            action_str = f"+{action:.0f} (chg)"
        elif action < -0.1:
            action_str = f"{action:.0f} (dis)"
        else:
            action_str = "0 (idle)"

        print(f"  {time_str:<8} {prices[t]:>8.1f} {action_str:>10} {soc[t]:>8.1f} {revenue[t]:>10.3f}")

    # Final SoC
    print(f"  {'24:00':<8} {'':>8} {'':>10} {soc[T]:>8.1f}")


def load_aemo_prices(csv_path):
    """
    Load real AEMO price data from a CSV file.

    Expected format (output from aemo_downloader.py):
        price_mwh
        59.728
        76.176
        ...
        (48 rows for one day)

    Args:
        csv_path: path to CSV file with 'price_mwh' column

    Returns:
        numpy array of 48 prices ($/MWh)
    """
    df = pd.read_csv(csv_path)

    if 'price_mwh' in df.columns:
        prices = df['price_mwh'].values
    elif 'price' in df.columns:
        prices = df['price'].values
    else:
        # Assume single column
        prices = df.iloc[:, 0].values

    if len(prices) != 48:
        print(f"  Warning: expected 48 periods, got {len(prices)}")

    return prices.astype(float)


def main():
    """Run the DP optimiser with real AEMO price data."""

    # Create battery (matching OpenDSS Storage element)
    battery = Battery(
        kwh_rated=200,
        kw_rated=100,
        eff_charge=0.95,
        eff_discharge=0.95,
        reserve_pct=10,
        degradation=0.02,
    )

    # Create solver
    solver = DPSolver(battery, dt_hours=0.5)

    print(f"Battery: {battery.kwh_rated} kWh / {battery.kw_rated} kW")
    print(f"SoC range: {battery.soc_min:.0f}–{battery.soc_max:.0f} kWh")
    print(f"SoC grid: {solver.n_soc} levels")
    print(f"Action grid: {solver.n_actions} levels "
          f"({solver.action_grid[0]:.0f} to {solver.action_grid[-1]:.0f} kW)")

    # ============================================================
    # Load real AEMO price data
    # Look for CSV files from aemo_downloader.py in aemo_data/
    # ============================================================

    price_dir = 'aemo_data'
    price_files = sorted(glob.glob(os.path.join(price_dir, 'prices_*.csv')))

    if not price_files:
        print(f"\nNo price files found in {price_dir}/")
        print(f"Run aemo_downloader.py first, or place CSV files with format:")
        print(f"  price_mwh")
        print(f"  59.73")
        print(f"  76.18")
        print(f"  ... (48 rows)")
        print(f"\nFalling back to synthetic prices...\n")

        # Fallback: use synthetic prices
        np.random.seed(42)
        price_files_data = {
            'synthetic_typical': generate_price_profile('typical_summer'),
            'synthetic_spike': generate_price_profile('spike_day'),
        }
    else:
        print(f"\nFound {len(price_files)} price files in {price_dir}/:")
        for f in price_files:
            print(f"  {f}")

        price_files_data = {}
        for fp in price_files:
            # Extract label from filename: prices_typical_2024-03-15.csv → typical_2024-03-15
            basename = os.path.basename(fp)
            label = basename.replace('prices_', '').replace('.csv', '')
            try:
                prices = load_aemo_prices(fp)
                price_files_data[label] = prices
            except Exception as e:
                print(f"  Error loading {fp}: {e}")

    # ============================================================
    # Run DP for each price scenario
    # ============================================================

    results = {}

    for label, prices in price_files_data.items():
        print(f"\n{'#'*75}")
        print(f"# SCENARIO: {label}")
        print(f"#   Price range: ${prices.min():.1f} to ${prices.max():.1f}/MWh")
        print(f"#   Mean price: ${prices.mean():.1f}/MWh")
        print(f"{'#'*75}")

        result = solver.solve(prices, initial_soc=100)
        print_results(result)

        # Export dispatch for OpenDSS
        dispatch_file = f'dp_dispatch_{label}.csv'
        export_dispatch_for_opendss(
            result['dispatch'],
            battery.kw_rated,
            dispatch_file
        )

        results[label] = result

    # ============================================================
    # Summary comparison across all scenarios
    # ============================================================

    if len(results) > 1:
        print(f"\n{'='*75}")
        print(f"  COMPARISON ACROSS ALL SCENARIOS")
        print(f"{'='*75}")
        print(f"  {'Scenario':<35} {'Revenue':>10} {'Charged':>10} {'Discharged':>12} {'Cycles':>8}")
        print(f"  {'':35} {'($)':>10} {'(kWh)':>10} {'(kWh)':>12} {'':>8}")
        print(f"  {'-'*35} {'-'*10} {'-'*10} {'-'*12} {'-'*8}")

        for label, r in results.items():
            chg = sum(a * 0.5 for a in r['dispatch'] if a > 0)
            dis = sum(-a * 0.5 for a in r['dispatch'] if a < 0)
            # Cycles = total energy throughput / (2 × capacity)
            cycles = (chg + dis) / (2 * battery.kwh_rated)
            print(f"  {label:<35} {r['total_revenue']:>10.2f} "
                  f"{chg:>10.1f} {dis:>12.1f} {cycles:>8.2f}")

        # Annual revenue estimate
        # Rough: typical day × 300 + high days × 65
        if 'typical' in ' '.join(results.keys()):
            typical_key = [k for k in results if 'typical' in k]
            if typical_key:
                typical_rev = results[typical_key[0]]['total_revenue']
                annual_est = typical_rev * 365
                print(f"\n  Annual revenue estimate (typical day × 365): ${annual_est:,.0f}")
                print(f"  (Actual annual revenue would be higher due to spike days)")

    print(f"\n  Next step: feed dp_dispatch_*.csv into OpenDSS as a Loadshape")
    print(f"  to verify network feasibility (voltage limits, line loading).")


if __name__ == '__main__':
    main()