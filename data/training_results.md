 Episode 45000/50000  avg_reward=   29.55  avg_violations=  0.0  epsilon=0.060
  Episode 47500/50000  avg_reward=   30.57  avg_violations=  0.0  epsilon=0.055
  Episode 50000/50000  avg_reward=   30.66  avg_violations=  0.0  epsilon=0.050
  Phase 1 result: revenue=$30.66, violations=0.0

  Phase 2: Learning violation avoidance (penalty=5.0, 50000 episodes)
  Episode 2500/50000  avg_reward=   15.43  avg_violations=  2.8  epsilon=0.086
  Episode 5000/50000  avg_reward=   17.75  avg_violations=  2.2  epsilon=0.074
  Episode 7500/50000  avg_reward=   21.16  avg_violations=  1.8  epsilon=0.064
  Episode 10000/50000  avg_reward=   23.03  avg_violations=  1.4  epsilon=0.055
  Episode 12500/50000  avg_reward=   24.93  avg_violations=  1.2  epsilon=0.047
  Episode 15000/50000  avg_reward=   28.04  avg_violations=  0.6  epsilon=0.041
  Episode 17500/50000  avg_reward=   27.12  avg_violations=  0.8  epsilon=0.035
  Episode 20000/50000  avg_reward=   28.99  avg_violations=  0.5  epsilon=0.030
  Episode 22500/50000  avg_reward=   30.43  avg_violations=  0.2  epsilon=0.026
  Episode 25000/50000  avg_reward=   28.12  avg_violations=  0.6  epsilon=0.022
  Episode 27500/50000  avg_reward=   27.93  avg_violations=  0.8  epsilon=0.019
  Episode 30000/50000  avg_reward=   29.84  avg_violations=  0.4  epsilon=0.017
  Episode 32500/50000  avg_reward=   29.69  avg_violations=  0.5  epsilon=0.014
  Episode 35000/50000  avg_reward=   30.24  avg_violations=  0.3  epsilon=0.012
  Episode 37500/50000  avg_reward=   31.01  avg_violations=  0.2  epsilon=0.011
  Episode 40000/50000  avg_reward=   31.78  avg_violations=  0.1  epsilon=0.009
  Episode 42500/50000  avg_reward=   31.90  avg_violations=  0.1  epsilon=0.008
  Episode 45000/50000  avg_reward=   31.94  avg_violations=  0.1  epsilon=0.007
  Episode 47500/50000  avg_reward=   31.12  avg_violations=  0.3  epsilon=0.006
  Episode 50000/50000  avg_reward=   31.80  avg_violations=  0.1  epsilon=0.005
  Phase 2 result: revenue=$32.50, violations=0.1

  Phase 2 training summary:
  Episodes trained:        50000
  Avg reward (last 50):    31.80
  Avg revenue (last 50):   $32.50
  Avg violations (last 50): 0.1
  Zero-violation episodes:  94%

  Summary (RL ±50kW 300kWh):
    Voltage range:      0.9416 – 1.0768 pu
    Voltage violations: 0 of 48 periods
    Total losses:       61.60 kWh
    Peak Tx loading:    52.2%
    Avg Tx loading:     25.3%

======================================================================
  ±50 kW dispatch, 400 kWh capacity
======================================================================

  --- DP Solver ---
  Revenue: $35.92

  Summary (DP ±50kW 400kWh):
    Voltage range:      0.9436 – 1.0768 pu
    Voltage violations: 0 of 48 periods
    Total losses:       61.03 kWh
    Peak Tx loading:    52.2%
    Avg Tx loading:     24.9%

  --- Q-Learning (two-phase, warm-started from DP) ---
  Q-table initialised from DP value function
  Phase 1: Refining arbitrage (penalty=0.0, 50000 episodes)
  Episode 2500/50000  avg_reward=   24.09  avg_violations=  0.0  epsilon=0.274
  Episode 5000/50000  avg_reward=   25.56  avg_violations=  0.0  epsilon=0.251
  Episode 7500/50000  avg_reward=   24.91  avg_violations=  0.0  epsilon=0.229
  Episode 10000/50000  avg_reward=   26.69  avg_violations=  0.0  epsilon=0.210
  Episode 12500/50000  avg_reward=   26.52  avg_violations=  0.0  epsilon=0.192
  Episode 15000/50000  avg_reward=   27.74  avg_violations=  0.0  epsilon=0.175
  Episode 17500/50000  avg_reward=   27.56  avg_violations=  0.0  epsilon=0.160
  Episode 20000/50000  avg_reward=   29.59  avg_violations=  0.0  epsilon=0.147
  Episode 22500/50000  avg_reward=   29.46  avg_violations=  0.0  epsilon=0.134
  Episode 25000/50000  avg_reward=   31.29  avg_violations=  0.0  epsilon=0.122
  Episode 27500/50000  avg_reward=   30.64  avg_violations=  0.0  epsilon=0.112
  Episode 30000/50000  avg_reward=   31.17  avg_violations=  0.0  epsilon=0.102
  Episode 32500/50000  avg_reward=   31.16  avg_violations=  0.0  epsilon=0.094
  Episode 35000/50000  avg_reward=   32.08  avg_violations=  0.0  epsilon=0.086
  Episode 37500/50000  avg_reward=   32.94  avg_violations=  0.0  epsilon=0.078
  Episode 40000/50000  avg_reward=   32.67  avg_violations=  0.0  epsilon=0.072
  Episode 42500/50000  avg_reward=   33.67  avg_violations=  0.0  epsilon=0.065
  Episode 45000/50000  avg_reward=   33.63  avg_violations=  0.0  epsilon=0.060
  Episode 47500/50000  avg_reward=   33.46  avg_violations=  0.0  epsilon=0.055
  Episode 50000/50000  avg_reward=   33.29  avg_violations=  0.0  epsilon=0.050
  Phase 1 result: revenue=$33.29, violations=0.0

  Phase 2: Learning violation avoidance (penalty=5.0, 50000 episodes)
  Episode 2500/50000  avg_reward=   17.16  avg_violations=  3.0  epsilon=0.086
  Episode 5000/50000  avg_reward=   24.61  avg_violations=  1.6  epsilon=0.074
  Episode 7500/50000  avg_reward=   23.71  avg_violations=  1.9  epsilon=0.064
  Episode 10000/50000  avg_reward=   28.70  avg_violations=  1.0  epsilon=0.055
  Episode 12500/50000  avg_reward=   28.75  avg_violations=  1.0  epsilon=0.047
  Episode 15000/50000  avg_reward=   31.35  avg_violations=  0.5  epsilon=0.041
  Episode 17500/50000  avg_reward=   26.34  avg_violations=  1.4  epsilon=0.035
  Episode 20000/50000  avg_reward=   28.35  avg_violations=  1.2  epsilon=0.030
  Episode 22500/50000  avg_reward=   33.22  avg_violations=  0.4  epsilon=0.026
  Episode 25000/50000  avg_reward=   34.32  avg_violations=  0.2  epsilon=0.022
  Episode 27500/50000  avg_reward=   31.87  avg_violations=  0.6  epsilon=0.019
  Episode 30000/50000  avg_reward=   31.60  avg_violations=  0.6  epsilon=0.017
  Episode 32500/50000  avg_reward=   31.62  avg_violations=  0.7  epsilon=0.014
  Episode 35000/50000  avg_reward=   33.40  avg_violations=  0.4  epsilon=0.012
  Episode 37500/50000  avg_reward=   35.31  avg_violations=  0.0  epsilon=0.011
  Episode 40000/50000  avg_reward=   34.54  avg_violations=  0.2  epsilon=0.009
  Episode 42500/50000  avg_reward=   34.73  avg_violations=  0.2  epsilon=0.008
  Episode 45000/50000  avg_reward=   34.36  avg_violations=  0.3  epsilon=0.007
  Episode 47500/50000  avg_reward=   33.76  avg_violations=  0.4  epsilon=0.006
  Episode 50000/50000  avg_reward=   35.56  avg_violations=  0.0  epsilon=0.005
  Phase 2 result: revenue=$35.66, violations=0.0

  Phase 2 training summary:
  Episodes trained:        50000
  Avg reward (last 50):    35.56
  Avg revenue (last 50):   $35.66
  Avg violations (last 50): 0.0
  Zero-violation episodes:  98%

  Summary (RL ±50kW 400kWh):
    Voltage range:      0.9455 – 1.0768 pu
    Voltage violations: 0 of 48 periods
    Total losses:       60.86 kWh
    Peak Tx loading:    52.2%
    Avg Tx loading:     24.8%

======================================================================
  ±80 kW dispatch, 200 kWh capacity
======================================================================

  --- DP Solver ---
  Revenue: $36.89

  Summary (DP ±80kW 200kWh):
    Voltage range:      0.9264 – 1.0960 pu
    Voltage violations: 6 of 48 periods
    Violation times:    06:00, 18:30, 19:00, 19:30, 20:00, 20:30
    Total losses:       70.28 kWh
    Peak Tx loading:    65.0%
    Avg Tx loading:     26.3%

  --- Q-Learning (two-phase, warm-started from DP) ---
  Q-table initialised from DP value function
  Phase 1: Refining arbitrage (penalty=0.0, 50000 episodes)
  Episode 2500/50000  avg_reward=   21.83  avg_violations=  0.0  epsilon=0.274
  Episode 5000/50000  avg_reward=   24.48  avg_violations=  0.0  epsilon=0.251
  Episode 7500/50000  avg_reward=   24.87  avg_violations=  0.0  epsilon=0.229
  Episode 10000/50000  avg_reward=   27.23  avg_violations=  0.0  epsilon=0.210
  Episode 12500/50000  avg_reward=   27.11  avg_violations=  0.0  epsilon=0.192
  Episode 15000/50000  avg_reward=   28.16  avg_violations=  0.0  epsilon=0.175
  Episode 17500/50000  avg_reward=   27.29  avg_violations=  0.0  epsilon=0.160
  Episode 20000/50000  avg_reward=   27.83  avg_violations=  0.0  epsilon=0.147
  Episode 22500/50000  avg_reward=   29.09  avg_violations=  0.0  epsilon=0.134
  Episode 25000/50000  avg_reward=   30.14  avg_violations=  0.0  epsilon=0.122
  Episode 27500/50000  avg_reward=   31.76  avg_violations=  0.0  epsilon=0.112
  Episode 30000/50000  avg_reward=   31.93  avg_violations=  0.0  epsilon=0.102
  Episode 32500/50000  avg_reward=   32.33  avg_violations=  0.0  epsilon=0.094
  Episode 35000/50000  avg_reward=   32.93  avg_violations=  0.0  epsilon=0.086
  Episode 37500/50000  avg_reward=   32.46  avg_violations=  0.0  epsilon=0.078
  Episode 40000/50000  avg_reward=   32.83  avg_violations=  0.0  epsilon=0.072
  Episode 42500/50000  avg_reward=   33.85  avg_violations=  0.0  epsilon=0.065
  Episode 45000/50000  avg_reward=   33.61  avg_violations=  0.0  epsilon=0.060
  Episode 47500/50000  avg_reward=   33.49  avg_violations=  0.0  epsilon=0.055
  Episode 50000/50000  avg_reward=   34.01  avg_violations=  0.0  epsilon=0.050
  Phase 1 result: revenue=$34.01, violations=0.0

  Phase 2: Learning violation avoidance (penalty=5.0, 50000 episodes)
  Episode 2500/50000  avg_reward=   14.68  avg_violations=  2.9  epsilon=0.086
  Episode 5000/50000  avg_reward=   20.60  avg_violations=  1.7  epsilon=0.074
  Episode 7500/50000  avg_reward=   21.97  avg_violations=  1.7  epsilon=0.064
  Episode 10000/50000  avg_reward=   25.75  avg_violations=  1.0  epsilon=0.055
  Episode 12500/50000  avg_reward=   26.25  avg_violations=  0.9  epsilon=0.047
  Episode 15000/50000  avg_reward=   26.22  avg_violations=  1.1  epsilon=0.041
  Episode 17500/50000  avg_reward=   27.27  avg_violations=  0.7  epsilon=0.035
  Episode 20000/50000  avg_reward=   27.71  avg_violations=  0.8  epsilon=0.030
  Episode 22500/50000  avg_reward=   31.17  avg_violations=  0.1  epsilon=0.026
  Episode 25000/50000  avg_reward=   28.07  avg_violations=  0.8  epsilon=0.022
  Episode 27500/50000  avg_reward=   30.30  avg_violations=  0.3  epsilon=0.019
  Episode 30000/50000  avg_reward=   30.58  avg_violations=  0.3  epsilon=0.017
  Episode 32500/50000  avg_reward=   28.69  avg_violations=  0.7  epsilon=0.014
  Episode 35000/50000  avg_reward=   31.93  avg_violations=  0.1  epsilon=0.012
  Episode 37500/50000  avg_reward=   31.79  avg_violations=  0.1  epsilon=0.011
  Episode 40000/50000  avg_reward=   31.41  avg_violations=  0.3  epsilon=0.009
  Episode 42500/50000  avg_reward=   32.12  avg_violations=  0.2  epsilon=0.008
  Episode 45000/50000  avg_reward=   32.96  avg_violations=  0.0  epsilon=0.007
  Episode 47500/50000  avg_reward=   32.71  avg_violations=  0.1  epsilon=0.006
  Episode 50000/50000  avg_reward=   32.99  avg_violations=  0.0  epsilon=0.005
  Phase 2 result: revenue=$33.19, violations=0.0

  Phase 2 training summary:
  Episodes trained:        50000
  Avg reward (last 50):    32.99
  Avg revenue (last 50):   $33.19
  Avg violations (last 50): 0.0
  Zero-violation episodes:  98%

  Summary (RL ±80kW 200kWh):
    Voltage range:      0.9264 – 1.0960 pu
    Voltage violations: 1 of 48 periods
    Violation times:    20:30
    Total losses:       64.77 kWh
    Peak Tx loading:    65.0%
    Avg Tx loading:     24.4%

======================================================================
  ±80 kW dispatch, 300 kWh capacity
======================================================================

  --- DP Solver ---
  Revenue: $44.02

  Summary (DP ±80kW 300kWh):
    Voltage range:      0.9264 – 1.0960 pu
    Voltage violations: 4 of 48 periods
    Violation times:    06:00, 19:30, 20:00, 20:30
    Total losses:       75.34 kWh
    Peak Tx loading:    65.0%
    Avg Tx loading:     26.8%

  --- Q-Learning (two-phase, warm-started from DP) ---
  Q-table initialised from DP value function
  Phase 1: Refining arbitrage (penalty=0.0, 50000 episodes)
  Episode 2500/50000  avg_reward=   27.08  avg_violations=  0.0  epsilon=0.274
  Episode 5000/50000  avg_reward=   28.74  avg_violations=  0.0  epsilon=0.251
  Episode 7500/50000  avg_reward=   31.44  avg_violations=  0.0  epsilon=0.229
  Episode 10000/50000  avg_reward=   32.79  avg_violations=  0.0  epsilon=0.210
  Episode 12500/50000  avg_reward=   31.82  avg_violations=  0.0  epsilon=0.192
  Episode 15000/50000  avg_reward=   35.51  avg_violations=  0.0  epsilon=0.175
  Episode 17500/50000  avg_reward=   35.62  avg_violations=  0.0  epsilon=0.160
  Episode 20000/50000  avg_reward=   35.45  avg_violations=  0.0  epsilon=0.147
  Episode 22500/50000  avg_reward=   35.15  avg_violations=  0.0  epsilon=0.134
  Episode 25000/50000  avg_reward=   36.93  avg_violations=  0.0  epsilon=0.122
  Episode 27500/50000  avg_reward=   36.97  avg_violations=  0.0  epsilon=0.112
  Episode 30000/50000  avg_reward=   38.49  avg_violations=  0.0  epsilon=0.102
  Episode 32500/50000  avg_reward=   38.66  avg_violations=  0.0  epsilon=0.094
  Episode 35000/50000  avg_reward=   39.13  avg_violations=  0.0  epsilon=0.086
  Episode 37500/50000  avg_reward=   39.51  avg_violations=  0.0  epsilon=0.078
  Episode 40000/50000  avg_reward=   40.48  avg_violations=  0.0  epsilon=0.072
  Episode 42500/50000  avg_reward=   40.95  avg_violations=  0.0  epsilon=0.065
  Episode 45000/50000  avg_reward=   40.92  avg_violations=  0.0  epsilon=0.060
  Episode 47500/50000  avg_reward=   40.38  avg_violations=  0.0  epsilon=0.055
  Episode 50000/50000  avg_reward=   40.41  avg_violations=  0.0  epsilon=0.050
  Phase 1 result: revenue=$40.41, violations=0.0

  Phase 2: Learning violation avoidance (penalty=5.0, 50000 episodes)
  Episode 2500/50000  avg_reward=   32.82  avg_violations=  1.1  epsilon=0.086
  Episode 5000/50000  avg_reward=   32.24  avg_violations=  1.1  epsilon=0.074
  Episode 7500/50000  avg_reward=   33.18  avg_violations=  1.2  epsilon=0.064
  Episode 10000/50000  avg_reward=   36.26  avg_violations=  0.6  epsilon=0.055
  Episode 12500/50000  avg_reward=   35.36  avg_violations=  0.9  epsilon=0.047
  Episode 15000/50000  avg_reward=   35.19  avg_violations=  1.1  epsilon=0.041
  Episode 17500/50000  avg_reward=   37.13  avg_violations=  0.8  epsilon=0.035
  Episode 20000/50000  avg_reward=   39.01  avg_violations=  0.5  epsilon=0.030
  Episode 22500/50000  avg_reward=   40.56  avg_violations=  0.2  epsilon=0.026
  Episode 25000/50000  avg_reward=   39.34  avg_violations=  0.3  epsilon=0.022
  Episode 27500/50000  avg_reward=   39.85  avg_violations=  0.2  epsilon=0.019
  Episode 30000/50000  avg_reward=   40.70  avg_violations=  0.1  epsilon=0.017
  Episode 32500/50000  avg_reward=   40.44  avg_violations=  0.2  epsilon=0.014
  Episode 35000/50000  avg_reward=   41.44  avg_violations=  0.0  epsilon=0.012
  Episode 37500/50000  avg_reward=   41.08  avg_violations=  0.2  epsilon=0.011
  Episode 40000/50000  avg_reward=   41.28  avg_violations=  0.1  epsilon=0.009
  Episode 42500/50000  avg_reward=   41.28  avg_violations=  0.2  epsilon=0.008
  Episode 45000/50000  avg_reward=   42.16  avg_violations=  0.0  epsilon=0.007
  Episode 47500/50000  avg_reward=   41.47  avg_violations=  0.0  epsilon=0.006
  Episode 50000/50000  avg_reward=   41.63  avg_violations=  0.1  epsilon=0.005
  Phase 2 result: revenue=$42.03, violations=0.1

  Phase 2 training summary:
  Episodes trained:        50000
  Avg reward (last 50):    41.63
  Avg revenue (last 50):   $42.03
  Avg violations (last 50): 0.1
  Zero-violation episodes:  96%

  Summary (RL ±80kW 300kWh):
    Voltage range:      0.9264 – 1.0960 pu
    Voltage violations: 1 of 48 periods
    Violation times:    20:30
    Total losses:       69.51 kWh
    Peak Tx loading:    65.0%
    Avg Tx loading:     24.8%

