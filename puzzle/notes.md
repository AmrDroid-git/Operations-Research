# Sliding Blocks Puzzle Solver - Technical Notes

## Problem Description

The sliding blocks puzzle consists of numbered tiles on an N×N grid with one empty space. Tiles adjacent to the empty space can slide into it. The goal is to arrange tiles in ascending order with the empty space in the bottom-right corner.

**Solvability**: A configuration is solvable if and only if:
- For N odd: number of inversions is even
- For N even: (inversions + empty row from bottom) is odd

## PLNE Model (Programme Linéaire en Nombres Entiers)

Pure integer linear programming formulation.

### Decision Variables

- `x[i,j,t] ∈ {0,1}`: tile i is at position j at time t
- `m[i,j,t] ∈ {0,1}`: tile i moves from position j at time t

where i,j ∈ {0,...,N²-1} and t ∈ {0,...,T}

### Constraints

**Position Uniqueness**:
```
∑(j) x[i,j,t] = 1    ∀i,t    (each tile at exactly one position)
∑(i) x[i,j,t] = 1    ∀j,t    (each position has exactly one tile)
```

**Initial and Goal States**:
```
x[i, pos_init(i), 0] = 1    ∀i
x[i, pos_goal(i), T] = 1    ∀i
```

**Move Constraints**:
```
m[i,j,t] ≤ x[i,j,t]                                           ∀i,j,t
∑(i,j) m[i,j,t] = 1                                          ∀t
x[i,j,t+1] ≤ x[i,j,t] + ∑(k∈neighbors(j)) m[i,k,t]          ∀i≠0,j,t
x[i,j,t] - x[i,j,t+1] ≤ x[0,j,t] + m[i,j,t]                 ∀i≠0,j,t
```

### Objective

```
minimize: ∑(t,i,j) m[i,j,t]
```

## PLM Model (Programme Linéaire Mixte)

Mixed integer-continuous formulation for improved performance.

### Additional Variables

- `dist[i,t] ∈ ℝ⁺`: Manhattan distance of tile i from goal at time t

### Additional Constraints

**Manhattan Distance**:
```
dist[i,t] ≥ ∑(j) (|row(j) - row_goal(i)| + |col(j) - col_goal(i)|) × x[i,j,t]    ∀i≠0,t
```

### Objective

```
minimize: ∑(t,i,j) m[i,j,t] + 0.01 × ∑(i) dist[i,T]
```

The distance penalty guides LP relaxation toward better solutions.

## Model Comparison

| Aspect | PLNE | PLM |
|--------|------|-----|
| Variables | All binary | Binary + continuous |
| Performance (3×3) | 0.2-1.0s | 0.1-0.8s |
| Performance (4×4) | 5-60s | 2-30s |

>I was unable to get the 4x4 puzzle to work since the constraint count is higher than what my license allows.

## Implementation Architecture

### Core Classes

**PuzzleState**: Board representation, move generation, solvability checking

**GurobiSolver**: Optimization solver with mode selection (PLNE/PLM)
- Iterative deepening: starts with T=1, increments until solution found (max T=12)
- Guarantees optimal solution within horizon limit
- Note: Size-limited licenses may hit limits at T≈9-12 depending on puzzle complexity

**PuzzleWidget**: PyQt6 visualization with animations

**MainWindow**: UI with solver mode selector, controls, statistics display

## Usage

```bash
pip install -r requirements.txt
python main.py
```

Select puzzle size (3×3 or 4×4), choose solver mode (PLNE or PLM), shuffle, and solve.

## Testing

```bash
python -m pytest test_puzzle_state.py -v
python -m pytest test_gurobi_solver.py -v
python verify_solver.py
```

