import numpy as np

class Battery:
    def __init__(self, kwh_rated=200, kw_rated=100, eff_charge=0.95, eff_discharge=0.95, reserve_pct=10, degradation=0.02):
        """
        kwh_rated: total battery capacity
        kw_rated: max charge/discharge power
        eff_charge, eff_discharge, : charge/discharge efficiency
        reserve_pct: battery reserve rate
        degradation: cost per kWh throughput
        """
        self.kwh_rated = kwh_rated
        self.kw_rated = kw_rated
        self.eta_c = eff_charge             # charging efficiency η_c 
        self.eta_d = eff_discharge          # discharging efficiency η_d
        self.soc_min = kwh_rated * reserve_pct / 100
        self.soc_max = kwh_rated
        self.degradation = degradation      # $/kWh throughput


    def next_soc(self, soc, action_kw, dt_hours):
        """
        The state transition.
        Charging (a > 0): s' = s + η_c · a · Δt
        Discharging (a < 0): s' = s + a · Δt / η_d
        """
        action_kw = np.asarray(action_kw)
        return np.where(
            action_kw >= 0,
            soc + self.eta_c * action_kw * dt_hours,      # charging
            soc + action_kw * dt_hours / self.eta_d,       # discharging
        )

    def feasible_actions(self, soc, dt_hours, action_grid):
        """
        Keep only actions where 
        1. |action| ≤ kw_rated, and
        2. soc_min ≤ next_soc ≤ soc_max
        """
        action_grid = np.asarray(action_grid)
        s_next = self.next_soc(soc, action_grid, dt_hours)
        mask = (np.abs(action_grid) <= self.kw_rated) & \
               (s_next >= self.soc_min) & \
               (s_next <= self.soc_max)
        return action_grid[mask]

    def reward(self, action_kw, price, dt_hours):
        return - price / 1000 * action_kw * dt_hours - self.degradation * np.abs(action_kw) * dt_hours
    
    def __repr__(self):
        return (f"Battery(capacity: {self.kwh_rated}kWh / power rated: {self.kw_rated}kW, "
                f"charging/discharging efficiency η_c={self.eta_c}, η_d={self.eta_d})")
    

if __name__=="__main__":
    b = Battery()
    actions = np.linspace(-100, 100, 41)

    # next_soc: scalar
    print(b.next_soc(100, 60, 0.5))          # expect 128.5

    # next_soc: vector
    print(b.next_soc(100, actions[:5], 0.5))  # array of 5 values

    # reward: vector
    print(b.reward(actions[:5], 150, 0.5))    # array of 5 revenues

    # feasible_actions: vectorised
    f = b.feasible_actions(100, 0.5, actions)
    print(f"Feasible: {len(f)} actions, {f.min():.0f} to {f.max():.0f} kW")