======================================================================
  ±80 kW dispatch, 400 kWh capacity
======================================================================

  --- DP Solver ---
  Revenue: $49.01

  Summary (DP ±80kW 400kWh):
    Voltage range:      0.9264 – 1.0960 pu
    Voltage violations: 3 of 48 periods
    Violation times:    06:00, 19:30, 20:30
    Total losses:       80.86 kWh
    Peak Tx loading:    65.0%
    Avg Tx loading:     27.2%

  --- Q-Learning (two-phase, warm-started from DP) ---
  Q-table initialised from DP value function
  Phase 1: Refining arbitrage (penalty=0.0, 50000 episodes)
  Episode 2500/50000  avg_reward=   29.35  avg_violations=  0.0  epsilon=0.274
  Episode 5000/50000  avg_reward=   34.48  avg_violations=  0.0  epsilon=0.251
  Episode 7500/50000  avg_reward=   34.87  avg_violations=  0.0  epsilon=0.229
  Episode 10000/50000  avg_reward=   35.87  avg_violations=  0.0  epsilon=0.210
  Episode 12500/50000  avg_reward=   37.87  avg_violations=  0.0  epsilon=0.192
  Episode 15000/50000  avg_reward=   38.48  avg_violations=  0.0  epsilon=0.175
  Episode 17500/50000  avg_reward=   38.54  avg_violations=  0.0  epsilon=0.160
  Episode 20000/50000  avg_reward=   39.69  avg_violations=  0.0  epsilon=0.147
  Episode 22500/50000  avg_reward=   41.19  avg_violations=  0.0  epsilon=0.134
  Episode 25000/50000  avg_reward=   41.81  avg_violations=  0.0  epsilon=0.122
  Episode 27500/50000  avg_reward=   43.34  avg_violations=  0.0  epsilon=0.112
  Episode 30000/50000  avg_reward=   42.56  avg_violations=  0.0  epsilon=0.102
  Episode 32500/50000  avg_reward=   43.31  avg_violations=  0.0  epsilon=0.094
  Episode 35000/50000  avg_reward=   44.26  avg_violations=  0.0  epsilon=0.086
  Episode 37500/50000  avg_reward=   44.47  avg_violations=  0.0  epsilon=0.078
  Episode 40000/50000  avg_reward=   44.87  avg_violations=  0.0  epsilon=0.072
  Episode 42500/50000  avg_reward=   44.32  avg_violations=  0.0  epsilon=0.065
  Episode 45000/50000  avg_reward=   45.55  avg_violations=  0.0  epsilon=0.060
  Episode 47500/50000  avg_reward=   45.93  avg_violations=  0.0  epsilon=0.055
  Episode 50000/50000  avg_reward=   46.38  avg_violations=  0.0  epsilon=0.050
  Phase 1 result: revenue=$46.38, violations=0.0

  Phase 2: Learning violation avoidance (penalty=5.0, 50000 episodes)
  Episode 2500/50000  avg_reward=   34.74  avg_violations=  1.6  epsilon=0.086
  Episode 5000/50000  avg_reward=   37.70  avg_violations=  1.3  epsilon=0.074
  Episode 7500/50000  avg_reward=   40.66  avg_violations=  0.9  epsilon=0.064
  Episode 10000/50000  avg_reward=   40.63  avg_violations=  0.9  epsilon=0.055
  Episode 12500/50000  avg_reward=   39.15  avg_violations=  1.2  epsilon=0.047
  Episode 15000/50000  avg_reward=   39.64  avg_violations=  1.2  epsilon=0.041
  Episode 17500/50000  avg_reward=   44.75  avg_violations=  0.4  epsilon=0.035
  Episode 20000/50000  avg_reward=   44.29  avg_violations=  0.4  epsilon=0.030
  Episode 22500/50000  avg_reward=   43.56  avg_violations=  0.6  epsilon=0.026
  Episode 25000/50000  avg_reward=   45.92  avg_violations=  0.4  epsilon=0.022
  Episode 27500/50000  avg_reward=   47.24  avg_violations=  0.1  epsilon=0.019
  Episode 30000/50000  avg_reward=   47.99  avg_violations=  0.0  epsilon=0.017
  Episode 32500/50000  avg_reward=   46.90  avg_violations=  0.2  epsilon=0.014
  Episode 35000/50000  avg_reward=   47.92  avg_violations=  0.0  epsilon=0.012
  Episode 37500/50000  avg_reward=   47.32  avg_violations=  0.1  epsilon=0.011
  Episode 40000/50000  avg_reward=   46.51  avg_violations=  0.4  epsilon=0.009
  Episode 42500/50000  avg_reward=   47.70  avg_violations=  0.1  epsilon=0.008
  Episode 45000/50000  avg_reward=   47.80  avg_violations=  0.2  epsilon=0.007
  Episode 47500/50000  avg_reward=   48.16  avg_violations=  0.0  epsilon=0.006
  Episode 50000/50000  avg_reward=   48.49  avg_violations=  0.0  epsilon=0.005
  Phase 2 result: revenue=$48.49, violations=0.0

  Phase 2 training summary:
  Episodes trained:        50000
  Avg reward (last 50):    48.49
  Avg revenue (last 50):   $48.49
  Avg violations (last 50): 0.0
  Zero-violation episodes:  100%

  Summary (RL ±80kW 400kWh):
    Voltage range:      0.9406 – 1.0960 pu
    Voltage violations: 0 of 48 periods
    Total losses:       78.39 kWh
    Peak Tx loading:    65.0%
    Avg Tx loading:     26.6%

======================================================================
  ±100 kW dispatch, 200 kWh capacity
======================================================================

  --- DP Solver ---
  Revenue: $41.18

  Summary (DP ±100kW 200kWh):
    Voltage range:      0.9264 – 1.1100 pu
    Voltage violations: 10 of 48 periods
    Violation times:    06:00, 12:00, 12:30, 13:00, 17:00, 18:30, 19:00, 19:30, 20:00, 20:30
    Total losses:       79.13 kWh
    Peak Tx loading:    73.5%
    Avg Tx loading:     27.8%

  --- Q-Learning (two-phase, warm-started from DP) ---
  Q-table initialised from DP value function
  Phase 1: Refining arbitrage (penalty=0.0, 50000 episodes)
  Episode 2500/50000  avg_reward=   23.24  avg_violations=  0.0  epsilon=0.274
  Episode 5000/50000  avg_reward=   26.18  avg_violations=  0.0  epsilon=0.251
  Episode 7500/50000  avg_reward=   28.51  avg_violations=  0.0  epsilon=0.229
  Episode 10000/50000  avg_reward=   26.67  avg_violations=  0.0  epsilon=0.210
  Episode 12500/50000  avg_reward=   28.67  avg_violations=  0.0  epsilon=0.192
  Episode 15000/50000  avg_reward=   29.86  avg_violations=  0.0  epsilon=0.175
  Episode 17500/50000  avg_reward=   32.17  avg_violations=  0.0  epsilon=0.160
  Episode 20000/50000  avg_reward=   32.22  avg_violations=  0.0  epsilon=0.147
  Episode 22500/50000  avg_reward=   34.31  avg_violations=  0.0  epsilon=0.134
  Episode 25000/50000  avg_reward=   31.56  avg_violations=  0.0  epsilon=0.122
  Episode 27500/50000  avg_reward=   33.85  avg_violations=  0.0  epsilon=0.112
  Episode 30000/50000  avg_reward=   34.90  avg_violations=  0.0  epsilon=0.102
  Episode 32500/50000  avg_reward=   35.68  avg_violations=  0.0  epsilon=0.094
  Episode 35000/50000  avg_reward=   36.49  avg_violations=  0.0  epsilon=0.086
  Episode 37500/50000  avg_reward=   36.54  avg_violations=  0.0  epsilon=0.078
  Episode 40000/50000  avg_reward=   37.34  avg_violations=  0.0  epsilon=0.072
  Episode 42500/50000  avg_reward=   37.01  avg_violations=  0.0  epsilon=0.065
  Episode 45000/50000  avg_reward=   37.02  avg_violations=  0.0  epsilon=0.060
  Episode 47500/50000  avg_reward=   38.13  avg_violations=  0.0  epsilon=0.055
  Episode 50000/50000  avg_reward=   37.40  avg_violations=  0.0  epsilon=0.050
  Phase 1 result: revenue=$37.40, violations=0.0

  Phase 2: Learning violation avoidance (penalty=5.0, 50000 episodes)
  Episode 2500/50000  avg_reward=    3.91  avg_violations=  5.3  epsilon=0.086
  Episode 5000/50000  avg_reward=   21.16  avg_violations=  1.9  epsilon=0.074
  Episode 7500/50000  avg_reward=   21.53  avg_violations=  1.9  epsilon=0.064
  Episode 10000/50000  avg_reward=   25.53  avg_violations=  1.3  epsilon=0.055
  Episode 12500/50000  avg_reward=   27.51  avg_violations=  0.9  epsilon=0.047
  Episode 15000/50000  avg_reward=   22.64  avg_violations=  2.0  epsilon=0.041
  Episode 17500/50000  avg_reward=   27.07  avg_violations=  1.3  epsilon=0.035
  Episode 20000/50000  avg_reward=   32.87  avg_violations=  0.3  epsilon=0.030
  Episode 22500/50000  avg_reward=   31.81  avg_violations=  0.5  epsilon=0.026
  Episode 25000/50000  avg_reward=   29.61  avg_violations=  0.9  epsilon=0.022
  Episode 27500/50000  avg_reward=   30.95  avg_violations=  0.8  epsilon=0.019
  Episode 30000/50000  avg_reward=   31.16  avg_violations=  0.8  epsilon=0.017
  Episode 32500/50000  avg_reward=   32.06  avg_violations=  0.6  epsilon=0.014
  Episode 35000/50000  avg_reward=   34.95  avg_violations=  0.2  epsilon=0.012
  Episode 37500/50000  avg_reward=   34.30  avg_violations=  0.2  epsilon=0.011
  Episode 40000/50000  avg_reward=   35.01  avg_violations=  0.0  epsilon=0.009
  Episode 42500/50000  avg_reward=   35.36  avg_violations=  0.1  epsilon=0.008
  Episode 45000/50000  avg_reward=   35.62  avg_violations=  0.1  epsilon=0.007
  Episode 47500/50000  avg_reward=   33.59  avg_violations=  0.4  epsilon=0.006
  Episode 50000/50000  avg_reward=   35.91  avg_violations=  0.0  epsilon=0.005
  Phase 2 result: revenue=$35.91, violations=0.0

  Phase 2 training summary:
  Episodes trained:        50000
  Avg reward (last 50):    35.91
  Avg revenue (last 50):   $35.91
  Avg violations (last 50): 0.0
  Zero-violation episodes:  100%

  Summary (RL ±100kW 200kWh):
    Voltage range:      0.9264 – 1.0999 pu
    Voltage violations: 2 of 48 periods
    Violation times:    19:30, 20:00
    Total losses:       69.03 kWh
    Peak Tx loading:    67.0%
    Avg Tx loading:     24.9%

======================================================================
  ±100 kW dispatch, 300 kWh capacity
======================================================================

  --- DP Solver ---
  Revenue: $50.17

  Summary (DP ±100kW 300kWh):
    Voltage range:      0.9264 – 1.1100 pu
    Voltage violations: 9 of 48 periods
    Violation times:    06:00, 11:30, 12:00, 12:30, 13:00, 19:00, 19:30, 20:00, 20:30
    Total losses:       85.46 kWh
    Peak Tx loading:    73.5%
    Avg Tx loading:     27.8%

  --- Q-Learning (two-phase, warm-started from DP) ---
  Q-table initialised from DP value function
  Phase 1: Refining arbitrage (penalty=0.0, 50000 episodes)
  Episode 2500/50000  avg_reward=   32.20  avg_violations=  0.0  epsilon=0.274
  Episode 5000/50000  avg_reward=   30.14  avg_violations=  0.0  epsilon=0.251
  Episode 7500/50000  avg_reward=   34.67  avg_violations=  0.0  epsilon=0.229
  Episode 10000/50000  avg_reward=   35.73  avg_violations=  0.0  epsilon=0.210
  Episode 12500/50000  avg_reward=   36.85  avg_violations=  0.0  epsilon=0.192
  Episode 15000/50000  avg_reward=   38.50  avg_violations=  0.0  epsilon=0.175
  Episode 17500/50000  avg_reward=   40.16  avg_violations=  0.0  epsilon=0.160
  Episode 20000/50000  avg_reward=   41.42  avg_violations=  0.0  epsilon=0.147
  Episode 22500/50000  avg_reward=   41.93  avg_violations=  0.0  epsilon=0.134
  Episode 25000/50000  avg_reward=   42.78  avg_violations=  0.0  epsilon=0.122
  Episode 27500/50000  avg_reward=   42.33  avg_violations=  0.0  epsilon=0.112
  Episode 30000/50000  avg_reward=   42.42  avg_violations=  0.0  epsilon=0.102
  Episode 32500/50000  avg_reward=   44.36  avg_violations=  0.0  epsilon=0.094
  Episode 35000/50000  avg_reward=   44.59  avg_violations=  0.0  epsilon=0.086
  Episode 37500/50000  avg_reward=   43.90  avg_violations=  0.0  epsilon=0.078
  Episode 40000/50000  avg_reward=   46.29  avg_violations=  0.0  epsilon=0.072
  Episode 42500/50000  avg_reward=   45.51  avg_violations=  0.0  epsilon=0.065
  Episode 45000/50000  avg_reward=   46.57  avg_violations=  0.0  epsilon=0.060
  Episode 47500/50000  avg_reward=   47.61  avg_violations=  0.0  epsilon=0.055
  Episode 50000/50000  avg_reward=   46.48  avg_violations=  0.0  epsilon=0.050
  Phase 1 result: revenue=$46.48, violations=0.0

  Phase 2: Learning violation avoidance (penalty=5.0, 50000 episodes)
  Episode 2500/50000  avg_reward=   17.01  avg_violations=  4.2  epsilon=0.086
  Episode 5000/50000  avg_reward=   29.12  avg_violations=  2.5  epsilon=0.074
  Episode 7500/50000  avg_reward=   22.47  avg_violations=  3.5  epsilon=0.064
  Episode 10000/50000  avg_reward=   32.14  avg_violations=  1.7  epsilon=0.055
  Episode 12500/50000  avg_reward=   30.27  avg_violations=  2.2  epsilon=0.047
  Episode 15000/50000  avg_reward=   33.07  avg_violations=  1.7  epsilon=0.041
  Episode 17500/50000  avg_reward=   35.21  avg_violations=  1.2  epsilon=0.035
  Episode 20000/50000  avg_reward=   33.87  avg_violations=  1.4  epsilon=0.030
  Episode 22500/50000  avg_reward=   36.16  avg_violations=  1.1  epsilon=0.026
  Episode 25000/50000  avg_reward=   35.37  avg_violations=  1.3  epsilon=0.022
  Episode 27500/50000  avg_reward=   36.50  avg_violations=  1.2  epsilon=0.019
  Episode 30000/50000  avg_reward=   37.76  avg_violations=  1.0  epsilon=0.017
  Episode 32500/50000  avg_reward=   40.49  avg_violations=  0.6  epsilon=0.014
  Episode 35000/50000  avg_reward=   40.19  avg_violations=  0.7  epsilon=0.012
  Episode 37500/50000  avg_reward=   38.40  avg_violations=  0.9  epsilon=0.011
  Episode 40000/50000  avg_reward=   39.50  avg_violations=  0.7  epsilon=0.009
  Episode 42500/50000  avg_reward=   39.83  avg_violations=  0.8  epsilon=0.008
  Episode 45000/50000  avg_reward=   42.60  avg_violations=  0.3  epsilon=0.007
  Episode 47500/50000  avg_reward=   42.41  avg_violations=  0.3  epsilon=0.006
  Episode 50000/50000  avg_reward=   43.54  avg_violations=  0.2  epsilon=0.005
  Phase 2 result: revenue=$44.34, violations=0.2

  Phase 2 training summary:
  Episodes trained:        50000
  Avg reward (last 50):    43.54
  Avg revenue (last 50):   $44.34
  Avg violations (last 50): 0.2
  Zero-violation episodes:  84%

  Summary (RL ±100kW 300kWh):
    Voltage range:      0.9264 – 1.0999 pu
    Voltage violations: 3 of 48 periods
    Violation times:    19:30, 20:00, 20:30
    Total losses:       78.28 kWh
    Peak Tx loading:    67.0%
    Avg Tx loading:     25.9%

