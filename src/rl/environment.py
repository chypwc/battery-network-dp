import numpy as np
from src.opendss import network
from src.opendss.feeders import FEEDER_32
from src.dp.battery import Battery

class CommunityBatteryEnv:

    def __init__(self, prices, load_profile, solar_profile,
                 dss_file=None, dispatch_limit=50,
                 violation_penalty=10, battery_kwh=200,
                 n_actions=21,
                 skip_network=False):
        
        self.battery = Battery(kwh_rated=battery_kwh)
        self.prices = prices
        self.T = len(prices)
        self.load_profile = load_profile
        self.solar_profile = solar_profile
        self.dt = 0.5

        self.dss_file = dss_file if dss_file else FEEDER_32['dss_file']

        self.action_values = np.linspace(-dispatch_limit, dispatch_limit, n_actions)
        self.n_actions = len(self.action_values)

        self.penalty = violation_penalty
        self.skip_network = skip_network

    def reset(self, ):
        """Start a new episode."""
        network.load_circuit(self.dss_file)
        network.enable_battery()
        if self.battery.kwh_rated != 200:
            network.set_battery_capacity(self.battery.kwh_rated)
        
        self.t = 0
        self.soc = self.battery.kwh_rated / 2 # initial soc
        return (self.soc, self.t)

    def step(self, action_idx):
        action_kw = self.action_values[action_idx]
        s_next = self.battery.next_soc(self.soc, action_kw, self.dt)

        # If infeasible, find nearest feasible action instead of idling
        if s_next < self.battery.soc_min or s_next > self.battery.soc_max:
            feasible = self.battery.feasible_actions(self.soc, self.dt, self.action_values)
            if len(feasible) > 0:
                action_kw = feasible[np.argmin(np.abs(feasible - action_kw))]
                s_next = self.battery.next_soc(self.soc, action_kw, self.dt)
            else:
                action_kw = 0.0
                s_next = self.soc
        # Only call OpenDSS if needed
        if self.skip_network:
            n_violation = 0
            v_min = 1.0
            v_max = 1.0
        else:
            network.set_loads(FEEDER_32['load_names'], self.load_profile[self.t])
            network.set_solar(FEEDER_32['pv_names'],
                              FEEDER_32['pv_rated_kw'],
                              self.solar_profile[self.t])
            network.set_battery(action_kw)
            r = network.solve_and_read()

            n_violation = 0
            for name, pu_list in r['bus_voltages'].items():
                for v in pu_list:
                    if 0 < v < 2.0:
                        if v < 0.94 or v > 1.10:
                            n_violation += 1
            v_min = r['v_min']
            v_max = r['v_max']

        revenue = float(self.battery.reward(action_kw, self.prices[self.t], self.dt))
        reward = revenue - self.penalty * n_violation

        self.soc = float(s_next)
        self.t += 1
        done = (self.t >= self.T)

        info = {
            'revenue': float(revenue),
            'violations': n_violation,
            'action_kw': action_kw,
            'v_min': v_min,
            'v_max': v_max,
        }

        return (self.soc, self.t), reward, done, info


if __name__ == '__main__':
    from src.dp.prices import load_day_prices
    from src.opendss.profiles import generate_load_profile, generate_solar_profile

    prices = load_day_prices('data/aemo/prices_typical_2024-06-28.csv')
    load_profile = generate_load_profile()
    solar_profile = generate_solar_profile()

    env = CommunityBatteryEnv(prices, load_profile, solar_profile)

    # Run one episode with random actions
    state = env.reset()
    total_reward = 0
    total_revenue = 0
    total_violations = 0

    for t in range(48):
        action_idx = np.random.randint(env.n_actions)  # random action
        next_state, reward, done, info = env.step(action_idx)
        total_reward += reward
        total_revenue += info['revenue']
        total_violations += info['violations']

        soc, step = next_state
        print(f"  t={t:>2}  action={info['action_kw']:+6.1f}kW  "
              f"SoC={soc:6.1f}  reward={reward:+7.2f}  "
              f"violations={info['violations']}  V_min={info['v_min']:.4f}")

    print(f"\nEpisode summary:")
    print(f"  Total reward:     {total_reward:.2f}")
    print(f"  Total revenue:    {total_revenue:.2f}")
    print(f"  Total violations: {total_violations}")