"""
Network-constrained DP feedback loop.

Iterates between DP optimisation and OpenDSS verification
until the dispatch is both economically optimal and network-feasible.
"""

import numpy as np
from src.dp.solver import DPSolver
from src.integration.constraints import check_network, generate_constraints


def run_feedback_loop(battery, prices, load_profile, solar_profile,
                      feeder_config, dss_file,
                      dispatch_limit=50, initial_soc=100,
                      max_iterations=5):
    """
    Iterate between DP and OpenDSS until network-feasible.

    Args:
        battery: Battery instance
        prices: array of 48 spot prices ($/MWh)
        load_profile: array of 48 load multipliers
        solar_profile: array of 48 solar multipliers
        feeder_config: dict with load_names, pv_names, pv_rated_kw
        dss_file: path to DSS file
        dispatch_limit: max dispatch power (kW)
        initial_soc: starting SoC (kWh)
        max_iterations: convergence limit

    Returns:
        dict with:
            dispatch: final network-feasible dispatch
            result: DP solver output
            iterations: list of iteration summaries
            converged: bool

    Pseudocode:
    ---------------------------------------------------------------------    
    constraints = None

    for iteration = 1 to max_iterations:
        # Step 1: Solve DP
        if constraints is None:
            result = solver.solve(prices)           # unconstrained
        else:
            result = solver.solve_constrained(prices, constraints)

        dispatch = result['dispatch']

        # Step 2: Check network
        network_results = check_network(dispatch, ...)

        # Step 3: Count violations
        if no violations:
            return dispatch (converged!)

        # Step 4: Generate new constraints
        constraints = generate_constraints(network_results, battery)

    return dispatch (did not converge)
    """
    solver = DPSolver(battery, dt_hours=0.5, dispatch_limit=dispatch_limit)
    constraints = None
    all_violation_periods = set()  # accumulate across iterations
    iterations = []

    for i in range(max_iterations):
        print(f"\n  --- Iteration {i + 1} ---")

        # Step 1: Solve DP
        if constraints is None:
            print(f"  DP: unconstrained")
            result = solver.solve(prices, initial_soc=initial_soc)
        else:
            n_forced = sum(1 for d in constraints['min_discharge'] if d < -0.1)
            print(f"  DP: constrained ({n_forced} forced discharge periods)")
            result = solver.solve_constrained(prices, constraints,
                                              initial_soc=initial_soc)

        dispatch = result['dispatch']
        print(f"  Revenue: ${result['total_revenue']:.2f}")

        # Step 2: Check network
        print(f"  Network check...")
        net_results = check_network(
            dispatch, load_profile, solar_profile, feeder_config, dss_file,
            battery=battery)

        # Step 3: Count violations
        undervoltage = [r for r in net_results if r['undervoltage']]
        overvoltage = [r for r in net_results if r['overvoltage']]
        total_violations = len(undervoltage) + len(overvoltage)

        print(f"  Violations: {total_violations} "
              f"({len(undervoltage)} under, {len(overvoltage)} over)")

        iterations.append({
            'iteration': i + 1,
            'revenue': result['total_revenue'],
            'violations': total_violations,
        })

        # Step 4: Check convergence
        if total_violations == 0:
            print(f"  ✅ Converged — dispatch is network-feasible")
            return {
                'dispatch': dispatch,
                'result': result,
                'iterations': iterations,
                'converged': True,
            }

        # Step 5: Accumulate violation periods and regenerate constraints
        for r in net_results:
            if r['undervoltage']:
                all_violation_periods.add(r['t'])
            if r['overvoltage']:
                all_violation_periods.add(r['t'])

        # Build merged network_results that includes ALL historical violations
        merged_results = []
        for r in net_results:
            merged = r.copy()
            if r['t'] in all_violation_periods:
                merged['undervoltage'] = True  # keep it constrained
            merged_results.append(merged)

        constraints = generate_constraints(
                        merged_results, battery,
                        load_profile=load_profile,
                        solar_profile=solar_profile,
                        feeder_config=feeder_config,
                        dss_file=dss_file)

    print(f"  ⚠️  Did not converge after {max_iterations} iterations")
    return {
        'dispatch': dispatch,
        'result': result,
        'iterations': iterations,
        'converged': False,
    }


def print_iteration_summary(iterations):
    print(f"\n  {'Iter':>5} {'Revenue':>10} {'Violations':>12}")
    print(f"  {'-'*5} {'-'*10} {'-'*12}")
    for r in iterations:
        print(f"  {r['iteration']:>5} ${r['revenue']:>9.2f} {r['violations']:>12}")

    if len(iterations) > 1:
        cost = iterations[0]['revenue'] - iterations[-1]['revenue']
        print(f"\n  Revenue cost of network constraints: ${cost:.2f}/day")
        print(f"  Annual impact: ${cost * 365:,.0f}/year")