======================================================================
  ±100 kW dispatch, 400 kWh capacity
======================================================================

  --- DP Solver ---
  Revenue: $56.76

  Summary (DP ±100kW 400kWh):
    Voltage range:      0.9264 – 1.1100 pu
    Voltage violations: 10 of 48 periods
    Violation times:    06:00, 11:00, 11:30, 12:00, 12:30, 13:00, 13:30, 19:30, 20:00, 20:30
    Total losses:       95.65 kWh
    Peak Tx loading:    73.5%
    Avg Tx loading:     29.5%

  --- Q-Learning (two-phase, warm-started from DP) ---
  Q-table initialised from DP value function
  Phase 1: Refining arbitrage (penalty=0.0, 50000 episodes)
  Episode 2500/50000  avg_reward=   34.01  avg_violations=  0.0  epsilon=0.274
  Episode 5000/50000  avg_reward=   36.82  avg_violations=  0.0  epsilon=0.251
  Episode 7500/50000  avg_reward=   39.11  avg_violations=  0.0  epsilon=0.229
  Episode 10000/50000  avg_reward=   42.75  avg_violations=  0.0  epsilon=0.210
  Episode 12500/50000  avg_reward=   41.96  avg_violations=  0.0  epsilon=0.192
  Episode 15000/50000  avg_reward=   43.38  avg_violations=  0.0  epsilon=0.175
  Episode 17500/50000  avg_reward=   44.25  avg_violations=  0.0  epsilon=0.160
  Episode 20000/50000  avg_reward=   44.56  avg_violations=  0.0  epsilon=0.147
  Episode 22500/50000  avg_reward=   47.05  avg_violations=  0.0  epsilon=0.134
  Episode 25000/50000  avg_reward=   47.64  avg_violations=  0.0  epsilon=0.122
  Episode 27500/50000  avg_reward=   48.08  avg_violations=  0.0  epsilon=0.112
  Episode 30000/50000  avg_reward=   48.08  avg_violations=  0.0  epsilon=0.102
  Episode 32500/50000  avg_reward=   50.07  avg_violations=  0.0  epsilon=0.094
  Episode 35000/50000  avg_reward=   49.24  avg_violations=  0.0  epsilon=0.086
  Episode 37500/50000  avg_reward=   51.75  avg_violations=  0.0  epsilon=0.078
  Episode 40000/50000  avg_reward=   52.27  avg_violations=  0.0  epsilon=0.072
  Episode 42500/50000  avg_reward=   51.44  avg_violations=  0.0  epsilon=0.065
  Episode 45000/50000  avg_reward=   52.15  avg_violations=  0.0  epsilon=0.060
  Episode 47500/50000  avg_reward=   52.55  avg_violations=  0.0  epsilon=0.055
  Episode 50000/50000  avg_reward=   53.33  avg_violations=  0.0  epsilon=0.050
  Phase 1 result: revenue=$53.33, violations=0.0

  Phase 2: Learning violation avoidance (penalty=5.0, 50000 episodes)
  Episode 2500/50000  avg_reward=   23.52  avg_violations=  4.6  epsilon=0.086
  Episode 5000/50000  avg_reward=   31.54  avg_violations=  3.2  epsilon=0.074
  Episode 7500/50000  avg_reward=   34.48  avg_violations=  2.9  epsilon=0.064
  Episode 10000/50000  avg_reward=   36.06  avg_violations=  2.3  epsilon=0.055
  Episode 12500/50000  avg_reward=   36.94  avg_violations=  2.2  epsilon=0.047
  Episode 15000/50000  avg_reward=   39.36  avg_violations=  1.8  epsilon=0.041
  Episode 17500/50000  avg_reward=   38.12  avg_violations=  2.0  epsilon=0.035
  Episode 20000/50000  avg_reward=   39.91  avg_violations=  1.7  epsilon=0.030
  Episode 22500/50000  avg_reward=   41.26  avg_violations=  1.6  epsilon=0.026
  Episode 25000/50000  avg_reward=   43.71  avg_violations=  1.3  epsilon=0.022
  Episode 27500/50000  avg_reward=   43.49  avg_violations=  1.4  epsilon=0.019
  Episode 30000/50000  avg_reward=   45.43  avg_violations=  1.1  epsilon=0.017
  Episode 32500/50000  avg_reward=   47.19  avg_violations=  0.7  epsilon=0.014
  Episode 35000/50000  avg_reward=   48.54  avg_violations=  0.7  epsilon=0.012
  Episode 37500/50000  avg_reward=   46.81  avg_violations=  0.9  epsilon=0.011
  Episode 40000/50000  avg_reward=   45.78  avg_violations=  1.1  epsilon=0.009
  Episode 42500/50000  avg_reward=   47.33  avg_violations=  0.8  epsilon=0.008
  Episode 45000/50000  avg_reward=   48.65  avg_violations=  0.7  epsilon=0.007
  Episode 47500/50000  avg_reward=   48.24  avg_violations=  0.8  epsilon=0.006
  Episode 50000/50000  avg_reward=   48.09  avg_violations=  0.8  epsilon=0.005
  Phase 2 result: revenue=$51.89, violations=0.8

  Phase 2 training summary:
  Episodes trained:        50000
  Avg reward (last 50):    48.09
  Avg revenue (last 50):   $51.89
  Avg violations (last 50): 0.8
  Zero-violation episodes:  40%

  Summary (RL ±100kW 400kWh):
    Voltage range:      0.9264 – 1.0999 pu
    Voltage violations: 1 of 48 periods
    Violation times:    20:30
    Total losses:       83.81 kWh
    Peak Tx loading:    67.0%
    Avg Tx loading:     26.6%

  Summary (No Battery):
    Voltage range:      0.9268 – 1.0431 pu
    Voltage violations: 11 of 48 periods
    Violation times:    06:00, 06:30, 07:00, 17:00, 17:30, 18:00, 18:30, 19:00, 19:30, 20:00, 20:30
    Total losses:       57.17 kWh
    Peak Tx loading:    49.7%
    Avg Tx loading:     27.1%

==========================================================================================
  DP vs Q-LEARNING: HEAD-TO-HEAD COMPARISON
==========================================================================================
  Config            DP Rev  DP Viol  DP Loss   RL Rev  RL Viol  RL Loss
  --------------- -------- -------- -------- -------- -------- --------
  baseline             ---       11    57.2      ---       11    57.2
  ±50kW/200       $  28.38        4    62.2 $  24.98        0    55.1
  ±50kW/300       $  32.69        0    61.8 $  32.55        0    61.6
  ±50kW/400       $  35.92        0    61.0 $  35.90        0    60.9
  ±80kW/200       $  36.89        6    70.3 $  33.70        1    64.8
  ±80kW/300       $  44.02        4    75.3 $  41.48        1    69.5
  ±80kW/400       $  49.01        3    80.9 $  48.93        0    78.4
  ±100kW/200      $  41.18       10    79.1 $  34.72        2    69.0
  ±100kW/300      $  50.17        9    85.5 $  44.05        3    78.3
  ±100kW/400      $  56.76       10    95.6 $  51.27        1    83.8

==========================================================================================
  RL IMPROVEMENT OVER DP
==========================================================================================
  Config             Rev Gap   Viol Δ     Loss Δ Assessment
  --------------- ---------- -------- ---------- --------------------
  ±50kW/200       $    -3.40       -4      -7.1 ✅ RL fixes violations
  ±50kW/300       $    -0.14       +0      -0.2 🟰 Both optimal
  ±50kW/400       $    -0.02       +0      -0.2 🟰 Both optimal
  ±80kW/200       $    -3.19       -5      -5.5 📉 RL fewer violations
  ±80kW/300       $    -2.53       -3      -5.8 📉 RL fewer violations
  ±80kW/400       $    -0.08       -3      -2.5 ✅ RL fixes violations
  ±100kW/200      $    -6.46       -8     -10.1 📉 RL fewer violations
  ±100kW/300      $    -6.11       -6      -7.2 📉 RL fewer violations
  ±100kW/400      $    -5.49       -9     -11.8 📉 RL fewer violations

==========================================================================================
  KEY FINDINGS
==========================================================================================
  DP minimum feasible:  ±50kW / 300kWh ($32.69/day)
  RL minimum feasible:  ±50kW / 200kWh ($24.98/day)

  Q-learning reduces minimum battery size by 100 kWh (33% smaller)

==========================================================================================
  DISPATCH PROFILE: ±50kW / 200kWh
  DP: $28.38/day, 4 violations
  RL: $24.98/day, 0 violations
==========================================================================================
  t    Time     Price    DP kW  DP SoC    RL kW  RL SoC    Diff
  --   -----   ------  ------- -------  ------- -------  ------
  0    00:00  $  59.7        0   100.0      +25   100.0     +25
  1    00:30  $  76.2        0   100.0        0   111.9        
  2    01:00  $  74.9        0   100.0        0   111.9        
  3    01:30  $  78.9        0   100.0        0   111.9        
  4    02:00  $  80.6        0   100.0        0   111.9        
  5    02:30  $  79.8        0   100.0        0   111.9        
  6    03:00  $  62.4        0   100.0        0   111.9        
  7    03:30  $  64.2        0   100.0        0   111.9        
  8    04:00  $  62.3        0   100.0        0   111.9        
  9    04:30  $  64.3        0   100.0        0   111.9        
  10   05:00  $  75.3        0   100.0        0   111.9        
  11   05:30  $  59.6        0   100.0       +5   111.9      +5
  12   06:00  $ 101.0        0   100.0      -10   114.2     -10
  13   06:30  $ 147.7      -50   100.0      -50   109.0        
  14   07:00  $ 230.4      -50    73.7      -50    82.7        
  15   07:30  $ 228.0      -50    47.4      -50    56.4        
  16   08:00  $ 103.2        0    21.1      -10    30.0     -10
  17   08:30  $  40.0        0    21.1        0    24.8        
  18   09:00  $  52.2        0    21.1        0    24.8        
  19   09:30  $  60.4        0    21.1        0    24.8        
  20   10:00  $  50.6        0    21.1        0    24.8        
  21   10:30  $  44.3        0    21.1        0    24.8        
  22   11:00  $  25.3      +50    21.1      +50    24.8        
  23   11:30  $  15.8      +50    44.8      +50    48.5        
  24   12:00  $ -13.1      +50    68.6      +50    72.3        
  25   12:30  $ -14.4      +50    92.3      +50    96.0        
  26   13:00  $ -13.9      +50   116.1      +50   119.8        
  27   13:30  $  28.6      +50   139.8      +50   143.5        
  28   14:00  $  36.0      +25   163.6      +20   167.3      -5
  29   14:30  $  37.3      +50   175.4        0   176.8     -50
  30   15:00  $  51.7        0   199.2        0   176.8        
  31   15:30  $  72.9        0   199.2        0   176.8        
  32   16:00  $ 113.2      -40   199.2      -20   176.8     +20
  33   16:30  $ 162.5      -50   178.1      -50   166.2        
  34   17:00  $ 137.3      -50   151.8      -50   139.9        
  35   17:30  $ 173.8      -50   125.5      -50   113.6        
  36   18:00  $ 144.7      -50    99.2      -50    87.3        
  37   18:30  $ 135.0      -50    72.9      -50    61.0        
  38   19:00  $ 114.8      -50    46.5      +40    34.7     +90
  39   19:30  $ 105.3        0    20.2      -45    53.7     -45
  40   20:00  $ 107.1        0    20.2      +45    30.0     +45
  41   20:30  $ 105.0        0    20.2      -40    51.4     -40
  42   21:00  $ 105.8        0    20.2      -15    30.3     -15
  43   21:30  $  78.0        0    20.2        0    22.4        
  44   22:00  $  87.4        0    20.2        0    22.4        
  45   22:30  $  71.3        0    20.2        0    22.4        
  46   23:00  $  78.0        0    20.2        0    22.4        
  47   23:30  $  72.7        0    20.2        0    22.4        
  END                             20.2             22.4

  Revenue gap: $3.40/day

==========================================================================================
  DISPATCH PROFILE: ±80kW / 200kWh
  DP: $36.89/day, 6 violations
  RL: $33.70/day, 1 violations
==========================================================================================
  t    Time     Price    DP kW  DP SoC    RL kW  RL SoC    Diff
  --   -----   ------  ------- -------  ------- -------  ------
  0    00:00  $  59.7      +56   100.0       -8   100.0     -64
  1    00:30  $  76.2        0   126.6        0    95.8        
  2    01:00  $  74.9        0   126.6        0    95.8        
  3    01:30  $  78.9        0   126.6        0    95.8        
  4    02:00  $  80.6        0   126.6        0    95.8        
  5    02:30  $  79.8        0   126.6        0    95.8        
  6    03:00  $  62.4        0   126.6       +8    95.8      +8
  7    03:30  $  64.2        0   126.6        0    99.6        
  8    04:00  $  62.3        0   126.6      +32    99.6     +32
  9    04:30  $  64.3        0   126.6        0   114.8        
  10   05:00  $  75.3        0   126.6        0   114.8        
  11   05:30  $  59.6      +48   126.6      +80   114.8     +32
  12   06:00  $ 101.0        0   149.4       +8   152.8      +8
  13   06:30  $ 147.7      -80   149.4      -80   156.6        
  14   07:00  $ 230.4      -80   107.3      -80   114.5        
  15   07:30  $ 228.0      -80    65.2      -80    72.4        
  16   08:00  $ 103.2        0    23.1      -16    30.3     -16
  17   08:30  $  40.0        0    23.1        0    21.9        
  18   09:00  $  52.2        0    23.1        0    21.9        
  19   09:30  $  60.4        0    23.1        0    21.9        
  20   10:00  $  50.6        0    23.1        0    21.9        
  21   10:30  $  44.3        0    23.1        0    21.9        
  22   11:00  $  25.3      +48    23.1      +48    21.9        
  23   11:30  $  15.8      +80    45.9      +80    44.7        
  24   12:00  $ -13.1      +80    83.9      +80    82.7        
  25   12:30  $ -14.4      +80   121.9      +80   120.7        
  26   13:00  $ -13.9      +80   159.9      +80   158.7        
  27   13:30  $  28.6        0   197.9        0   196.7        
  28   14:00  $  36.0        0   197.9        0   196.7        
  29   14:30  $  37.3        0   197.9        0   196.7        
  30   15:00  $  51.7        0   197.9        0   196.7        
  31   15:30  $  72.9        0   197.9        0   196.7        
  32   16:00  $ 113.2        0   197.9        0   196.7        
  33   16:30  $ 162.5      -80   197.9      -80   196.7        
  34   17:00  $ 137.3      -80   155.8      -56   154.5     +24
  35   17:30  $ 173.8      -80   113.7      -80   125.1        
  36   18:00  $ 144.7      -80    71.6      -64    83.0     +16
  37   18:30  $ 135.0      -16    29.5      -40    49.3     -24
  38   19:00  $ 114.8        0    21.0      +40    28.2     +40
  39   19:30  $ 105.3        0    21.0      -40    47.2     -40
  40   20:00  $ 107.1        0    21.0      +40    26.2     +40
  41   20:30  $ 105.0        0    21.0        0    45.2        
  42   21:00  $ 105.8        0    21.0      -40    45.2     -40
  43   21:30  $  78.0        0    21.0        0    24.1        
  44   22:00  $  87.4        0    21.0        0    24.1        
  45   22:30  $  71.3        0    21.0        0    24.1        
  46   23:00  $  78.0        0    21.0        0    24.1        
  47   23:30  $  72.7        0    21.0        0    24.1        
  END                             21.0             24.1

  Revenue gap: $3.19/day

==========================================================================================
  DISPATCH PROFILE: ±80kW / 300kWh
  DP: $44.02/day, 4 violations
  RL: $41.48/day, 1 violations
