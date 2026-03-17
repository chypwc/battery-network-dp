
import numpy as np

class DPSolver:
    """
    Backward-induction DP solver for battery arbitrage.

    Discretises the state space (SoC) and action space,
    solves backward to get the value function and policy,
    then simulates forward to produce a dispatch schedule.
    """
    def __init__(self, battery, dt_hours=0.5, n_soc=41, n_actions=41, dispatch_limit=None):
        self.battery = battery
        self.dt = dt_hours
        self.n_soc = n_soc
        self.n_actions = n_actions
        
        self.soc_grid = np.linspace(battery.soc_min, battery.soc_max, n_soc)
        
        max_power = dispatch_limit if dispatch_limit else battery.kw_rated
        self.action_grid = np.linspace(-max_power, max_power, n_actions)
        self.dispatch_limit = max_power

    def _interp_value(self, value_array, soc):
        return np.interp(soc, self.soc_grid, value_array)

    
    def solve(self, prices, initial_soc=None):
        """
        Solve unconstrained DP.

        Args:
            prices: array of spot prices ($/MWh), length T
            initial_soc: starting SoC in kWh (default: 50%)

        Returns:
            dict: dispatch, soc, revenue, total_revenue, prices
        """
        return self._solve_internal(prices, initial_soc, constraints=None)

    def solve_constrained(self, prices, constraints, initial_soc=None):
        """
        Solve DP with network constraints.

        Args:
            prices: array of spot prices ($/MWh), length T
            constraints: dict with min_discharge, max_charge, min_soc arrays
            initial_soc: starting SoC in kWh (default: 50%)

        Returns:
            dict: dispatch, soc, revenue, total_revenue, prices
        """
        return self._solve_internal(prices, initial_soc, constraints)
        
    
    def _solve_internal(self, prices, initial_soc, constraints):
        """
        backward recursion:
        V_{T-1} (s) = max_a [ r(s, a, p_{T-1} ) + V_T (s') ] <-- use V_T to compute V_{T-1}
        
        forward pass: 
        obtain optimal actions and corresponding soc for each time
        """
        if initial_soc is None:
            initial_soc = self.battery.kwh_rated / 2

        T = len(prices)
        b = self.battery
        dt = self.dt

        # Unpack constraints
        if constraints:
            min_discharge = constraints['min_discharge']
            max_charge = constraints['max_charge']
            min_soc = constraints['min_soc']
        else:
            min_discharge = np.zeros(T)
            max_charge = np.full(T, self.dispatch_limit)
            min_soc = np.full(T, b.soc_min)

        # Value and policy tables
        V = np.zeros((T+1, self.n_soc))      # 0, ..., T
        policy = np.zeros((T, self.n_soc))   

        # ---- Backward pass: t = T-1 down to 0 ----
        for t in range(T-1, -1, -1):
            for i, soc in enumerate(self.soc_grid):
                # Try all feasible actions, keep the best
                feasible = b.feasible_actions(soc, dt, self.action_grid)

                if len(feasible) == 0:
                    continue
                
                # Apply network constraints as mask
                mask = np.ones(len(feasible), dtype=bool)

                # Force discharge (undervoltage): keep only actions ≤ min_discharge[t]
                if min_discharge[t] < -0.1:
                    mask &= (feasible <= min_discharge[t])

                # Limit charge (overvoltage): keep only actions ≤ max_charge[t]
                mask &= (feasible <= max_charge[t])

                # Min SoC: keep only actions where SoC ≥ min_soc[t+1]
                if t + 1 < T:
                    s_next_all = b.next_soc(soc, feasible, dt)
                    mask &= (s_next_all >= min_soc[t + 1])
                
                feasible = feasible[mask]

                if len(feasible) == 0:
                    # Fallback if constraints eliminate everything
                    fallback = min_discharge[t] if min_discharge[t] < -0.1 else 0
                    s_next_fb = b.next_soc(soc, fallback, dt)
                    s_next_fb = max(b.soc_min, min(b.soc_max, float(s_next_fb)))
                    V[t][i] = b.reward(fallback, prices[t], dt) \
                                + np.interp(s_next_fb, self.soc_grid, V[t+1])
                    policy[t][i] = fallback
                    continue

                s_next = b.next_soc(soc, feasible, dt)
                rewards = b.reward(feasible, prices[t], dt)

                # interpolate future value for all next states for each action
                v_futures = np.interp(s_next, self.soc_grid, V[t+1])

                # Total value for each action
                totals = rewards + v_futures

                # Best action
                best_idx = np.argmax(totals)
                V[t][i] = totals[best_idx]
                policy[t][i] = feasible[best_idx]

        # ---- Forward pass ----
        if initial_soc is None:
            initial_soc = b.kwh_rated / 2

        dispatch = np.zeros(T)
        soc_trajectory = np.zeros(T + 1)
        revenue = np.zeros(T)
        soc_trajectory[0] = initial_soc

        for t in range(T):
            soc = soc_trajectory[t]
            action = np.interp(soc, self.soc_grid, policy[t])
            feasible = b.feasible_actions(soc, dt, self.action_grid)

            if len(feasible) > 0:
                # Apply constraints in forward pass 
                if constraints:
                    fmask = np.ones(len(feasible), dtype=bool)
                    if min_discharge[t] < -0.1:
                        fmask &= (feasible <= min_discharge[t])
                    fmask &= (feasible <= max_charge[t])
                    constrained = feasible[fmask]
                    if len(constrained) > 0:
                        feasible = constrained

                action = feasible[np.argmin(np.abs(feasible - action))]
            else:
                action = 0

            dispatch[t] = action
            soc_trajectory[t + 1] = b.next_soc(soc, action, dt)
            # ensure s' feasible given the interpolated action
            soc_trajectory[t + 1] = max(b.soc_min, min(b.soc_max, float(soc_trajectory[t+1])))
            revenue[t] = b.reward(action, prices[t], dt)

        return {
            'dispatch': dispatch,
            'soc': soc_trajectory,
            'revenue': revenue,
            'total_revenue': np.sum(revenue),
            'prices': prices,
        }

if __name__ == '__main__':
    import numpy as np
    from battery import Battery

    b = Battery(kwh_rated=200, kw_rated=100)

    # ---- Test: 8 periods, low then high prices ----
    prices = np.array([20.0, 20.0, 20.0, 20.0, 200.0, 200.0, 200.0, 200.0])

    # ---- Test with finer grids ----
    for n in [41, 81, 161]:
        solver = DPSolver(b, dispatch_limit=50, n_soc=n, n_actions=n)
        result = solver.solve(prices, initial_soc=100)
        d = result['dispatch']
        charge = sum(a * 0.5 for a in d if a > 0)
        discharge = sum(-a * 0.5 for a in d if a < 0)
        print(f"  n={n:<4}  revenue=${result['total_revenue']:.2f}  "
              f"charge={charge:.1f}kWh  discharge={discharge:.1f}kWh  "
              f"dispatch={[f'{a:+.0f}' for a in d]}")