import numpy as np
from dp.battery import Battery

def test_next_soc():
    b = Battery()
    print(b.kwh_rated, b.kw_rated, b.soc_min, b.soc_max)
    assert abs(b.next_soc(100, 60, 0.5) - 128.5) < 1e-6
    assert abs(b.next_soc(100, -80, 0.5) - 57.8947) < 1e-3

def test_reward():
    b = Battery()
    assert abs(b.reward(-80, 150, 0.5) - 5.2) < 1e-4   # expect ~$5.20 (sell at $150)
    assert abs(b.reward(60, 20, 0.5) - (-1.2)) < 1e-4     # expect ~-$1.20 (buy at $20)


def test_feasible_actions():
    b = Battery()
    actions = np.linspace(-200, 200, 41)
    f = b.feasible_actions(180, 0.5, actions)
    print(f"Feasible from SoC=180: {len(f)} actions, range {min(f):.0f} to {max(f):.0f}")
    assert all(abs(a) <= b.kw_rated for a in f)
    assert all(b.soc_min <= b.next_soc(180, a, 0.5) <= b.soc_max for a in f)