==========================================================================================
  t    Time     Price    DP kW  DP SoC    RL kW  RL SoC    Diff
  --   -----   ------  ------- -------  ------- -------  ------
  0    00:00  $  59.7      +16   150.0      +16   150.0        
  1    00:30  $  76.2        0   157.6        0   157.6        
  2    01:00  $  74.9        0   157.6        0   157.6        
  3    01:30  $  78.9        0   157.6        0   157.6        
  4    02:00  $  80.6        0   157.6        0   157.6        
  5    02:30  $  79.8        0   157.6        0   157.6        
  6    03:00  $  62.4        0   157.6        0   157.6        
  7    03:30  $  64.2        0   157.6        0   157.6        
  8    04:00  $  62.3        0   157.6        0   157.6        
  9    04:30  $  64.3        0   157.6        0   157.6        
  10   05:00  $  75.3        0   157.6        0   157.6        
  11   05:30  $  59.6       +8   157.6      +16   157.6      +8
  12   06:00  $ 101.0        0   161.4       -8   165.2      -8
  13   06:30  $ 147.7      -80   161.4      -80   161.0        
  14   07:00  $ 230.4      -80   119.3      -80   118.9        
  15   07:30  $ 228.0      -80    77.2      -80    76.8        
  16   08:00  $ 103.2       -8    35.1       -8    34.7        
  17   08:30  $  40.0        0    30.9      +40    30.5     +40
  18   09:00  $  52.2        0    30.9        0    49.5        
  19   09:30  $  60.4        0    30.9        0    49.5        
  20   10:00  $  50.6        0    30.9        0    49.5        
  21   10:30  $  44.3        0    30.9        0    49.5        
  22   11:00  $  25.3      +80    30.9      +80    49.5        
  23   11:30  $  15.8      +80    68.9      +80    87.5        
  24   12:00  $ -13.1      +80   106.9      +80   125.5        
  25   12:30  $ -14.4      +80   144.9      +80   163.5        
  26   13:00  $ -13.9      +80   182.9      +80   201.5        
  27   13:30  $  28.6      +80   220.9      +80   239.5        
  28   14:00  $  36.0      +32   258.9        0   277.5     -32
  29   14:30  $  37.3      +48   274.1        0   277.5     -48
  30   15:00  $  51.7        0   296.9        0   277.5        
  31   15:30  $  72.9        0   296.9        0   277.5        
  32   16:00  $ 113.2      -40   296.9       -8   277.5     +32
  33   16:30  $ 162.5      -80   275.8      -80   273.3        
  34   17:00  $ 137.3      -80   233.7      -80   231.1        
  35   17:30  $ 173.8      -80   191.6      -80   189.0        
  36   18:00  $ 144.7      -80   149.5      -72   146.9      +8
  37   18:30  $ 135.0      -80   107.4      -72   109.0      +8
  38   19:00  $ 114.8      -56    65.3      -40    71.1     +16
  39   19:30  $ 105.3        0    35.8      +56    50.1     +56
  40   20:00  $ 107.1       -8    35.8      -40    76.7     -32
  41   20:30  $ 105.0        0    31.6        0    55.6        
  42   21:00  $ 105.8        0    31.6      -40    55.6     -40
  43   21:30  $  78.0        0    31.6        0    34.6        
  44   22:00  $  87.4        0    31.6        0    34.6        
  45   22:30  $  71.3        0    31.6        0    34.6        
  46   23:00  $  78.0        0    31.6        0    34.6        
  47   23:30  $  72.7        0    31.6        0    34.6        
  END                             31.6             34.6

  Revenue gap: $2.53/day

==========================================================================================
  DISPATCH PROFILE: ±80kW / 400kWh
  DP: $49.01/day, 3 violations
  RL: $48.93/day, 0 violations
==========================================================================================
  t    Time     Price    DP kW  DP SoC    RL kW  RL SoC    Diff
  --   -----   ------  ------- -------  ------- -------  ------
  0    00:00  $  59.7        0   200.0        0   200.0        
  1    00:30  $  76.2        0   200.0        0   200.0        
  2    01:00  $  74.9        0   200.0        0   200.0        
  3    01:30  $  78.9        0   200.0        0   200.0        
  4    02:00  $  80.6        0   200.0        0   200.0        
  5    02:30  $  79.8        0   200.0        0   200.0        
  6    03:00  $  62.4        0   200.0        0   200.0        
  7    03:30  $  64.2        0   200.0        0   200.0        
  8    04:00  $  62.3        0   200.0        0   200.0        
  9    04:30  $  64.3        0   200.0        0   200.0        
  10   05:00  $  75.3        0   200.0        0   200.0        
  11   05:30  $  59.6        0   200.0        0   200.0        
  12   06:00  $ 101.0        0   200.0       -8   200.0      -8
  13   06:30  $ 147.7      -80   200.0      -80   195.8        
  14   07:00  $ 230.4      -80   157.9      -80   153.7        
  15   07:30  $ 228.0      -80   115.8      -80   111.6        
  16   08:00  $ 103.2      -56    73.7      -48    69.5      +8
  17   08:30  $  40.0      +80    44.2      +80    44.2        
  18   09:00  $  52.2        0    82.2        0    82.2        
  19   09:30  $  60.4        0    82.2        0    82.2        
  20   10:00  $  50.6        0    82.2        0    82.2        
  21   10:30  $  44.3      +32    82.2      +24    82.2      -8
  22   11:00  $  25.3      +80    97.4      +80    93.6        
  23   11:30  $  15.8      +80   135.4      +80   131.6        
  24   12:00  $ -13.1      +80   173.4      +80   169.6        
  25   12:30  $ -14.4      +80   211.4      +80   207.6        
  26   13:00  $ -13.9      +80   249.4      +80   245.6        
  27   13:30  $  28.6      +80   287.4      +80   283.6        
  28   14:00  $  36.0      +80   325.4      +80   321.6        
  29   14:30  $  37.3      +72   363.4      +80   359.6      +8
  30   15:00  $  51.7        0   397.6        0   397.6        
  31   15:30  $  72.9        0   397.6        0   397.6        
  32   16:00  $ 113.2      -80   397.6      -64   397.6     +16
  33   16:30  $ 162.5      -80   355.5      -80   363.9        
  34   17:00  $ 137.3      -80   313.4      -80   321.8        
  35   17:30  $ 173.8      -80   271.3      -80   279.7        
  36   18:00  $ 144.7      -80   229.2      -80   237.6        
  37   18:30  $ 135.0      -80   187.1      -80   195.5        
  38   19:00  $ 114.8      -80   145.0      -80   153.4        
  39   19:30  $ 105.3      -32   102.9      -40   111.3      -8
  40   20:00  $ 107.1      -80    86.0      -48    90.2     +32
  41   20:30  $ 105.0        0    43.9      -40    65.0     -40
  42   21:00  $ 105.8        0    43.9        0    43.9        
  43   21:30  $  78.0        0    43.9        0    43.9        
  44   22:00  $  87.4        0    43.9        0    43.9        
  45   22:30  $  71.3        0    43.9        0    43.9        
  46   23:00  $  78.0        0    43.9        0    43.9        
  47   23:30  $  72.7        0    43.9        0    43.9        
  END                             43.9             43.9

  Revenue gap: $0.08/day

==========================================================================================
  DISPATCH PROFILE: ±100kW / 200kWh
  DP: $41.18/day, 10 violations
  RL: $34.72/day, 2 violations
==========================================================================================
  t    Time     Price    DP kW  DP SoC    RL kW  RL SoC    Diff
  --   -----   ------  ------- -------  ------- -------  ------
  0    00:00  $  59.7      +90   100.0      +90   100.0        
  1    00:30  $  76.2        0   142.8        0   142.8        
  2    01:00  $  74.9        0   142.8      -30   142.8     -30
  3    01:30  $  78.9        0   142.8        0   127.0        
  4    02:00  $  80.6        0   142.8        0   127.0        
  5    02:30  $  79.8        0   142.8        0   127.0        
  6    03:00  $  62.4        0   142.8      +10   127.0     +10
  7    03:30  $  64.2        0   142.8      +80   131.7     +80
  8    04:00  $  62.3        0   142.8        0   169.7        
  9    04:30  $  64.3        0   142.8        0   169.7        
  10   05:00  $  75.3        0   142.8        0   169.7        
  11   05:30  $  59.6      +90   142.8      +40   169.7     -50
  12   06:00  $ 101.0        0   185.5      -10   188.7     -10
  13   06:30  $ 147.7     -100   185.5     -100   183.4        
  14   07:00  $ 230.4     -100   132.9     -100   130.8        
  15   07:30  $ 228.0     -100    80.2     -100    78.2        
  16   08:00  $ 103.2      -10    27.6        0    25.6     +10
  17   08:30  $  40.0        0    22.3      -10    25.6     -10
  18   09:00  $  52.2        0    22.3        0    20.3        
  19   09:30  $  60.4        0    22.3        0    20.3        
  20   10:00  $  50.6        0    22.3        0    20.3        
  21   10:30  $  44.3        0    22.3        0    20.3        
  22   11:00  $  25.3        0    22.3      +10    20.3     +10
  23   11:30  $  15.8      +70    22.3      +80    25.0     +10
  24   12:00  $ -13.1     +100    55.6      +80    63.0     -20
  25   12:30  $ -14.4     +100   103.1      +70   101.0     -30
  26   13:00  $ -13.9     +100   150.6      +90   134.3     -10
  27   13:30  $  28.6        0   198.1        0   177.0        
  28   14:00  $  36.0        0   198.1        0   177.0        
  29   14:30  $  37.3        0   198.1        0   177.0        
  30   15:00  $  51.7        0   198.1        0   177.0        
  31   15:30  $  72.9        0   198.1        0   177.0        
  32   16:00  $ 113.2        0   198.1        0   177.0        
  33   16:30  $ 162.5     -100   198.1      -90   177.0     +10
  34   17:00  $ 137.3      -30   145.5      +60   129.7     +90
  35   17:30  $ 173.8     -100   129.7     -100   158.2        
  36   18:00  $ 144.7     -100    77.0      -90   105.5     +10
  37   18:30  $ 135.0        0    24.4      -60    58.2     -60
  38   19:00  $ 114.8        0    24.4      +40    26.6     +40
  39   19:30  $ 105.3        0    24.4        0    45.6        
  40   20:00  $ 107.1        0    24.4        0    45.6        
  41   20:30  $ 105.0        0    24.4      -40    45.6     -40
  42   21:00  $ 105.8        0    24.4        0    24.5        
  43   21:30  $  78.0        0    24.4        0    24.5        
  44   22:00  $  87.4        0    24.4        0    24.5        
  45   22:30  $  71.3        0    24.4        0    24.5        
  46   23:00  $  78.0        0    24.4        0    24.5        
  47   23:30  $  72.7        0    24.4        0    24.5        
  END                             24.4             24.5

  Revenue gap: $6.46/day

==========================================================================================
  DISPATCH PROFILE: ±100kW / 300kWh
  DP: $50.17/day, 9 violations
  RL: $44.05/day, 3 violations
==========================================================================================
  t    Time     Price    DP kW  DP SoC    RL kW  RL SoC    Diff
  --   -----   ------  ------- -------  ------- -------  ------
  0    00:00  $  59.7      +30   150.0      +40   150.0     +10
  1    00:30  $  76.2        0   164.2        0   169.0        
  2    01:00  $  74.9        0   164.2      -90   169.0     -90
  3    01:30  $  78.9        0   164.2        0   121.6        
  4    02:00  $  80.6        0   164.2        0   121.6        
  5    02:30  $  79.8        0   164.2        0   121.6        
  6    03:00  $  62.4        0   164.2      +10   121.6     +10
  7    03:30  $  64.2        0   164.2        0   126.4        
  8    04:00  $  62.3        0   164.2      +30   126.4     +30
  9    04:30  $  64.3        0   164.2      +10   140.6     +10
  10   05:00  $  75.3        0   164.2      +10   145.4     +10
  11   05:30  $  59.6      +60   164.2     +100   150.1     +40
  12   06:00  $ 101.0        0   192.8      -10   197.6     -10
  13   06:30  $ 147.7     -100   192.8     -100   192.4        
  14   07:00  $ 230.4     -100   140.1     -100   139.7        
  15   07:30  $ 228.0     -100    87.5     -100    87.1        
  16   08:00  $ 103.2        0    34.9        0    34.5        
  17   08:30  $  40.0        0    34.9     +100    34.5    +100
  18   09:00  $  52.2        0    34.9      +10    82.0     +10
  19   09:30  $  60.4        0    34.9        0    86.7        
  20   10:00  $  50.6        0    34.9        0    86.7        
  21   10:30  $  44.3        0    34.9        0    86.7        
  22   11:00  $  25.3      +90    34.9      +50    86.7     -40
  23   11:30  $  15.8     +100    77.6      +80   110.5     -20
  24   12:00  $ -13.1     +100   125.1      +50   148.5     -50
  25   12:30  $ -14.4     +100   172.6      +70   172.2     -30
  26   13:00  $ -13.9     +100   220.1      +90   205.5     -10
  27   13:30  $  28.6      +60   267.6      +90   248.2     +30
  28   14:00  $  36.0        0   296.1        0   291.0        
  29   14:30  $  37.3        0   296.1        0   291.0        
  30   15:00  $  51.7        0   296.1        0   291.0        
  31   15:30  $  72.9        0   296.1      +10   291.0     +10
  32   16:00  $ 113.2        0   296.1      -10   295.7     -10
  33   16:30  $ 162.5     -100   296.1     -100   290.5        
  34   17:00  $ 137.3     -100   243.5     -100   237.8        
  35   17:30  $ 173.8     -100   190.8     -100   185.2        
  36   18:00  $ 144.7     -100   138.2      -90   132.6     +10
  37   18:30  $ 135.0     -100    85.6      -90    85.2     +10
  38   19:00  $ 114.8        0    32.9      +40    37.8     +40
  39   19:30  $ 105.3        0    32.9        0    56.8        
  40   20:00  $ 107.1        0    32.9        0    56.8        
  41   20:30  $ 105.0        0    32.9        0    56.8        
  42   21:00  $ 105.8        0    32.9      -40    56.8     -40
  43   21:30  $  78.0        0    32.9        0    35.8        
  44   22:00  $  87.4        0    32.9        0    35.8        
  45   22:30  $  71.3        0    32.9        0    35.8        
  46   23:00  $  78.0        0    32.9        0    35.8        
  47   23:30  $  72.7        0    32.9      -10    35.8     -10
  END                             32.9             30.5

  Revenue gap: $6.11/day

==========================================================================================
  DISPATCH PROFILE: ±100kW / 400kWh
  DP: $56.76/day, 10 violations
  RL: $51.27/day, 1 violations
==========================================================================================
  t    Time     Price    DP kW  DP SoC    RL kW  RL SoC    Diff
  --   -----   ------  ------- -------  ------- -------  ------
  0    00:00  $  59.7        0   200.0        0   200.0        
  1    00:30  $  76.2        0   200.0        0   200.0        
  2    01:00  $  74.9        0   200.0        0   200.0        
  3    01:30  $  78.9        0   200.0      -50   200.0     -50
  4    02:00  $  80.6        0   200.0        0   173.7        
  5    02:30  $  79.8        0   200.0      +10   173.7     +10
  6    03:00  $  62.4        0   200.0      +10   178.4     +10
  7    03:30  $  64.2        0   200.0        0   183.2        
  8    04:00  $  62.3        0   200.0      +10   183.2     +10
  9    04:30  $  64.3        0   200.0        0   187.9        
  10   05:00  $  75.3        0   200.0        0   187.9        
  11   05:30  $  59.6        0   200.0      +40   187.9     +40
  12   06:00  $ 101.0        0   200.0      -10   206.9     -10
  13   06:30  $ 147.7     -100   200.0     -100   201.7        
  14   07:00  $ 230.4     -100   147.4     -100   149.0        
  15   07:30  $ 228.0     -100    94.7     -100    96.4        
  16   08:00  $ 103.2        0    42.1        0    43.8        
  17   08:30  $  40.0        0    42.1      +70    43.8     +70
  18   09:00  $  52.2        0    42.1        0    77.0        
  19   09:30  $  60.4        0    42.1        0    77.0        
  20   10:00  $  50.6        0    42.1        0    77.0        
  21   10:30  $  44.3        0    42.1        0    77.0        
  22   11:00  $  25.3     +100    42.1      +90    77.0     -10
  23   11:30  $  15.8     +100    89.6      +50   119.8     -50
  24   12:00  $ -13.1     +100   137.1      +80   143.5     -20
  25   12:30  $ -14.4     +100   184.6      +60   181.5     -40
  26   13:00  $ -13.9     +100   232.1      +90   210.0     -10
  27   13:30  $  28.6     +100   279.6      +90   252.8     -10
  28   14:00  $  36.0      +50   327.1     +100   295.5     +50
  29   14:30  $  37.3     +100   350.9     +100   343.0        
  30   15:00  $  51.7        0   398.4        0   390.5        
  31   15:30  $  72.9        0   398.4        0   390.5        
  32   16:00  $ 113.2      -80   398.4      -60   390.5     +20
  33   16:30  $ 162.5     -100   356.2     -100   358.9        
  34   17:00  $ 137.3     -100   303.6     -100   306.3        
  35   17:30  $ 173.8     -100   251.0     -100   253.7        
  36   18:00  $ 144.7     -100   198.4      -90   201.1     +10
  37   18:30  $ 135.0     -100   145.7     -100   153.7        
  38   19:00  $ 114.8     -100    93.1      -60   101.1     +40
  39   19:30  $ 105.3        0    40.5      +40    69.5     +40
  40   20:00  $ 107.1        0    40.5      -40    88.5     -40
  41   20:30  $ 105.0        0    40.5        0    67.4        
  42   21:00  $ 105.8        0    40.5        0    67.4        
  43   21:30  $  78.0        0    40.5        0    67.4        
  44   22:00  $  87.4        0    40.5      -50    67.4     -50
  45   22:30  $  71.3        0    40.5        0    41.1        
  46   23:00  $  78.0        0    40.5        0    41.1        
  47   23:30  $  72.7        0    40.5        0    41.1        
  END                             40.5             41.1

  Revenue gap: $5.49/day


