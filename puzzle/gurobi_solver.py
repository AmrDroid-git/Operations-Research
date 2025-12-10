from typing import List, Tuple, Optional
import gurobipy as gp
from gurobipy import GRB, GurobiError
import numpy as np
from .puzzle_state import PuzzleState


class SolverMode:
    PLNE = "PLNE"
    PLM = "PLM"


class GurobiSolver:
    def __init__(self, initial_state: PuzzleState, mode: str = SolverMode.PLNE, 
                 max_steps: int = 12, time_limit: int = 300):
        self.initial_state = initial_state
        self.mode = mode
        self.max_steps = max_steps
        self.time_limit = time_limit
        self.size = initial_state.size
        self.n_tiles = self.size * self.size
        self.solution = None
        self.solve_time = 0
        self.model = None
        self.last_error = None
    
    def solve(self) -> Optional[List[Tuple[int, int]]]:
        if not self.initial_state.is_solvable():
            return None
        
        if self.initial_state.is_goal():
            return []
        
        for horizon in range(1, self.max_steps + 1):
            try:
                print(f"Trying horizon {horizon}...")
                solution = self._solve_with_horizon(horizon)
                if solution is not None:
                    self.solution = solution
                    print(f"Solution found at horizon {horizon}")
                    return solution
                print(f"No solution at horizon {horizon}, trying next...")
            except GurobiError as e:
                print(f"Gurobi error at horizon {horizon}: {e}")
                self.last_error = str(e)
                if "too large" in str(e).lower() or "size-limited" in str(e).lower():
                    print("Model too large for license, stopping search")
                    return None
                continue
            except Exception as e:
                print(f"Unexpected error at horizon {horizon}: {e}")
                self.last_error = str(e)
                continue
        
        print("Reached max horizon without finding solution")
        return None
    
    def _solve_with_horizon(self, horizon: int) -> Optional[List[Tuple[int, int]]]:
        model = gp.Model("sliding_puzzle")
        model.setParam('OutputFlag', 0)
        model.setParam('TimeLimit', self.time_limit)
        
        self.model = model
        
        print(f"Solving with {self.mode} mode, horizon={horizon}")
        
        if self.mode == SolverMode.PLNE:
            return self._solve_plne(model, horizon)
        else:
            return self._solve_plm(model, horizon)
    
    def _solve_plne(self, model: gp.Model, horizon: int) -> Optional[List[Tuple[int, int]]]:
        x = {}
        for t in range(horizon + 1):
            for tile in range(self.n_tiles):
                for pos in range(self.n_tiles):
                    x[tile, pos, t] = model.addVar(vtype=GRB.BINARY, 
                                                    name=f"x_{tile}_{pos}_{t}")
        
        m = {}
        for t in range(horizon):
            for tile in range(self.n_tiles):
                for pos in range(self.n_tiles):
                    m[tile, pos, t] = model.addVar(vtype=GRB.BINARY, 
                                                    name=f"m_{tile}_{pos}_{t}")
        
        for tile in range(self.n_tiles):
            for t in range(horizon + 1):
                model.addConstr(gp.quicksum(x[tile, pos, t] for pos in range(self.n_tiles)) == 1,
                               name=f"one_pos_tile_{tile}_t_{t}")
        
        for pos in range(self.n_tiles):
            for t in range(horizon + 1):
                model.addConstr(gp.quicksum(x[tile, pos, t] for tile in range(self.n_tiles)) == 1,
                               name=f"one_tile_pos_{pos}_t_{t}")
        
        for tile in range(self.n_tiles):
            init_pos = self._get_initial_position(tile)
            model.addConstr(x[tile, init_pos, 0] == 1, name=f"init_{tile}")
        
        goal_board = self.initial_state._create_goal_state()
        for tile in range(self.n_tiles):
            goal_pos = self._get_goal_position(tile, goal_board)
            model.addConstr(x[tile, goal_pos, horizon] == 1, name=f"goal_{tile}")
        
        for t in range(horizon):
            for tile in range(self.n_tiles):
                for pos in range(self.n_tiles):
                    model.addConstr(m[tile, pos, t] <= x[tile, pos, t],
                                   name=f"move_from_{tile}_{pos}_{t}")
        
        for t in range(horizon):
            model.addConstr(gp.quicksum(m[tile, pos, t] 
                                       for tile in range(self.n_tiles) 
                                       for pos in range(self.n_tiles)) == 1,
                           name=f"one_move_{t}")
        
        for t in range(horizon):
            for tile in range(self.n_tiles):
                if tile == 0:
                    continue
                for pos in range(self.n_tiles):
                    neighbors = self._get_neighbors(pos)
                    model.addConstr(
                        x[tile, pos, t + 1] <= x[tile, pos, t] + 
                        gp.quicksum(m[tile, n, t] for n in neighbors if n != pos),
                        name=f"valid_move_{tile}_{pos}_{t}"
                    )
        
        for t in range(horizon):
            for tile in range(self.n_tiles):
                if tile == 0:
                    continue
                for pos in range(self.n_tiles):
                    neighbors = self._get_neighbors(pos)
                    model.addConstr(
                        x[tile, pos, t] - x[tile, pos, t + 1] <= 
                        x[0, pos, t] + gp.quicksum(m[tile, pos, t] for _ in [1]),
                        name=f"empty_adjacent_{tile}_{pos}_{t}"
                    )
        
        model.setObjective(gp.quicksum(m[tile, pos, t] 
                                       for t in range(horizon) 
                                       for tile in range(self.n_tiles) 
                                       for pos in range(self.n_tiles)), 
                          GRB.MINIMIZE)
        
        model.optimize()
        
        if model.status == GRB.OPTIMAL:
            return self._extract_solution(x, m, horizon)
        
        return None
    
    def _solve_plm(self, model: gp.Model, horizon: int) -> Optional[List[Tuple[int, int]]]:
        x = {}
        for t in range(horizon + 1):
            for tile in range(self.n_tiles):
                for pos in range(self.n_tiles):
                    x[tile, pos, t] = model.addVar(vtype=GRB.BINARY, 
                                                    name=f"x_{tile}_{pos}_{t}")
        
        m = {}
        for t in range(horizon):
            for tile in range(self.n_tiles):
                for pos in range(self.n_tiles):
                    m[tile, pos, t] = model.addVar(vtype=GRB.BINARY, 
                                                    name=f"m_{tile}_{pos}_{t}")
        
        dist = {}
        for t in range(horizon + 1):
            for tile in range(self.n_tiles):
                dist[tile, t] = model.addVar(vtype=GRB.CONTINUOUS, lb=0, 
                                             name=f"dist_{tile}_{t}")
        
        for tile in range(self.n_tiles):
            for t in range(horizon + 1):
                model.addConstr(gp.quicksum(x[tile, pos, t] for pos in range(self.n_tiles)) == 1,
                               name=f"one_pos_tile_{tile}_t_{t}")
        
        for pos in range(self.n_tiles):
            for t in range(horizon + 1):
                model.addConstr(gp.quicksum(x[tile, pos, t] for tile in range(self.n_tiles)) == 1,
                               name=f"one_tile_pos_{pos}_t_{t}")
        
        for tile in range(self.n_tiles):
            init_pos = self._get_initial_position(tile)
            model.addConstr(x[tile, init_pos, 0] == 1, name=f"init_{tile}")
        
        goal_board = self.initial_state._create_goal_state()
        for tile in range(self.n_tiles):
            goal_pos = self._get_goal_position(tile, goal_board)
            model.addConstr(x[tile, goal_pos, horizon] == 1, name=f"goal_{tile}")
        
        for t in range(horizon):
            for tile in range(self.n_tiles):
                for pos in range(self.n_tiles):
                    model.addConstr(m[tile, pos, t] <= x[tile, pos, t],
                                   name=f"move_from_{tile}_{pos}_{t}")
        
        for t in range(horizon):
            model.addConstr(gp.quicksum(m[tile, pos, t] 
                                       for tile in range(self.n_tiles) 
                                       for pos in range(self.n_tiles)) == 1,
                           name=f"one_move_{t}")
        
        for t in range(horizon):
            for tile in range(self.n_tiles):
                if tile == 0:
                    continue
                for pos in range(self.n_tiles):
                    neighbors = self._get_neighbors(pos)
                    model.addConstr(
                        x[tile, pos, t + 1] <= x[tile, pos, t] + 
                        gp.quicksum(m[tile, n, t] for n in neighbors if n != pos),
                        name=f"valid_move_{tile}_{pos}_{t}"
                    )
        
        for t in range(horizon + 1):
            for tile in range(1, self.n_tiles):
                goal_pos = self._get_goal_position(tile, goal_board)
                goal_row, goal_col = goal_pos // self.size, goal_pos % self.size
                
                model.addConstr(
                    dist[tile, t] >= gp.quicksum(
                        (abs((pos // self.size) - goal_row) + abs((pos % self.size) - goal_col)) * 
                        x[tile, pos, t] for pos in range(self.n_tiles)
                    ),
                    name=f"manhattan_{tile}_{t}"
                )
        
        model.setObjective(
            gp.quicksum(m[tile, pos, t] 
                       for t in range(horizon) 
                       for tile in range(self.n_tiles) 
                       for pos in range(self.n_tiles)) +
            0.01 * gp.quicksum(dist[tile, horizon] for tile in range(1, self.n_tiles)),
            GRB.MINIMIZE
        )
        
        model.optimize()
        
        if model.status == GRB.OPTIMAL:
            return self._extract_solution(x, m, horizon)
        
        return None
    
    def _get_initial_position(self, tile: int) -> int:
        pos = self.initial_state.get_position_of_tile(tile)
        return pos[0] * self.size + pos[1]
    
    def _get_goal_position(self, tile: int, goal_board: np.ndarray) -> int:
        pos = np.where(goal_board == tile)
        if len(pos[0]) == 0:
            return -1
        return int(pos[0][0] * self.size + pos[1][0])
    
    def _get_neighbors(self, pos: int) -> List[int]:
        row, col = pos // self.size, pos % self.size
        neighbors = []
        
        if row > 0:
            neighbors.append((row - 1) * self.size + col)
        if row < self.size - 1:
            neighbors.append((row + 1) * self.size + col)
        if col > 0:
            neighbors.append(row * self.size + (col - 1))
        if col < self.size - 1:
            neighbors.append(row * self.size + (col + 1))
        
        return neighbors
    
    def _extract_solution(self, x, m, horizon: int) -> List[Tuple[int, int]]:
        moves = []
        
        for t in range(horizon):
            for tile in range(self.n_tiles):
                for pos in range(self.n_tiles):
                    if m[tile, pos, t].X > 0.5:
                        row, col = pos // self.size, pos % self.size
                        moves.append((row, col))
                        break
        
        return moves
    
    def get_statistics(self) -> dict:
        if self.model is None:
            return {'last_error': self.last_error} if self.last_error else {}
        
        stats = {
            'mode': self.mode,
            'solve_time': self.model.Runtime,
            'num_moves': len(self.solution) if self.solution else 0,
            'num_variables': self.model.NumVars,
            'num_constraints': self.model.NumConstrs,
            'objective_value': self.model.ObjVal if self.model.status == GRB.OPTIMAL else None
        }
        
        if self.last_error:
            stats['last_error'] = self.last_error
        
        return stats
