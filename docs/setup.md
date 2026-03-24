# Setup Guide

## Project Structure

```
community-battery/
├── requirements.txt
│
├── scripts/                        ← All runnable entry points
│   ├── download_prices.py              Download AEMO price data
│   ├── run_timeseries.py               Baseline vs DP-optimised comparison
│   ├── run_feedback.py                 DP feedback loop sensitivity analysis
│   ├── run_qlearning.py                Q-learning sensitivity (Model A: spot)
│   ├── run_qlearning_tou.py            Q-learning sensitivity (Model B: TOU)
│   ├── run_business_model_comparison.py  Model A vs Model B comparison
│   ├── run_branch_comparison.py        Branch A vs Branch B voltage analysis
│   ├── run_pypsa_annual.py             PyPSA full-year optimisation (366 days)
│   ├── run_annual_dispatch.py          PyPSA + DP + OpenDSS violations (366 days)
│   ├── run_representative_days.py      DP + RL on 5 representative price days
│   ├── run_check_dispatch.py           Verify dispatch against OpenDSS
│   ├── pick_representative_days.py     Select representative days from annual data
│   └── generate_figures.py             Generate README figures (histogram, dispatch, heatmap)
│
├── dss/
│   └── suburb_feeder_32.dss        ← OpenDSS circuit definition
│
├── src/
│   ├── dp/                         ← Dynamic programming optimiser
│   │   ├── battery.py                  Battery physical model
│   │   ├── solver.py                   Bellman equation solver
│   │   └── prices.py                   AEMO data + TOU profile builder
│   │
│   ├── opendss/                    ← Distribution network model
│   │   ├── network.py                  OpenDSS interface
│   │   ├── profiles.py                 Load and solar profiles
│   │   └── feeders.py                  Feeder element configuration
│   │
│   ├── integration/                ← DP ↔ OpenDSS feedback loop
│   │   ├── timeseries.py               Time-series power flow simulation
│   │   ├── constraints.py              Voltage constraint generation
│   │   └── feedback.py                 Iterative DP re-solve
│   │
│   ├── rl/                         ← Q-learning with network feedback
│   │   ├── environment.py              Gymnasium-style OpenDSS environment
│   │   ├── q_learning.py               Two-phase training algorithm
│   │   └── utils.py                    DP warm-start, dispatch extraction
│   │
│   ├── pypsa/                      ← Full-year LP optimisation
│   │   ├── network.py                  Single-bus battery network builder
│   │   ├── dispatch.py                 Daily optimisation + annual sweep
│   │   └── analysis.py                 Revenue statistics and distributions
│   │
│   └── stochastic/                 ← POMDP with Bayesian belief updating
│       ├── regime.py                   K-means day classification
│       ├── tauchen.py                  Price grid and transition matrices
│       ├── belief.py                   Bayesian belief update and grid
│       ├── solver.py                   POMDP backward induction
│       ├── simulate.py                 Full-year simulation
│       └── analysis.py                 Value of information analysis
│
├── data/
│   ├── aemo/                       ← AEMO price data
│   │   ├── nem_prices_NSW1_clean.csv   Cleaned 2024 30-min prices
│   │   ├── nem_prices_NSW1_2018_2023_clean.csv  Training data (6 years)
│   │   └── prices_*.csv                Representative day extracts
│   ├── pypsa/
│   │   ├── annual_revenue.csv          366-day PyPSA revenue results
│   │   └── annual_dispatch_results.csv 366-day PyPSA + DP with violations
│   ├── stochastic/                 ← POMDP simulation results
│   │   ├── pomdp_annual_results.csv    366-day out-of-sample results
│   │   └── pomdp_test_output.log       Representative day detailed output
│   └── q_tables/                   ← Trained Q-tables (.npz)
│
├── docs/
│   ├── figures/                    ← Generated figures for README
│   │   ├── revenue_histogram.png
│   │   ├── dispatch_comparison.png
│   │   └── violations_heatmap.png
│   ├── methods.md                  ← Full mathematical formulation
│   ├── business_models.md          ← Model A (spot) vs Model B (TOU) comparison
│   ├── dp_vs_rl_findings.md        ← Dispatch comparison analysis
│   ├── npv_analysis.md             ← NPV model and sensitivity
│   ├── policy_implications.md      ← Policy recommendations
│   ├── annual_revenue_analysis.md  ← PyPSA methodology and LP formulation
│   ├── full_year_dispatch_analysis.md ← Integrated annual results
│   └── stochastic_dp.md           ← POMDP formulation, Tauchen model, value of information
│
└── tests/
    └── test_battery.py
```

## Quick Start

```bash
# Install dependencies (uv virtual environment)
uv pip install -r requirements.txt

# Download AEMO NSW1 price data (Jan–Dec 2024)
python -m scripts.download_prices

# Single-day analysis
python -m scripts.run_timeseries               # Baseline vs DP comparison
python -m scripts.run_qlearning                # RL spot price training (9 configs)
python -m scripts.run_qlearning_tou            # RL TOU price training (9 configs)

# Full-year analysis
python -m scripts.run_pypsa_annual             # PyPSA LP, 366 days (~60s)
python -m scripts.run_annual_dispatch          # PyPSA + DP + violations (~36 min)
python -m scripts.run_representative_days      # DP + RL on 5 representative days (~50 min)

# Analyse cached results
python -m scripts.run_pypsa_annual --cached
python -m scripts.run_annual_dispatch --cached

# Stochastic DP (POMDP with Bayesian belief updating)
python -m scripts.download_prices              # Downloads 2018–2024 data if needed
python -m src.stochastic.simulate              # Full-year POMDP simulation (~3 min)
python -m src.stochastic.analysis              # Value of information analysis

# Generate figures for README
python -m scripts.generate_figures             # Revenue histogram + dispatch comparison
python -m scripts.generate_figures --with-heatmap  # + violations heatmap (~36 min)
```

## Dependencies

| Package | Purpose |
|---------|---------|
| `opendssdirect.py` | OpenDSS power flow engine |
| `numpy` | Numerical computation |
| `pandas` | Data handling and resampling |
| `requests` | AEMO data download |
| `pypsa` | Linear optimal power flow |
| `highspy` | HiGHS LP solver for PyPSA |
| `scikit-learn` | K-means regime classification (stochastic DP) |

## Detailed Documentation

| Document | Contents |
|----------|----------|
| [docs/business_models.md](docs/business_models.md) | Model A (spot) vs Model B (TOU): price signals, revenue characteristics, risk comparison |
| [docs/full_year_dispatch_analysis.md](docs/full_year_dispatch_analysis.md) | 366-day PyPSA + DP + RL analysis with violations, seasonal breakdown, representative day selection |
| [docs/dp_vs_rl_findings.md](docs/dp_vs_rl_findings.md) | Detailed dispatch profiles, RL strategy analysis, 9-config sensitivity results |
| [docs/npv_analysis.md](docs/npv_analysis.md) | 20-year NPV model, three-tier DNSP benefit framework, sensitivity analysis |
| [docs/policy_implications.md](docs/policy_implications.md) | Recommendations for DNSPs, regulators, and community battery operators |
| [docs/annual_revenue_analysis.md](docs/annual_revenue_analysis.md) | PyPSA LP methodology, objective function, constraints, revenue extraction |
| [docs/stochastic_dp.md](docs/stochastic_dp.md) | POMDP formulation, Tauchen model, Bayesian belief updating, value of information |
| [docs/methods.md](docs/methods.md) | Full mathematical formulation: DP, Q-learning, OpenDSS integration |