======================================================================
  ±80 kW dispatch, 200 kWh capacity
======================================================================

  --- DP Solver ---
  Revenue: $37.08

  Summary (DP ±80kW 200kWh):
    Voltage range:      0.9281 – 1.0965 pu
    Voltage violations: 6 of 48 periods
    Violation times:    06:00, 18:30, 19:00, 19:30, 20:00, 20:30
    Total losses:       70.60 kWh
    Peak Tx loading:    64.8%
    Avg Tx loading:     26.4%

  --- Q-Learning (two-phase, warm-started from DP) ---
  Q-table initialised from DP value function
  Phase 1: Refining arbitrage (penalty=0.0, 50000 episodes)
  Episode 2500/50000  avg_reward=   21.89  avg_violations=  0.0  epsilon=0.274
  Episode 5000/50000  avg_reward=   23.81  avg_violations=  0.0  epsilon=0.251
  Episode 7500/50000  avg_reward=   24.83  avg_violations=  0.0  epsilon=0.229
  Episode 10000/50000  avg_reward=   26.74  avg_violations=  0.0  epsilon=0.210
  Episode 12500/50000  avg_reward=   29.01  avg_violations=  0.0  epsilon=0.192
  Episode 15000/50000  avg_reward=   27.19  avg_violations=  0.0  epsilon=0.175
  Episode 17500/50000  avg_reward=   28.17  avg_violations=  0.0  epsilon=0.160
  Episode 20000/50000  avg_reward=   28.94  avg_violations=  0.0  epsilon=0.147
  Episode 22500/50000  avg_reward=   31.12  avg_violations=  0.0  epsilon=0.134
  Episode 25000/50000  avg_reward=   30.75  avg_violations=  0.0  epsilon=0.122
  Episode 27500/50000  avg_reward=   31.98  avg_violations=  0.0  epsilon=0.112
  Episode 30000/50000  avg_reward=   32.50  avg_violations=  0.0  epsilon=0.102
  Episode 32500/50000  avg_reward=   31.74  avg_violations=  0.0  epsilon=0.094
  Episode 35000/50000  avg_reward=   32.67  avg_violations=  0.0  epsilon=0.086
  Episode 37500/50000  avg_reward=   32.79  avg_violations=  0.0  epsilon=0.078
  Episode 40000/50000  avg_reward=   33.33  avg_violations=  0.0  epsilon=0.072
  Episode 42500/50000  avg_reward=   33.76  avg_violations=  0.0  epsilon=0.065
  Episode 45000/50000  avg_reward=   34.14  avg_violations=  0.0  epsilon=0.060
  Episode 47500/50000  avg_reward=   34.51  avg_violations=  0.0  epsilon=0.055
  Episode 50000/50000  avg_reward=   34.73  avg_violations=  0.0  epsilon=0.050
  Phase 1 result: revenue=$34.73, violations=0.0
  Q-table saved: data/q_tables/Q_phase1_80kW_200kWh.npz (shape (80, 48, 33))

  Phase 2: Learning violation avoidance (penalty=5.0, 80000 episodes)
  Episode 2500/80000  avg_reward=   12.40  avg_violations=  3.3  epsilon=0.087
  Episode 5000/80000  avg_reward=   18.07  avg_violations=  2.4  epsilon=0.075
  Episode 7500/80000  avg_reward=   17.99  avg_violations=  2.4  epsilon=0.065
  Episode 10000/80000  avg_reward=   26.54  avg_violations=  0.9  epsilon=0.056
  Episode 12500/80000  avg_reward=   23.36  avg_violations=  1.7  epsilon=0.049
  Episode 15000/80000  avg_reward=   23.13  avg_violations=  1.7  epsilon=0.042
  Episode 17500/80000  avg_reward=   28.61  avg_violations=  0.7  epsilon=0.037
  Episode 20000/80000  avg_reward=   28.79  avg_violations=  0.7  epsilon=0.032
  Episode 22500/80000  avg_reward=   27.84  avg_violations=  0.9  epsilon=0.027
  Episode 25000/80000  avg_reward=   28.21  avg_violations=  0.8  epsilon=0.024
  Episode 27500/80000  avg_reward=   29.94  avg_violations=  0.5  epsilon=0.021
  Episode 30000/80000  avg_reward=   31.99  avg_violations=  0.1  epsilon=0.018
  Episode 32500/80000  avg_reward=   29.75  avg_violations=  0.7  epsilon=0.015
  Episode 35000/80000  avg_reward=   31.42  avg_violations=  0.3  epsilon=0.013
  Episode 37500/80000  avg_reward=   32.00  avg_violations=  0.4  epsilon=0.012
  Episode 40000/80000  avg_reward=   33.60  avg_violations=  0.0  epsilon=0.010
  Episode 42500/80000  avg_reward=   32.60  avg_violations=  0.2  epsilon=0.009
  Episode 45000/80000  avg_reward=   33.81  avg_violations=  0.0  epsilon=0.007
  Episode 47500/80000  avg_reward=   32.45  avg_violations=  0.3  epsilon=0.006
  Episode 50000/80000  avg_reward=   33.47  avg_violations=  0.1  epsilon=0.006
  Episode 52500/80000  avg_reward=   32.92  avg_violations=  0.2  epsilon=0.005
  Episode 55000/80000  avg_reward=   33.96  avg_violations=  0.0  epsilon=0.004
  Episode 57500/80000  avg_reward=   33.69  avg_violations=  0.1  epsilon=0.004
  Episode 60000/80000  avg_reward=   34.38  avg_violations=  0.0  epsilon=0.003
  Episode 62500/80000  avg_reward=   34.37  avg_violations=  0.0  epsilon=0.003
  Episode 65000/80000  avg_reward=   34.41  avg_violations=  0.0  epsilon=0.002
  Episode 67500/80000  avg_reward=   34.23  avg_violations=  0.0  epsilon=0.002
  Episode 70000/80000  avg_reward=   34.11  avg_violations=  0.0  epsilon=0.002
  Episode 72500/80000  avg_reward=   33.68  avg_violations=  0.1  epsilon=0.002
  Episode 75000/80000  avg_reward=   34.03  avg_violations=  0.0  epsilon=0.001
  Episode 77500/80000  avg_reward=   34.44  avg_violations=  0.0  epsilon=0.001
  Episode 80000/80000  avg_reward=   34.31  avg_violations=  0.0  epsilon=0.001
  Phase 2 result: revenue=$34.31, violations=0.0
  Q-table saved: data/q_tables/Q_phase2_80kW_200kWh.npz (shape (80, 48, 33))

  Phase 2 training summary:
  Episodes trained:        80000
  Avg reward (last 50):    34.31
  Avg revenue (last 50):   $34.31
  Avg violations (last 50): 0.0
  Zero-violation episodes:  100%

  Summary (RL ±80kW 200kWh):
    Voltage range:      0.9413 – 1.0960 pu
    Voltage violations: 0 of 48 periods
    Total losses:       64.07 kWh
    Peak Tx loading:    65.0%
    Avg Tx loading:     24.5%

======================================================================
  ±80 kW dispatch, 300 kWh capacity
======================================================================

  --- DP Solver ---
  Revenue: $44.26

  Summary (DP ±80kW 300kWh):
    Voltage range:      0.9264 – 1.0960 pu
    Voltage violations: 4 of 48 periods
    Violation times:    06:00, 19:30, 20:00, 20:30
    Total losses:       76.67 kWh
    Peak Tx loading:    65.0%
    Avg Tx loading:     26.8%

  --- Q-Learning (two-phase, warm-started from DP) ---
  Q-table initialised from DP value function
  Phase 1: Refining arbitrage (penalty=0.0, 50000 episodes)
  Episode 2500/50000  avg_reward=   27.35  avg_violations=  0.0  epsilon=0.274
  Episode 5000/50000  avg_reward=   29.72  avg_violations=  0.0  epsilon=0.251
  Episode 7500/50000  avg_reward=   30.33  avg_violations=  0.0  epsilon=0.229
  Episode 10000/50000  avg_reward=   31.54  avg_violations=  0.0  epsilon=0.210
  Episode 12500/50000  avg_reward=   31.88  avg_violations=  0.0  epsilon=0.192
  Episode 15000/50000  avg_reward=   34.75  avg_violations=  0.0  epsilon=0.175
  Episode 17500/50000  avg_reward=   36.01  avg_violations=  0.0  epsilon=0.160
  Episode 20000/50000  avg_reward=   35.29  avg_violations=  0.0  epsilon=0.147
  Episode 22500/50000  avg_reward=   36.68  avg_violations=  0.0  epsilon=0.134
  Episode 25000/50000  avg_reward=   37.77  avg_violations=  0.0  epsilon=0.122
  Episode 27500/50000  avg_reward=   38.66  avg_violations=  0.0  epsilon=0.112
  Episode 30000/50000  avg_reward=   38.53  avg_violations=  0.0  epsilon=0.102
  Episode 32500/50000  avg_reward=   38.48  avg_violations=  0.0  epsilon=0.094
  Episode 35000/50000  avg_reward=   38.88  avg_violations=  0.0  epsilon=0.086
  Episode 37500/50000  avg_reward=   39.75  avg_violations=  0.0  epsilon=0.078
  Episode 40000/50000  avg_reward=   40.46  avg_violations=  0.0  epsilon=0.072
  Episode 42500/50000  avg_reward=   40.74  avg_violations=  0.0  epsilon=0.065
  Episode 45000/50000  avg_reward=   39.08  avg_violations=  0.0  epsilon=0.060
  Episode 47500/50000  avg_reward=   40.83  avg_violations=  0.0  epsilon=0.055
  Episode 50000/50000  avg_reward=   41.99  avg_violations=  0.0  epsilon=0.050
  Phase 1 result: revenue=$41.99, violations=0.0
  Q-table saved: data/q_tables/Q_phase1_80kW_300kWh.npz (shape (80, 48, 33))

  Phase 2: Learning violation avoidance (penalty=5.0, 80000 episodes)
  Episode 2500/80000  avg_reward=   26.30  avg_violations=  2.3  epsilon=0.087
  Episode 5000/80000  avg_reward=   30.91  avg_violations=  1.1  epsilon=0.075
  Episode 7500/80000  avg_reward=   29.73  avg_violations=  1.8  epsilon=0.065
  Episode 10000/80000  avg_reward=   34.06  avg_violations=  1.0  epsilon=0.056
  Episode 12500/80000  avg_reward=   32.57  avg_violations=  1.4  epsilon=0.049
  Episode 15000/80000  avg_reward=   38.89  avg_violations=  0.3  epsilon=0.042
  Episode 17500/80000  avg_reward=   37.84  avg_violations=  0.4  epsilon=0.037
  Episode 20000/80000  avg_reward=   34.57  avg_violations=  1.0  epsilon=0.032
  Episode 22500/80000  avg_reward=   37.68  avg_violations=  0.6  epsilon=0.027
  Episode 25000/80000  avg_reward=   39.35  avg_violations=  0.3  epsilon=0.024
  Episode 27500/80000  avg_reward=   39.33  avg_violations=  0.3  epsilon=0.021
  Episode 30000/80000  avg_reward=   39.34  avg_violations=  0.4  epsilon=0.018
  Episode 32500/80000  avg_reward=   41.70  avg_violations=  0.0  epsilon=0.015
  Episode 35000/80000  avg_reward=   40.36  avg_violations=  0.3  epsilon=0.013
  Episode 37500/80000  avg_reward=   37.61  avg_violations=  0.8  epsilon=0.012
  Episode 40000/80000  avg_reward=   41.99  avg_violations=  0.0  epsilon=0.010
  Episode 42500/80000  avg_reward=   41.60  avg_violations=  0.1  epsilon=0.009
  Episode 45000/80000  avg_reward=   40.68  avg_violations=  0.3  epsilon=0.007
  Episode 47500/80000  avg_reward=   41.94  avg_violations=  0.0  epsilon=0.006
  Episode 50000/80000  avg_reward=   42.30  avg_violations=  0.0  epsilon=0.006
  Episode 52500/80000  avg_reward=   42.40  avg_violations=  0.0  epsilon=0.005
  Episode 55000/80000  avg_reward=   41.78  avg_violations=  0.1  epsilon=0.004
  Episode 57500/80000  avg_reward=   42.13  avg_violations=  0.0  epsilon=0.004
  Episode 60000/80000  avg_reward=   42.38  avg_violations=  0.0  epsilon=0.003
  Episode 62500/80000  avg_reward=   42.19  avg_violations=  0.0  epsilon=0.003
  Episode 65000/80000  avg_reward=   42.43  avg_violations=  0.0  epsilon=0.002
  Episode 67500/80000  avg_reward=   42.47  avg_violations=  0.0  epsilon=0.002
  Episode 70000/80000  avg_reward=   42.50  avg_violations=  0.0  epsilon=0.002
  Episode 72500/80000  avg_reward=   42.36  avg_violations=  0.0  epsilon=0.002
  Episode 75000/80000  avg_reward=   42.36  avg_violations=  0.0  epsilon=0.001
  Episode 77500/80000  avg_reward=   42.38  avg_violations=  0.0  epsilon=0.001
  Episode 80000/80000  avg_reward=   42.46  avg_violations=  0.0  epsilon=0.001
  Phase 2 result: revenue=$42.46, violations=0.0
  Q-table saved: data/q_tables/Q_phase2_80kW_300kWh.npz (shape (80, 48, 33))

  Phase 2 training summary:
  Episodes trained:        80000
  Avg reward (last 50):    42.46
  Avg revenue (last 50):   $42.46
  Avg violations (last 50): 0.0
  Zero-violation episodes:  100%

  Summary (RL ±80kW 300kWh):
    Voltage range:      0.9413 – 1.0960 pu
    Voltage violations: 0 of 48 periods
    Total losses:       72.11 kWh
    Peak Tx loading:    65.0%
    Avg Tx loading:     25.3%

======================================================================
  ±80 kW dispatch, 400 kWh capacity
