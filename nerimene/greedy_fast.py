# src/greedy_fast.py
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from typing import List, Tuple

def greedy_max_k_cover_fast(candidates: pd.DataFrame, population: pd.DataFrame,
                            k: int, radius: float) -> Tuple[List[int], float, np.ndarray]:
    """
    Fast greedy using KDTree. radius in same units as x,y.
    Returns: (selected_ids, total_covered_pop, covered_mask)
    - selected_ids : list of candidate ids (values from column 'id')
    - total_covered_pop : sum of population weights covered
    - covered_mask : boolean array length n_pop showing which population points are covered
    """
    # defensive copy / reset index
    candidates = candidates.reset_index(drop=True).copy()
    population = population.reset_index(drop=True).copy()

    # ensure numeric coords
    for col in ('x','y'):
        if col not in candidates.columns or col not in population.columns:
            raise ValueError(f"Both candidates and population must contain column '{col}'")
        candidates[col] = pd.to_numeric(candidates[col], errors='coerce')
        population[col] = pd.to_numeric(population[col], errors='coerce')

    # population weights default to 1
    if 'pop' not in population.columns:
        population['pop'] = 1.0
    population['pop'] = pd.to_numeric(population['pop'], errors='coerce').fillna(0.0)

    n_cand = len(candidates)
    n_pop = len(population)
    if n_cand == 0 or n_pop == 0 or k <= 0:
        return [], 0.0, np.zeros(n_pop, dtype=bool)

    pop_coords = np.column_stack((population['x'].values, population['y'].values))
    cand_coords = np.column_stack((candidates['x'].values, candidates['y'].values))
    pop_weights = population['pop'].values.astype(float)

    tree = cKDTree(pop_coords)
    # list of arrays of pop-indices that each candidate covers
    coverage_lists = [np.array(tree.query_ball_point(pt, r=radius), dtype=int) for pt in cand_coords]

    covered = np.zeros(n_pop, dtype=bool)
    selected_indices = []
    selected_ids = []

    for _ in range(min(k, n_cand)):
        best_ci = -1
        best_gain = 0.0
        for ci, cov in enumerate(coverage_lists):
            if ci in selected_indices:
                continue
            if cov.size == 0:
                continue
            # which indices of population are not yet covered
            uncov = cov[~covered[cov]]
            if uncov.size == 0:
                continue
            gain = pop_weights[uncov].sum()
            if gain > best_gain:
                best_gain = gain
                best_ci = ci
        if best_ci == -1:
            break
        selected_indices.append(best_ci)
        # candidate id from column 'id' (cast to int if possible)
        try:
            selected_ids.append(int(candidates.iloc[best_ci]['id']))
        except Exception:
            selected_ids.append(candidates.iloc[best_ci]['id'])
        # mark newly covered population points
        covered[coverage_lists[best_ci]] = True

    total_covered = float(pop_weights[covered].sum())
    return selected_ids, total_covered, covered
