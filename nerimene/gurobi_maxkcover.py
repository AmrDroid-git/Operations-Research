# src/gurobi_maxkcover.py
import time
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

# try import gurobi, but allow absence
try:
    import gurobipy as gp
    from gurobipy import GRB
except Exception:
    gp = None
    GRB = None

def build_coverage_lists(candidates_df: pd.DataFrame, population_df: pd.DataFrame, radius: float):
    """
    Returns:
     - coverage_lists: list (len = n_cand) of numpy arrays of population indices covered by candidate j
     - pop_to_cands: list (len = n_pop) of lists of candidate indices covering population point i
    """
    pop_coords = np.column_stack((population_df['x'].values, population_df['y'].values))
    cand_coords = np.column_stack((candidates_df['x'].values, candidates_df['y'].values))
    tree = cKDTree(pop_coords)
    coverage_lists = [np.array(tree.query_ball_point(pt, r=radius), dtype=int) for pt in cand_coords]
    pop_to_cands = [[] for _ in range(len(pop_coords))]
    for j, cov in enumerate(coverage_lists):
        for i in cov:
            pop_to_cands[i].append(j)
    return coverage_lists, pop_to_cands

def solve_max_k_coverage_with_gurobi(candidates_df: pd.DataFrame, population_df: pd.DataFrame,
                                     k: int, radius: float, time_limit: float = None, mip_gap: float = 1e-6, threads: int = 0):
    """
    Solve max-k-coverage using Gurobi MIP.
    Returns: selected_ids (list), total_covered (float), model (gurobi model or None)
    Raises ImportError if gurobipy is not available.
    """
    if gp is None:
        raise ImportError("gurobipy not available in this environment.")

    candidates = candidates_df.reset_index(drop=True).copy()
    population = population_df.reset_index(drop=True).copy()

    for col in ('x','y'):
        if col not in candidates.columns or col not in population.columns:
            raise ValueError(f"Both candidates and population must contain column '{col}'")
        candidates[col] = pd.to_numeric(candidates[col], errors='coerce')
        population[col] = pd.to_numeric(population[col], errors='coerce')
    if 'pop' not in population.columns:
        population['pop'] = 1.0
    population['pop'] = pd.to_numeric(population['pop'], errors='coerce').fillna(0.0)

    n_cand = len(candidates); n_pop = len(population)
    if n_cand == 0 or n_pop == 0 or k <= 0:
        return [], 0.0, None

    coverage_lists, pop_to_cands = build_coverage_lists(candidates, population, radius)

    m = gp.Model("max_k_coverage")
    # reduce console output
    m.Params.OutputFlag = 0

    if time_limit is not None:
        m.setParam('TimeLimit', float(time_limit))
    if mip_gap is not None:
        m.setParam('MIPGap', float(mip_gap))
    if threads and threads > 0:
        m.setParam('Threads', int(threads))

    # decision vars
    x = m.addVars(n_cand, vtype=GRB.BINARY, name="x")
    y = m.addVars(n_pop, vtype=GRB.BINARY, name="y")

    m.addConstr(x.sum() == int(k), name="select_k")
    for i in range(n_pop):
        covering = pop_to_cands[i]
        if len(covering) == 0:
            m.addConstr(y[i] == 0)
        else:
            m.addConstr(y[i] <= gp.quicksum(x[j] for j in covering), name=f"cover_{i}")

    pop_weights = population['pop'].values.astype(float)
    m.setObjective(gp.quicksum(pop_weights[i] * y[i] for i in range(n_pop)), GRB.MAXIMIZE)

    start = time.time()
    m.optimize()
    solve_time = time.time() - start

    # Extract solution
    selected_indices = [j for j in range(n_cand) if x[j].X > 0.5]
    try:
        selected_ids = [int(candidates.iloc[j]['id']) for j in selected_indices]
    except Exception:
        selected_ids = [candidates.iloc[j]['id'] for j in selected_indices]

    total_covered = float(sum(pop_weights[i] for i in range(n_pop) if y[i].X > 0.5))

    return selected_ids, total_covered, m