======================================================================

  --- DP Solver ---
  Revenue: $49.36

  Summary (DP ±80kW 400kWh):
    Voltage range:      0.9286 – 1.0960 pu
    Voltage violations: 3 of 48 periods
    Violation times:    06:00, 19:30, 20:30
    Total losses:       81.44 kWh
    Peak Tx loading:    65.0%
    Avg Tx loading:     27.2%

  --- Q-Learning (two-phase, warm-started from DP) ---
  Q-table initialised from DP value function
  Phase 1: Refining arbitrage (penalty=0.0, 50000 episodes)
  Episode 2500/50000  avg_reward=   31.23  avg_violations=  0.0  epsilon=0.274
  Episode 5000/50000  avg_reward=   33.37  avg_violations=  0.0  epsilon=0.251
  Episode 7500/50000  avg_reward=   33.64  avg_violations=  0.0  epsilon=0.229
  Episode 10000/50000  avg_reward=   37.37  avg_violations=  0.0  epsilon=0.210
  Episode 12500/50000  avg_reward=   37.80  avg_violations=  0.0  epsilon=0.192
  Episode 15000/50000  avg_reward=   37.05  avg_violations=  0.0  epsilon=0.175
  Episode 17500/50000  avg_reward=   39.52  avg_violations=  0.0  epsilon=0.160
  Episode 20000/50000  avg_reward=   39.46  avg_violations=  0.0  epsilon=0.147
  Episode 22500/50000  avg_reward=   40.65  avg_violations=  0.0  epsilon=0.134
  Episode 25000/50000  avg_reward=   43.31  avg_violations=  0.0  epsilon=0.122
  Episode 27500/50000  avg_reward=   42.05  avg_violations=  0.0  epsilon=0.112
  Episode 30000/50000  avg_reward=   43.19  avg_violations=  0.0  epsilon=0.102
  Episode 32500/50000  avg_reward=   43.92  avg_violations=  0.0  epsilon=0.094
  Episode 35000/50000  avg_reward=   43.51  avg_violations=  0.0  epsilon=0.086
  Episode 37500/50000  avg_reward=   45.19  avg_violations=  0.0  epsilon=0.078
  Episode 40000/50000  avg_reward=   44.94  avg_violations=  0.0  epsilon=0.072
  Episode 42500/50000  avg_reward=   45.39  avg_violations=  0.0  epsilon=0.065
  Episode 45000/50000  avg_reward=   44.67  avg_violations=  0.0  epsilon=0.060
  Episode 47500/50000  avg_reward=   46.32  avg_violations=  0.0  epsilon=0.055
  Episode 50000/50000  avg_reward=   47.50  avg_violations=  0.0  epsilon=0.050
  Phase 1 result: revenue=$47.50, violations=0.0
  Q-table saved: data/q_tables/Q_phase1_80kW_400kWh.npz (shape (80, 48, 33))

  Phase 2: Learning violation avoidance (penalty=5.0, 80000 episodes)
  Episode 2500/80000  avg_reward=   34.65  avg_violations=  1.8  epsilon=0.087
  Episode 5000/80000  avg_reward=   33.47  avg_violations=  2.0  epsilon=0.075
  Episode 7500/80000  avg_reward=   39.08  avg_violations=  1.3  epsilon=0.065
  Episode 10000/80000  avg_reward=   39.05  avg_violations=  1.2  epsilon=0.056
  Episode 12500/80000  avg_reward=   41.85  avg_violations=  0.6  epsilon=0.049
  Episode 15000/80000  avg_reward=   43.86  avg_violations=  0.6  epsilon=0.042
  Episode 17500/80000  avg_reward=   39.80  avg_violations=  1.4  epsilon=0.037
  Episode 20000/80000  avg_reward=   42.83  avg_violations=  0.8  epsilon=0.032
  Episode 22500/80000  avg_reward=   45.36  avg_violations=  0.2  epsilon=0.027
  Episode 25000/80000  avg_reward=   44.95  avg_violations=  0.5  epsilon=0.024
  Episode 27500/80000  avg_reward=   44.13  avg_violations=  0.7  epsilon=0.021
  Episode 30000/80000  avg_reward=   45.72  avg_violations=  0.4  epsilon=0.018
  Episode 32500/80000  avg_reward=   46.20  avg_violations=  0.3  epsilon=0.015
  Episode 35000/80000  avg_reward=   46.92  avg_violations=  0.3  epsilon=0.013
  Episode 37500/80000  avg_reward=   47.21  avg_violations=  0.1  epsilon=0.012
  Episode 40000/80000  avg_reward=   46.48  avg_violations=  0.3  epsilon=0.010
  Episode 42500/80000  avg_reward=   46.83  avg_violations=  0.3  epsilon=0.009
  Episode 45000/80000  avg_reward=   48.20  avg_violations=  0.1  epsilon=0.007
  Episode 47500/80000  avg_reward=   47.99  avg_violations=  0.2  epsilon=0.006
  Episode 50000/80000  avg_reward=   47.19  avg_violations=  0.2  epsilon=0.006
  Episode 52500/80000  avg_reward=   47.74  avg_violations=  0.1  epsilon=0.005
  Episode 55000/80000  avg_reward=   48.01  avg_violations=  0.1  epsilon=0.004
  Episode 57500/80000  avg_reward=   48.27  avg_violations=  0.0  epsilon=0.004
  Episode 60000/80000  avg_reward=   48.58  avg_violations=  0.0  epsilon=0.003
  Episode 62500/80000  avg_reward=   48.86  avg_violations=  0.0  epsilon=0.003
  Episode 65000/80000  avg_reward=   48.71  avg_violations=  0.0  epsilon=0.002
  Episode 67500/80000  avg_reward=   48.81  avg_violations=  0.0  epsilon=0.002
  Episode 70000/80000  avg_reward=   48.77  avg_violations=  0.0  epsilon=0.002
  Episode 72500/80000  avg_reward=   48.65  avg_violations=  0.0  epsilon=0.002
  Episode 75000/80000  avg_reward=   48.64  avg_violations=  0.0  epsilon=0.001
  Episode 77500/80000  avg_reward=   48.93  avg_violations=  0.0  epsilon=0.001
  Episode 80000/80000  avg_reward=   48.88  avg_violations=  0.0  epsilon=0.001
  Phase 2 result: revenue=$48.88, violations=0.0
  Q-table saved: data/q_tables/Q_phase2_80kW_400kWh.npz (shape (80, 48, 33))

  Phase 2 training summary:
  Episodes trained:        80000
  Avg reward (last 50):    48.88
  Avg revenue (last 50):   $48.88
  Avg violations (last 50): 0.0
  Zero-violation episodes:  100%

  Summary (RL ±80kW 400kWh):
    Voltage range:      0.9413 – 1.0960 pu
    Voltage violations: 0 of 48 periods
    Total losses:       78.02 kWh
    Peak Tx loading:    65.0%
    Avg Tx loading:     26.1%

======================================================================
  ±100 kW dispatch, 200 kWh capacity
======================================================================

  --- DP Solver ---
  Revenue: $41.23

  Summary (DP ±100kW 200kWh):
    Voltage range:      0.9264 – 1.1100 pu
    Voltage violations: 10 of 48 periods
    Violation times:    06:00, 12:00, 12:30, 13:00, 17:00, 18:30, 19:00, 19:30, 20:00, 20:30
    Total losses:       78.27 kWh
    Peak Tx loading:    73.5%
    Avg Tx loading:     27.8%

  --- Q-Learning (two-phase, warm-started from DP) ---
  Q-table initialised from DP value function
  Phase 1: Refining arbitrage (penalty=0.0, 50000 episodes)
  Episode 2500/50000  avg_reward=   24.11  avg_violations=  0.0  epsilon=0.274
  Episode 5000/50000  avg_reward=   25.04  avg_violations=  0.0  epsilon=0.251
  Episode 7500/50000  avg_reward=   25.46  avg_violations=  0.0  epsilon=0.229
  Episode 10000/50000  avg_reward=   30.20  avg_violations=  0.0  epsilon=0.210
  Episode 12500/50000  avg_reward=   28.77  avg_violations=  0.0  epsilon=0.192
  Episode 15000/50000  avg_reward=   30.41  avg_violations=  0.0  epsilon=0.175
  Episode 17500/50000  avg_reward=   30.57  avg_violations=  0.0  epsilon=0.160
  Episode 20000/50000  avg_reward=   32.09  avg_violations=  0.0  epsilon=0.147
  Episode 22500/50000  avg_reward=   34.16  avg_violations=  0.0  epsilon=0.134
  Episode 25000/50000  avg_reward=   34.03  avg_violations=  0.0  epsilon=0.122
  Episode 27500/50000  avg_reward=   34.17  avg_violations=  0.0  epsilon=0.112
  Episode 30000/50000  avg_reward=   35.55  avg_violations=  0.0  epsilon=0.102
  Episode 32500/50000  avg_reward=   36.26  avg_violations=  0.0  epsilon=0.094
  Episode 35000/50000  avg_reward=   36.03  avg_violations=  0.0  epsilon=0.086
  Episode 37500/50000  avg_reward=   36.82  avg_violations=  0.0  epsilon=0.078
  Episode 40000/50000  avg_reward=   37.62  avg_violations=  0.0  epsilon=0.072
  Episode 42500/50000  avg_reward=   38.31  avg_violations=  0.0  epsilon=0.065
  Episode 45000/50000  avg_reward=   38.39  avg_violations=  0.0  epsilon=0.060
  Episode 47500/50000  avg_reward=   38.36  avg_violations=  0.0  epsilon=0.055
  Episode 50000/50000  avg_reward=   38.74  avg_violations=  0.0  epsilon=0.050
  Phase 1 result: revenue=$38.74, violations=0.0
  Q-table saved: data/q_tables/Q_phase1_100kW_200kWh.npz (shape (100, 48, 33))

  Phase 2: Learning violation avoidance (penalty=10.0, 100000 episodes)
  Episode 2500/100000  avg_reward=   -9.65  avg_violations=  4.0  epsilon=0.089
  Episode 5000/100000  avg_reward=   -2.19  avg_violations=  3.1  epsilon=0.079
  Episode 7500/100000  avg_reward=  -11.63  avg_violations=  4.2  epsilon=0.071
  Episode 10000/100000  avg_reward=   12.68  avg_violations=  1.8  epsilon=0.063
  Episode 12500/100000  avg_reward=   18.63  avg_violations=  1.2  epsilon=0.056
  Episode 15000/100000  avg_reward=   18.98  avg_violations=  1.4  epsilon=0.050
  Episode 17500/100000  avg_reward=   18.45  avg_violations=  1.3  epsilon=0.045
  Episode 20000/100000  avg_reward=   20.09  avg_violations=  1.2  epsilon=0.040
  Episode 22500/100000  avg_reward=   20.30  avg_violations=  1.2  epsilon=0.035
  Episode 25000/100000  avg_reward=   25.00  avg_violations=  0.8  epsilon=0.032
  Episode 27500/100000  avg_reward=   22.62  avg_violations=  0.9  epsilon=0.028
  Episode 30000/100000  avg_reward=   22.26  avg_violations=  1.0  epsilon=0.025
  Episode 32500/100000  avg_reward=   30.15  avg_violations=  0.3  epsilon=0.022
  Episode 35000/100000  avg_reward=   26.99  avg_violations=  0.7  epsilon=0.020
  Episode 37500/100000  avg_reward=   33.89  avg_violations=  0.1  epsilon=0.018
  Episode 40000/100000  avg_reward=   31.50  avg_violations=  0.3  epsilon=0.016
  Episode 42500/100000  avg_reward=   30.61  avg_violations=  0.4  epsilon=0.014
  Episode 45000/100000  avg_reward=   33.58  avg_violations=  0.1  epsilon=0.013
  Episode 47500/100000  avg_reward=   32.60  avg_violations=  0.3  epsilon=0.011
  Episode 50000/100000  avg_reward=   31.43  avg_violations=  0.4  epsilon=0.010
  Episode 52500/100000  avg_reward=   34.91  avg_violations=  0.1  epsilon=0.009
  Episode 55000/100000  avg_reward=   34.85  avg_violations=  0.1  epsilon=0.008
  Episode 57500/100000  avg_reward=   33.66  avg_violations=  0.2  epsilon=0.007
  Episode 60000/100000  avg_reward=   35.35  avg_violations=  0.0  epsilon=0.006
  Episode 62500/100000  avg_reward=   34.23  avg_violations=  0.1  epsilon=0.006
  Episode 65000/100000  avg_reward=   34.56  avg_violations=  0.2  epsilon=0.005
  Episode 67500/100000  avg_reward=   35.65  avg_violations=  0.0  epsilon=0.004
  Episode 70000/100000  avg_reward=   35.73  avg_violations=  0.0  epsilon=0.004
  Episode 72500/100000  avg_reward=   35.97  avg_violations=  0.0  epsilon=0.004
  Episode 75000/100000  avg_reward=   32.70  avg_violations=  0.3  epsilon=0.003
  Episode 77500/100000  avg_reward=   35.68  avg_violations=  0.0  epsilon=0.003
  Episode 80000/100000  avg_reward=   33.07  avg_violations=  0.3  epsilon=0.003
  Episode 82500/100000  avg_reward=   35.05  avg_violations=  0.1  epsilon=0.002
  Episode 85000/100000  avg_reward=   33.99  avg_violations=  0.2  epsilon=0.002
  Episode 87500/100000  avg_reward=   36.27  avg_violations=  0.0  epsilon=0.002
  Episode 90000/100000  avg_reward=   35.92  avg_violations=  0.0  epsilon=0.002
  Episode 92500/100000  avg_reward=   36.11  avg_violations=  0.0  epsilon=0.001
  Episode 95000/100000  avg_reward=   35.98  avg_violations=  0.0  epsilon=0.001
  Episode 97500/100000  avg_reward=   36.31  avg_violations=  0.0  epsilon=0.001
  Episode 100000/100000  avg_reward=   36.29  avg_violations=  0.0  epsilon=0.001
  Phase 2 result: revenue=$36.29, violations=0.0
  Q-table saved: data/q_tables/Q_phase2_100kW_200kWh.npz (shape (100, 48, 33))

  Phase 2 training summary:
  Episodes trained:        100000
  Avg reward (last 50):    36.29
  Avg revenue (last 50):   $36.29
  Avg violations (last 50): 0.0
  Zero-violation episodes:  100%

  Summary (RL ±100kW 200kWh):
    Voltage range:      0.9406 – 1.0968 pu
    Voltage violations: 0 of 48 periods
    Total losses:       68.58 kWh
    Peak Tx loading:    65.5%
    Avg Tx loading:     25.4%

======================================================================
  ±100 kW dispatch, 300 kWh capacity
======================================================================

  --- DP Solver ---
  Revenue: $50.54

  Summary (DP ±100kW 300kWh):
    Voltage range:      0.9264 – 1.1100 pu
    Voltage violations: 10 of 48 periods
    Violation times:    06:00, 11:00, 11:30, 12:00, 12:30, 13:00, 19:00, 19:30, 20:00, 20:30
    Total losses:       85.79 kWh
    Peak Tx loading:    73.5%
    Avg Tx loading:     27.7%

  --- Q-Learning (two-phase, warm-started from DP) ---
  Q-table initialised from DP value function
  Phase 1: Refining arbitrage (penalty=0.0, 50000 episodes)
  Episode 2500/50000  avg_reward=   29.63  avg_violations=  0.0  epsilon=0.274
  Episode 5000/50000  avg_reward=   34.83  avg_violations=  0.0  epsilon=0.251
  Episode 7500/50000  avg_reward=   35.52  avg_violations=  0.0  epsilon=0.229
  Episode 10000/50000  avg_reward=   33.85  avg_violations=  0.0  epsilon=0.210
  Episode 12500/50000  avg_reward=   37.39  avg_violations=  0.0  epsilon=0.192
  Episode 15000/50000  avg_reward=   38.40  avg_violations=  0.0  epsilon=0.175
  Episode 17500/50000  avg_reward=   39.18  avg_violations=  0.0  epsilon=0.160
  Episode 20000/50000  avg_reward=   40.96  avg_violations=  0.0  epsilon=0.147
  Episode 22500/50000  avg_reward=   42.75  avg_violations=  0.0  epsilon=0.134
  Episode 25000/50000  avg_reward=   41.28  avg_violations=  0.0  epsilon=0.122
  Episode 27500/50000  avg_reward=   43.16  avg_violations=  0.0  epsilon=0.112
  Episode 30000/50000  avg_reward=   44.24  avg_violations=  0.0  epsilon=0.102
  Episode 32500/50000  avg_reward=   43.86  avg_violations=  0.0  epsilon=0.094
  Episode 35000/50000  avg_reward=   44.84  avg_violations=  0.0  epsilon=0.086
  Episode 37500/50000  avg_reward=   44.10  avg_violations=  0.0  epsilon=0.078
  Episode 40000/50000  avg_reward=   45.85  avg_violations=  0.0  epsilon=0.072
  Episode 42500/50000  avg_reward=   46.44  avg_violations=  0.0  epsilon=0.065
  Episode 45000/50000  avg_reward=   46.84  avg_violations=  0.0  epsilon=0.060
  Episode 47500/50000  avg_reward=   47.71  avg_violations=  0.0  epsilon=0.055
  Episode 50000/50000  avg_reward=   47.01  avg_violations=  0.0  epsilon=0.050
  Phase 1 result: revenue=$47.01, violations=0.0
  Q-table saved: data/q_tables/Q_phase1_100kW_300kWh.npz (shape (100, 48, 33))

  Phase 2: Learning violation avoidance (penalty=10.0, 100000 episodes)
  Episode 2500/100000  avg_reward=  -12.36  avg_violations=  5.2  epsilon=0.089
  Episode 5000/100000  avg_reward=   -1.97  avg_violations=  4.1  epsilon=0.079
  Episode 7500/100000  avg_reward=   12.26  avg_violations=  2.7  epsilon=0.071
  Episode 10000/100000  avg_reward=   10.62  avg_violations=  2.8  epsilon=0.063
  Episode 12500/100000  avg_reward=   12.38  avg_violations=  2.6  epsilon=0.056
  Episode 15000/100000  avg_reward=   15.79  avg_violations=  2.4  epsilon=0.050
  Episode 17500/100000  avg_reward=   21.58  avg_violations=  1.8  epsilon=0.045
  Episode 20000/100000  avg_reward=   21.65  avg_violations=  1.9  epsilon=0.040
  Episode 22500/100000  avg_reward=   18.02  avg_violations=  2.1  epsilon=0.035
   Episode 25000/100000  avg_reward=   21.61  avg_violations=  1.9  epsilon=0.032
  Episode 27500/100000  avg_reward=   15.92  avg_violations=  2.4  epsilon=0.028
  Episode 30000/100000  avg_reward=   24.42  avg_violations=  1.7  epsilon=0.025
  Episode 32500/100000  avg_reward=   22.86  avg_violations=  1.7  epsilon=0.022
  Episode 35000/100000  avg_reward=   26.18  avg_violations=  1.6  epsilon=0.020
  Episode 37500/100000  avg_reward=   25.64  avg_violations=  1.6  epsilon=0.018
  Episode 40000/100000  avg_reward=   25.88  avg_violations=  1.7  epsilon=0.016
  Episode 42500/100000  avg_reward=   30.25  avg_violations=  1.3  epsilon=0.014
  Episode 45000/100000  avg_reward=   32.41  avg_violations=  1.1  epsilon=0.013
  Episode 47500/100000  avg_reward=   30.83  avg_violations=  1.3  epsilon=0.011
  Episode 50000/100000  avg_reward=   31.29  avg_violations=  1.3  epsilon=0.010
  Episode 52500/100000  avg_reward=   30.38  avg_violations=  1.4  epsilon=0.009
  Episode 55000/100000  avg_reward=   31.58  avg_violations=  1.3  epsilon=0.008
  Episode 57500/100000  avg_reward=   40.54  avg_violations=  0.3  epsilon=0.007
  Episode 60000/100000  avg_reward=   37.55  avg_violations=  0.6  epsilon=0.006
  Episode 62500/100000  avg_reward=   43.95  avg_violations=  0.0  epsilon=0.006
  Episode 65000/100000  avg_reward=   43.66  avg_violations=  0.0  epsilon=0.005
  Episode 67500/100000  avg_reward=   43.35  avg_violations=  0.1  epsilon=0.004
  Episode 70000/100000  avg_reward=   43.72  avg_violations=  0.1  epsilon=0.004
  Episode 72500/100000  avg_reward=   41.66  avg_violations=  0.3  epsilon=0.004
  Episode 75000/100000  avg_reward=   43.45  avg_violations=  0.0  epsilon=0.003
  Episode 77500/100000  avg_reward=   41.14  avg_violations=  0.3  epsilon=0.003
  Episode 80000/100000  avg_reward=   43.71  avg_violations=  0.0  epsilon=0.003
  Episode 82500/100000  avg_reward=   44.51  avg_violations=  0.0  epsilon=0.002
  Episode 85000/100000  avg_reward=   44.22  avg_violations=  0.0  epsilon=0.002
  Episode 87500/100000  avg_reward=   44.53  avg_violations=  0.0  epsilon=0.002
  Episode 90000/100000  avg_reward=   44.47  avg_violations=  0.0  epsilon=0.002
  Episode 92500/100000  avg_reward=   43.96  avg_violations=  0.0  epsilon=0.001
  Episode 95000/100000  avg_reward=   44.21  avg_violations=  0.0  epsilon=0.001
  Episode 97500/100000  avg_reward=   44.25  avg_violations=  0.0  epsilon=0.001
  Episode 100000/100000  avg_reward=   44.53  avg_violations=  0.0  epsilon=0.001
  Phase 2 result: revenue=$44.53, violations=0.0
  Q-table saved: data/q_tables/Q_phase2_100kW_300kWh.npz (shape (100, 48, 33))

  Phase 2 training summary:
  Episodes trained:        100000
  Avg reward (last 50):    44.53
  Avg revenue (last 50):   $44.53
  Avg violations (last 50): 0.0
  Zero-violation episodes:  100%

  Summary (RL ±100kW 300kWh):
    Voltage range:      0.9406 – 1.0992 pu
    Voltage violations: 0 of 48 periods
    Total losses:       73.57 kWh
    Peak Tx loading:    66.0%
    Avg Tx loading:     25.6%

======================================================================
  ±100 kW dispatch, 400 kWh capacity
======================================================================

  --- DP Solver ---
  Revenue: $56.56

  Summary (DP ±100kW 400kWh):
    Voltage range:      0.9264 – 1.1100 pu
    Voltage violations: 10 of 48 periods
    Violation times:    06:00, 11:00, 11:30, 12:00, 12:30, 13:00, 13:30, 19:30, 20:00, 20:30
    Total losses:       95.44 kWh
    Peak Tx loading:    73.5%
    Avg Tx loading:     29.4%

  --- Q-Learning (two-phase, warm-started from DP) ---
  Q-table initialised from DP value function
  Phase 1: Refining arbitrage (penalty=0.0, 50000 episodes)
  Episode 2500/50000  avg_reward=   36.74  avg_violations=  0.0  epsilon=0.274
  Episode 5000/50000  avg_reward=   38.13  avg_violations=  0.0  epsilon=0.251
  Episode 7500/50000  avg_reward=   39.77  avg_violations=  0.0  epsilon=0.229
  Episode 10000/50000  avg_reward=   41.08  avg_violations=  0.0  epsilon=0.210
  Episode 12500/50000  avg_reward=   43.81  avg_violations=  0.0  epsilon=0.192
  Episode 15000/50000  avg_reward=   44.44  avg_violations=  0.0  epsilon=0.175
  Episode 17500/50000  avg_reward=   43.68  avg_violations=  0.0  epsilon=0.160
  Episode 20000/50000  avg_reward=   45.86  avg_violations=  0.0  epsilon=0.147
  Episode 22500/50000  avg_reward=   45.48  avg_violations=  0.0  epsilon=0.134
  Episode 25000/50000  avg_reward=   46.45  avg_violations=  0.0  epsilon=0.122
  Episode 27500/50000  avg_reward=   48.80  avg_violations=  0.0  epsilon=0.112
  Episode 30000/50000  avg_reward=   49.07  avg_violations=  0.0  epsilon=0.102
  Episode 32500/50000  avg_reward=   51.09  avg_violations=  0.0  epsilon=0.094
  Episode 35000/50000  avg_reward=   51.87  avg_violations=  0.0  epsilon=0.086
  Episode 37500/50000  avg_reward=   51.24  avg_violations=  0.0  epsilon=0.078
  Episode 40000/50000  avg_reward=   51.27  avg_violations=  0.0  epsilon=0.072
  Episode 42500/50000  avg_reward=   52.63  avg_violations=  0.0  epsilon=0.065
  Episode 45000/50000  avg_reward=   52.64  avg_violations=  0.0  epsilon=0.060
  Episode 47500/50000  avg_reward=   52.62  avg_violations=  0.0  epsilon=0.055
  Episode 50000/50000  avg_reward=   53.75  avg_violations=  0.0  epsilon=0.050
  Phase 1 result: revenue=$53.75, violations=0.0
  Q-table saved: data/q_tables/Q_phase1_100kW_400kWh.npz (shape (120, 48, 33))

  Phase 2: Learning violation avoidance (penalty=10.0, 100000 episodes)
  Episode 2500/100000  avg_reward=  -12.49  avg_violations=  6.0  epsilon=0.089
  Episode 5000/100000  avg_reward=   -1.36  avg_violations=  4.7  epsilon=0.079
  Episode 7500/100000  avg_reward=    7.43  avg_violations=  3.6  epsilon=0.071
  Episode 10000/100000  avg_reward=   11.05  avg_violations=  3.2  epsilon=0.063
  Episode 12500/100000  avg_reward=   21.74  avg_violations=  2.2  epsilon=0.056
  Episode 15000/100000  avg_reward=   27.52  avg_violations=  1.7  epsilon=0.050
  Episode 17500/100000  avg_reward=   25.53  avg_violations=  2.0  epsilon=0.045
  Episode 20000/100000  avg_reward=   29.64  avg_violations=  1.7  epsilon=0.040
  Episode 22500/100000  avg_reward=   20.80  avg_violations=  2.4  epsilon=0.035
  Episode 25000/100000  avg_reward=   27.15  avg_violations=  1.9  epsilon=0.032
  Episode 27500/100000  avg_reward=   31.83  avg_violations=  1.4  epsilon=0.028
  Episode 30000/100000  avg_reward=   30.98  avg_violations=  1.3  epsilon=0.025
  Episode 32500/100000  avg_reward=   40.17  avg_violations=  0.6  epsilon=0.022
  Episode 35000/100000  avg_reward=   35.87  avg_violations=  1.0  epsilon=0.020
  Episode 37500/100000  avg_reward=   41.15  avg_violations=  0.6  epsilon=0.018
  Episode 40000/100000  avg_reward=   40.57  avg_violations=  0.6  epsilon=0.016
  Episode 42500/100000  avg_reward=   40.83  avg_violations=  0.6  epsilon=0.014
  Episode 45000/100000  avg_reward=   39.48  avg_violations=  0.8  epsilon=0.013
  Episode 47500/100000  avg_reward=   47.02  avg_violations=  0.1  epsilon=0.011
  Episode 50000/100000  avg_reward=   43.57  avg_violations=  0.4  epsilon=0.010
  Episode 52500/100000  avg_reward=   46.84  avg_violations=  0.1  epsilon=0.009
  Episode 55000/100000  avg_reward=   45.90  avg_violations=  0.2  epsilon=0.008
  Episode 57500/100000  avg_reward=   45.06  avg_violations=  0.3  epsilon=0.007
  Episode 60000/100000  avg_reward=   45.96  avg_violations=  0.2  epsilon=0.006
  Episode 62500/100000  avg_reward=   47.86  avg_violations=  0.0  epsilon=0.006
  Episode 65000/100000  avg_reward=   47.35  avg_violations=  0.1  epsilon=0.005
  Episode 67500/100000  avg_reward=   46.16  avg_violations=  0.2  epsilon=0.004
  Episode 70000/100000  avg_reward=   48.28  avg_violations=  0.0  epsilon=0.004
  Episode 72500/100000  avg_reward=   47.50  avg_violations=  0.1  epsilon=0.004
  Episode 75000/100000  avg_reward=   48.24  avg_violations=  0.0  epsilon=0.003
  Episode 77500/100000  avg_reward=   48.27  avg_violations=  0.0  epsilon=0.003
  Episode 80000/100000  avg_reward=   47.95  avg_violations=  0.0  epsilon=0.003
  Episode 82500/100000  avg_reward=   47.82  avg_violations=  0.1  epsilon=0.002
  Episode 85000/100000  avg_reward=   47.55  avg_violations=  0.0  epsilon=0.002
  Episode 87500/100000  avg_reward=   46.44  avg_violations=  0.2  epsilon=0.002
  Episode 90000/100000  avg_reward=   46.58  avg_violations=  0.2  epsilon=0.002
  Episode 92500/100000  avg_reward=   48.31  avg_violations=  0.0  epsilon=0.001
  Episode 95000/100000  avg_reward=   48.33  avg_violations=  0.0  epsilon=0.001
  Episode 97500/100000  avg_reward=   47.82  avg_violations=  0.0  epsilon=0.001
  Episode 100000/100000  avg_reward=   48.33  avg_violations=  0.0  epsilon=0.001
  Phase 2 result: revenue=$48.53, violations=0.0
  Q-table saved: data/q_tables/Q_phase2_100kW_400kWh.npz (shape (120, 48, 33))

  Phase 2 training summary:
  Episodes trained:        100000
  Avg reward (last 50):    48.33
  Avg revenue (last 50):   $48.53
  Avg violations (last 50): 0.0
  Zero-violation episodes:  98%

  Summary (RL ±100kW 400kWh):
    Voltage range:      0.9406 – 1.0992 pu
    Voltage violations: 0 of 48 periods
    Total losses:       81.80 kWh
    Peak Tx loading:    66.0%
    Avg Tx loading:     26.5%

  Summary (No Battery):
    Voltage range:      0.9268 – 1.0431 pu
    Voltage violations: 11 of 48 periods
    Violation times:    06:00, 06:30, 07:00, 17:00, 17:30, 18:00, 18:30, 19:00, 19:30, 20:00, 20:30
    Total losses:       57.17 kWh
    Peak Tx loading:    49.7%
    Avg Tx loading:     27.1%

==========================================================================================
  DP vs Q-LEARNING: HEAD-TO-HEAD COMPARISON
==========================================================================================
  Config            DP Rev  DP Viol  DP Loss   RL Rev  RL Viol  RL Loss
  --------------- -------- -------- -------- -------- -------- --------
  baseline             ---       11    57.2      ---       11    57.2
  ±80kW/200       $  37.08        6    70.6 $  34.44        0    64.1
  ±80kW/300       $  44.26        4    76.7 $  42.50        0    72.1
  ±80kW/400       $  49.36        3    81.4 $  48.93        0    78.0
  ±100kW/200      $  41.23       10    78.3 $  36.31        0    68.6
  ±100kW/300      $  50.54       10    85.8 $  44.53        0    73.6
  ±100kW/400      $  56.56       10    95.4 $  48.51        0    81.8

==========================================================================================
  RL IMPROVEMENT OVER DP
==========================================================================================
  Config             Rev Gap   Viol Δ     Loss Δ Assessment
  --------------- ---------- -------- ---------- --------------------
  ±80kW/200       $    -2.64       -6      -6.5 ✅ RL fixes violations
  ±80kW/300       $    -1.76       -4      -4.6 ✅ RL fixes violations
  ±80kW/400       $    -0.43       -3      -3.4 ✅ RL fixes violations
  ±100kW/200      $    -4.92      -10      -9.7 ✅ RL fixes violations
  ±100kW/300      $    -6.00      -10     -12.2 ✅ RL fixes violations
  ±100kW/400      $    -8.05      -10     -13.6 ✅ RL fixes violations

==========================================================================================
  KEY FINDINGS
==========================================================================================
  DP: no fully feasible configuration in tested range
  RL minimum feasible:  ±80kW / 200kWh ($34.44/day)

==========================================================================================
  DISPATCH PROFILE: ±80kW / 200kWh
  DP: $37.08/day, 6 violations
  RL: $34.44/day, 0 violations
==========================================================================================
  t    Time     Price    DP kW  DP SoC    RL kW  RL SoC    Diff
  --   -----   ------  ------- -------  ------- -------  ------
  0    00:00  $  59.7      +80   100.0      +35   100.0     -45
  1    00:30  $  76.2        0   138.0        0   116.6        
  2    01:00  $  74.9        0   138.0        0   116.6        
  3    01:30  $  78.9        0   138.0        0   116.6        
  4    02:00  $  80.6        0   138.0        0   116.6        
  5    02:30  $  79.8        0   138.0        0   116.6        
  6    03:00  $  62.4        0   138.0        0   116.6        
  7    03:30  $  64.2        0   138.0        0   116.6        
  8    04:00  $  62.3        0   138.0        0   116.6        
  9    04:30  $  64.3        0   138.0        0   116.6        
  10   05:00  $  75.3        0   138.0        0   116.6        
  11   05:30  $  59.6      +25   138.0      +70   116.6     +45
  12   06:00  $ 101.0        0   149.9      -10   149.9     -10
  13   06:30  $ 147.7      -80   149.9      -75   144.6      +5
  14   07:00  $ 230.4      -80   107.8      -80   105.1        
  15   07:30  $ 228.0      -80    65.7      -80    63.0        
  16   08:00  $ 103.2       -5    23.6        0    20.9      +5
  17   08:30  $  40.0        0    20.9        0    20.9        
  18   09:00  $  52.2        0    20.9        0    20.9        
  19   09:30  $  60.4        0    20.9        0    20.9        
  20   10:00  $  50.6        0    20.9        0    20.9        
  21   10:30  $  44.3        0    20.9        0    20.9        
  22   11:00  $  25.3      +60    20.9      +55    20.9      -5
  23   11:30  $  15.8      +75    49.4      +80    47.1      +5
  24   12:00  $ -13.1      +80    85.1      +80    85.1        
  25   12:30  $ -14.4      +80   123.1      +80   123.1        
  26   13:00  $ -13.9      +80   161.1      +80   161.1        
  27   13:30  $  28.6        0   199.1        0   199.1        
  28   14:00  $  36.0        0   199.1        0   199.1        
  29   14:30  $  37.3        0   199.1        0   199.1        
  30   15:00  $  51.7        0   199.1        0   199.1        
  31   15:30  $  72.9        0   199.1        0   199.1        
  32   16:00  $ 113.2        0   199.1        0   199.1        
  33   16:30  $ 162.5      -80   199.1      -80   199.1        
  34   17:00  $ 137.3      -80   156.9      -50   156.9     +30
  35   17:30  $ 173.8      -80   114.8      -80   130.6        
  36   18:00  $ 144.7      -75    72.7      -75    88.5        
  37   18:30  $ 135.0      -25    33.3      -45    49.1     -20
  38   19:00  $ 114.8        0    20.1      +40    25.4     +40
  39   19:30  $ 105.3        0    20.1      -40    44.4     -40
  40   20:00  $ 107.1        0    20.1      +45    23.3     +45
  41   20:30  $ 105.0        0    20.1      -45    44.7     -45
  42   21:00  $ 105.8        0    20.1        0    21.0        
  43   21:30  $  78.0        0    20.1        0    21.0        
  44   22:00  $  87.4        0    20.1        0    21.0        
  45   22:30  $  71.3        0    20.1        0    21.0        
  46   23:00  $  78.0        0    20.1        0    21.0        
  47   23:30  $  72.7        0    20.1        0    21.0        
  END                             20.1             21.0

  Revenue gap: $2.64/day

==========================================================================================
  DISPATCH PROFILE: ±80kW / 300kWh
  DP: $44.26/day, 4 violations
  RL: $42.50/day, 0 violations
==========================================================================================
  t    Time     Price    DP kW  DP SoC    RL kW  RL SoC    Diff
  --   -----   ------  ------- -------  ------- -------  ------
  0    00:00  $  59.7      +20   150.0        0   150.0     -20
  1    00:30  $  76.2        0   159.5        0   150.0        
  2    01:00  $  74.9        0   159.5        0   150.0        
  3    01:30  $  78.9        0   159.5        0   150.0        
  4    02:00  $  80.6        0   159.5        0   150.0        
  5    02:30  $  79.8        0   159.5        0   150.0        
  6    03:00  $  62.4        0   159.5        0   150.0        
  7    03:30  $  64.2        0   159.5        0   150.0        
  8    04:00  $  62.3        0   159.5       -5   150.0      -5
  9    04:30  $  64.3        0   159.5        0   147.4        
  10   05:00  $  75.3        0   159.5        0   147.4        
  11   05:30  $  59.6       +5   159.5      +35   147.4     +30
  12   06:00  $ 101.0        0   161.9      -10   164.0     -10
  13   06:30  $ 147.7      -80   161.9      -75   158.7      +5
  14   07:00  $ 230.4      -80   119.8      -80   119.3        
  15   07:30  $ 228.0      -80    77.7      -80    77.2        
  16   08:00  $ 103.2      -10    35.6       -5    35.0      +5
  17   08:30  $  40.0        0    30.3        0    32.4        
  18   09:00  $  52.2        0    30.3        0    32.4        
  19   09:30  $  60.4        0    30.3        0    32.4        
  20   10:00  $  50.6        0    30.3        0    32.4        
  21   10:30  $  44.3        0    30.3        0    32.4        
  22   11:00  $  25.3      +80    30.3      +80    32.4        
  23   11:30  $  15.8      +80    68.3      +80    70.4        
  24   12:00  $ -13.1      +80   106.3      +80   108.4        
  25   12:30  $ -14.4      +80   144.3      +80   146.4        
  26   13:00  $ -13.9      +80   182.3      +80   184.4        
  27   13:30  $  28.6      +80   220.3      +80   222.4        
  28   14:00  $  36.0      +75   258.3      +80   260.4      +5
  29   14:30  $  37.3      +10   293.9        0   298.4     -10
  30   15:00  $  51.7        0   298.7        0   298.4        
  31   15:30  $  72.9        0   298.7        0   298.4        
  32   16:00  $ 113.2      -35   298.7        0   298.4     +35
  33   16:30  $ 162.5      -80   280.2      -80   298.4        
  34   17:00  $ 137.3      -80   238.1      -80   256.3        
  35   17:30  $ 173.8      -80   196.0      -80   214.2        
  36   18:00  $ 144.7      -80   153.9      -75   172.1      +5
  37   18:30  $ 135.0      -80   111.8      -75   132.6      +5
  38   19:00  $ 114.8      -75    69.7      -75    93.2        
  39   19:30  $ 105.3        0    30.2      +50    53.7     +50
  40   20:00  $ 107.1        0    30.2      -40    77.4     -40
  41   20:30  $ 105.0        0    30.2      -50    56.4     -50
  42   21:00  $ 105.8        0    30.2        0    30.1        
  43   21:30  $  78.0        0    30.2        0    30.1        
  44   22:00  $  87.4        0    30.2        0    30.1        
  45   22:30  $  71.3        0    30.2        0    30.1        
  46   23:00  $  78.0        0    30.2        0    30.1        
  47   23:30  $  72.7        0    30.2        0    30.1        
  END                             30.2             30.1

  Revenue gap: $1.76/day

==========================================================================================
  DISPATCH PROFILE: ±80kW / 400kWh
  DP: $49.36/day, 3 violations
  RL: $48.93/day, 0 violations
==========================================================================================
  t    Time     Price    DP kW  DP SoC    RL kW  RL SoC    Diff
  --   -----   ------  ------- -------  ------- -------  ------
  0    00:00  $  59.7        0   200.0      +30   200.0     +30
  1    00:30  $  76.2        0   200.0        0   214.2        
  2    01:00  $  74.9        0   200.0        0   214.2        
  3    01:30  $  78.9        0   200.0        0   214.2        
  4    02:00  $  80.6        0   200.0        0   214.2        
  5    02:30  $  79.8        0   200.0        0   214.2        
  6    03:00  $  62.4        0   200.0        0   214.2        
  7    03:30  $  64.2        0   200.0        0   214.2        
  8    04:00  $  62.3        0   200.0        0   214.2        
  9    04:30  $  64.3        0   200.0        0   214.2        
  10   05:00  $  75.3        0   200.0        0   214.2        
  11   05:30  $  59.6        0   200.0        0   214.2        
  12   06:00  $ 101.0        0   200.0      -10   214.2     -10
  13   06:30  $ 147.7      -80   200.0      -80   209.0        
  14   07:00  $ 230.4      -80   157.9      -80   166.9        
  15   07:30  $ 228.0      -80   115.8      -80   124.8        
  16   08:00  $ 103.2      -60    73.7      -75    82.7     -15
  17   08:30  $  40.0      +80    42.1      +80    43.2        
  18   09:00  $  52.2        0    80.1        0    81.2        
  19   09:30  $  60.4        0    80.1        0    81.2        
  20   10:00  $  50.6        0    80.1        0    81.2        
  21   10:30  $  44.3      +30    80.1      +30    81.2        
  22   11:00  $  25.3      +80    94.4      +75    95.4      -5
  23   11:30  $  15.8      +80   132.4      +80   131.1        
  24   12:00  $ -13.1      +80   170.4      +80   169.1        
  25   12:30  $ -14.4      +80   208.4      +80   207.1        
  26   13:00  $ -13.9      +80   246.4      +80   245.1        
  27   13:30  $  28.6      +80   284.4      +80   283.1        
  28   14:00  $  36.0      +80   322.4      +80   321.1        
  29   14:30  $  37.3      +80   360.4      +80   359.1        
  30   15:00  $  51.7        0   398.4        0   397.1        
  31   15:30  $  72.9        0   398.4        0   397.1        
  32   16:00  $ 113.2      -80   398.4      -45   397.1     +35
  33   16:30  $ 162.5      -80   356.2      -80   373.4        
  34   17:00  $ 137.3      -80   314.1      -80   331.3        
  35   17:30  $ 173.8      -80   272.0      -80   289.2        
  36   18:00  $ 144.7      -80   229.9      -80   247.1        
  37   18:30  $ 135.0      -80   187.8      -80   205.0        
  38   19:00  $ 114.8      -80   145.7      -80   162.9        
  39   19:30  $ 105.3      -10   103.6      -40   120.8     -30
  40   20:00  $ 107.1      -80    98.4      -65    99.7     +15
  41   20:30  $ 105.0       -5    56.2      -45    65.5     -40
  42   21:00  $ 105.8      -25    53.6        0    41.8     +25
  43   21:30  $  78.0        0    40.5        0    41.8        
  44   22:00  $  87.4        0    40.5        0    41.8        
  45   22:30  $  71.3        0    40.5        0    41.8        
  46   23:00  $  78.0        0    40.5        0    41.8        
  47   23:30  $  72.7        0    40.5        0    41.8        
  END                             40.5             41.8

  Revenue gap: $0.43/day

==========================================================================================
  DISPATCH PROFILE: ±100kW / 200kWh
  DP: $41.23/day, 10 violations
  RL: $36.31/day, 0 violations
==========================================================================================
  t    Time     Price    DP kW  DP SoC    RL kW  RL SoC    Diff
  --   -----   ------  ------- -------  ------- -------  ------
  0    00:00  $  59.7      +88   100.0      +50   100.0     -38
  1    00:30  $  76.2        0   141.6        0   123.8        
  2    01:00  $  74.9        0   141.6        0   123.8        
  3    01:30  $  78.9        0   141.6        0   123.8        
  4    02:00  $  80.6        0   141.6        0   123.8        
  5    02:30  $  79.8        0   141.6        0   123.8        
  6    03:00  $  62.4        0   141.6       +6   123.8      +6
  7    03:30  $  64.2        0   141.6        0   126.7        
  8    04:00  $  62.3        0   141.6      +25   126.7     +25
  9    04:30  $  64.3        0   141.6        0   138.6        
  10   05:00  $  75.3        0   141.6        0   138.6        
  11   05:30  $  59.6      +88   141.6     +100   138.6     +12
  12   06:00  $ 101.0        0   183.1      -12   186.1     -12
  13   06:30  $ 147.7     -100   183.1      -94   179.5      +6
  14   07:00  $ 230.4     -100   130.5     -100   130.2        
  15   07:30  $ 228.0     -100    77.9     -100    77.5        
  16   08:00  $ 103.2       -6    25.2       -6    24.9        
  17   08:30  $  40.0        0    21.9        0    21.6        
  18   09:00  $  52.2        0    21.9        0    21.6        
  19   09:30  $  60.4        0    21.9        0    21.6        
  20   10:00  $  50.6        0    21.9        0    21.6        
  21   10:30  $  44.3        0    21.9      +88    21.6     +88
  22   11:00  $  25.3        0    21.9       -6    63.2      -6
  23   11:30  $  15.8      +56    21.9      +75    59.9     +19
  24   12:00  $ -13.1     +100    48.7      +81    95.5     -19
  25   12:30  $ -14.4     +100    96.2      +81   134.1     -19
  26   13:00  $ -13.9     +100   143.7      +56   172.7     -44
  27   13:30  $  28.6      +12   191.2        0   199.4     -12
  28   14:00  $  36.0        0   197.1        0   199.4        
  29   14:30  $  37.3        0   197.1        0   199.4        
  30   15:00  $  51.7        0   197.1        0   199.4        
  31   15:30  $  72.9        0   197.1        0   199.4        
  32   16:00  $ 113.2        0   197.1        0   199.4        
  33   16:30  $ 162.5     -100   197.1     -100   199.4        
  34   17:00  $ 137.3      -25   144.5      -38   146.8     -12
  35   17:30  $ 173.8     -100   131.3      -94   127.1      +6
  36   18:00  $ 144.7     -100    78.7      -50    77.7     +50
  37   18:30  $ 135.0       -6    26.0      -44    51.4     -38
  38   19:00  $ 114.8        0    22.8      +38    28.4     +38
  39   19:30  $ 105.3        0    22.8      -38    46.2     -38
  40   20:00  $ 107.1        0    22.8      +38    26.4     +38
  41   20:30  $ 105.0        0    22.8      -38    44.3     -38
  42   21:00  $ 105.8        0    22.8       -6    24.5      -6
  43   21:30  $  78.0        0    22.8        0    21.2        
  44   22:00  $  87.4        0    22.8        0    21.2        
  45   22:30  $  71.3        0    22.8        0    21.2        
  46   23:00  $  78.0        0    22.8        0    21.2        
  47   23:30  $  72.7        0    22.8        0    21.2        
  END                             22.8             21.2

  Revenue gap: $4.92/day

==========================================================================================
  DISPATCH PROFILE: ±100kW / 300kWh
  DP: $50.54/day, 10 violations
  RL: $44.53/day, 0 violations
==========================================================================================
  t    Time     Price    DP kW  DP SoC    RL kW  RL SoC    Diff
  --   -----   ------  ------- -------  ------- -------  ------
  0    00:00  $  59.7      +38   150.0        0   150.0     -38
  1    00:30  $  76.2        0   167.8        0   150.0        
  2    01:00  $  74.9        0   167.8        0   150.0        
  3    01:30  $  78.9        0   167.8        0   150.0        
  4    02:00  $  80.6        0   167.8        0   150.0        
  5    02:30  $  79.8        0   167.8        0   150.0        
  6    03:00  $  62.4        0   167.8        0   150.0        
  7    03:30  $  64.2        0   167.8        0   150.0        
  8    04:00  $  62.3        0   167.8       -6   150.0      -6
  9    04:30  $  64.3        0   167.8       +6   146.7      +6
  10   05:00  $  75.3        0   167.8        0   149.7        
  11   05:30  $  59.6      +50   167.8      +94   149.7     +44
  12   06:00  $ 101.0        0   191.6      -12   194.2     -12
  13   06:30  $ 147.7     -100   191.6      -94   187.6      +6
  14   07:00  $ 230.4     -100   138.9     -100   138.3        
  15   07:30  $ 228.0     -100    86.3     -100    85.7        
  16   08:00  $ 103.2       -6    33.7        0    33.0      +6
  17   08:30  $  40.0        0    30.4      +69    33.0     +69
  18   09:00  $  52.2        0    30.4        0    65.7        
  19   09:30  $  60.4        0    30.4        0    65.7        
  20   10:00  $  50.6        0    30.4       +6    65.7      +6
  21   10:30  $  44.3        0    30.4        0    68.7        
  22   11:00  $  25.3     +100    30.4      +75    68.7     -25
  23   11:30  $  15.8     +100    77.9      +62   104.3     -38
  24   12:00  $ -13.1     +100   125.4      +81   134.0     -19
  25   12:30  $ -14.4     +100   172.9      +81   172.6     -19
  26   13:00  $ -13.9     +100   220.4      +25   211.2     -75
  27   13:30  $  28.6      +62   267.9      +94   223.0     +31
  28   14:00  $  36.0        0   297.6      +62   267.6     +62
  29   14:30  $  37.3        0   297.6        0   297.2        
  30   15:00  $  51.7        0   297.6        0   297.2        
  31   15:30  $  72.9        0   297.6        0   297.2        
  32   16:00  $ 113.2        0   297.6       -6   297.2      -6
  33   16:30  $ 162.5     -100   297.6     -100   294.0        
  34   17:00  $ 137.3     -100   244.9      -94   241.3      +6
  35   17:30  $ 173.8     -100   192.3     -100   192.0        
  36   18:00  $ 144.7     -100   139.7     -100   139.4        
  37   18:30  $ 135.0     -100    87.0      -62    86.7     +38
  38   19:00  $ 114.8       -6    34.4      -44    53.8     -38
  39   19:30  $ 105.3        0    31.1      +38    30.8     +38
  40   20:00  $ 107.1        0    31.1      +38    48.6     +38
  41   20:30  $ 105.0        0    31.1      -62    66.4     -62
  42   21:00  $ 105.8        0    31.1       -6    33.5      -6
  43   21:30  $  78.0        0    31.1        0    30.2        
  44   22:00  $  87.4        0    31.1        0    30.2        
  45   22:30  $  71.3        0    31.1        0    30.2        
  46   23:00  $  78.0        0    31.1        0    30.2        
  47   23:30  $  72.7        0    31.1        0    30.2        
  END                             31.1             30.2

  Revenue gap: $6.00/day

==========================================================================================
  DISPATCH PROFILE: ±100kW / 400kWh
  DP: $56.56/day, 10 violations
  RL: $48.51/day, 0 violations
==========================================================================================
  t    Time     Price    DP kW  DP SoC    RL kW  RL SoC    Diff
  --   -----   ------  ------- -------  ------- -------  ------
  0    00:00  $  59.7        0   200.0      +31   200.0     +31
  1    00:30  $  76.2        0   200.0        0   214.8        
  2    01:00  $  74.9        0   200.0        0   214.8        
  3    01:30  $  78.9        0   200.0        0   214.8        
  4    02:00  $  80.6        0   200.0        0   214.8        
  5    02:30  $  79.8        0   200.0        0   214.8        
  6    03:00  $  62.4        0   200.0        0   214.8        
  7    03:30  $  64.2        0   200.0      +31   214.8     +31
  8    04:00  $  62.3        0   200.0       +6   229.7      +6
  9    04:30  $  64.3        0   200.0       +6   232.7      +6
  10   05:00  $  75.3        0   200.0        0   235.6        
  11   05:30  $  59.6       +6   200.0        0   235.6      -6
  12   06:00  $ 101.0        0   203.0      -12   235.6     -12
  13   06:30  $ 147.7     -100   203.0     -100   229.0        
  14   07:00  $ 230.4     -100   150.3     -100   176.4        
  15   07:30  $ 228.0     -100    97.7     -100   123.8        
  16   08:00  $ 103.2       -6    45.1      -56    71.2     -50
  17   08:30  $  40.0        0    41.8       +6    41.5      +6
  18   09:00  $  52.2        0    41.8        0    44.5        
  19   09:30  $  60.4        0    41.8       -6    44.5      -6
  20   10:00  $  50.6        0    41.8      +38    41.2     +38
  21   10:30  $  44.3        0    41.8        0    59.0        
  22   11:00  $  25.3     +100    41.8      +81    59.0     -19
  23   11:30  $  15.8     +100    89.3      +81    97.6     -19
  24   12:00  $ -13.1     +100   136.8       +6   136.2     -94
  25   12:30  $ -14.4     +100   184.3      +69   139.2     -31
  26   13:00  $ -13.9     +100   231.8      +50   171.9     -50
  27   13:30  $  28.6     +100   279.3      +94   195.6      -6
  28   14:00  $  36.0      +94   326.8     +100   240.1      +6
  29   14:30  $  37.3      +56   371.3     +100   287.6     +44
  30   15:00  $  51.7        0   398.0     +100   335.1    +100
  31   15:30  $  72.9        0   398.0        0   382.6        
  32   16:00  $ 113.2      -88   398.0      -56   382.6     +31
  33   16:30  $ 162.5     -100   352.0     -100   353.0        
  34   17:00  $ 137.3     -100   299.4     -100   300.4        
  35   17:30  $ 173.8     -100   246.7     -100   247.8        
  36   18:00  $ 144.7     -100   194.1     -100   195.1        
  37   18:30  $ 135.0     -100   141.5     -100   142.5        
  38   19:00  $ 114.8      -88    88.8      -38    89.9     +50
  39   19:30  $ 105.3        0    42.8      -56    70.1     -56
  40   20:00  $ 107.1        0    42.8      +56    40.5     +56
  41   20:30  $ 105.0        0    42.8      -50    67.2     -50
  42   21:00  $ 105.8        0    42.8        0    40.9        
  43   21:30  $  78.0        0    42.8        0    40.9        
  44   22:00  $  87.4        0    42.8        0    40.9        
  45   22:30  $  71.3        0    42.8        0    40.9        
  46   23:00  $  78.0        0    42.8        0    40.9        
  47   23:30  $  72.7        0    42.8        0    40.9        
  END                             42.8             40.9