from puzzle_state import PuzzleState
from gurobi_solver import GurobiSolver, SolverMode
import numpy as np


def test_3x3_plne():
    print("\n=== Testing 3x3 Puzzle with PLNE ===")
    board = np.array([[1, 2, 3], [4, 0, 5], [6, 7, 8]])
    puzzle = PuzzleState(3, board)
    
    print("Initial state:")
    print(puzzle)
    print(f"Solvable: {puzzle.is_solvable()}")
    
    solver = GurobiSolver(puzzle, mode=SolverMode.PLNE, max_steps=15)
    solution = solver.solve()
    
    if solution:
        print(f"\nSolution found with {len(solution)} moves")
        stats = solver.get_statistics()
        print(f"Solve time: {stats['solve_time']:.2f} seconds")
        print(f"Variables: {stats['num_variables']}")
        print(f"Constraints: {stats['num_constraints']}")
        
        test_puzzle = puzzle.copy()
        for i, move in enumerate(solution):
            test_puzzle = test_puzzle.apply_move(move)
            print(f"\nMove {i+1}: {move}")
            print(test_puzzle)
        
        print(f"\nGoal reached: {test_puzzle.is_goal()}")
    else:
        print("No solution found")


def test_3x3_plm():
    print("\n=== Testing 3x3 Puzzle with PLM ===")
    board = np.array([[1, 2, 3], [4, 0, 5], [6, 7, 8]])
    puzzle = PuzzleState(3, board)
    
    print("Initial state:")
    print(puzzle)
    
    solver = GurobiSolver(puzzle, mode=SolverMode.PLM, max_steps=15)
    solution = solver.solve()
    
    if solution:
        print(f"\nSolution found with {len(solution)} moves")
        stats = solver.get_statistics()
        print(f"Solve time: {stats['solve_time']:.2f} seconds")
        print(f"Variables: {stats['num_variables']}")
        print(f"Constraints: {stats['num_constraints']}")
        
        test_puzzle = puzzle.copy()
        for move in solution:
            test_puzzle = test_puzzle.apply_move(move)
        
        print(f"Goal reached: {test_puzzle.is_goal()}")
    else:
        print("No solution found")


def test_shuffled_3x3():
    print("\n=== Testing Shuffled 3x3 Puzzle ===")
    puzzle = PuzzleState(3)
    puzzle.shuffle(15)
    
    print("Shuffled state:")
    print(puzzle)
    print(f"Solvable: {puzzle.is_solvable()}")
    
    if puzzle.is_solvable() and not puzzle.is_goal():
        solver = GurobiSolver(puzzle, mode=SolverMode.PLM, max_steps=20)
        solution = solver.solve()
        
        if solution:
            print(f"\nSolution found with {len(solution)} moves")
            stats = solver.get_statistics()
            print(f"Solve time: {stats['solve_time']:.2f} seconds")
            
            test_puzzle = puzzle.copy()
            for move in solution:
                test_puzzle = test_puzzle.apply_move(move)
            
            print(f"Goal reached: {test_puzzle.is_goal()}")
        else:
            print("No solution found within time limit")


if __name__ == "__main__":
    try:
        test_3x3_plne()
    except Exception as e:
        print(f"PLNE test failed: {e}")
    
    try:
        test_3x3_plm()
    except Exception as e:
        print(f"PLM test failed: {e}")
    
    try:
        test_shuffled_3x3()
    except Exception as e:
        print(f"Shuffled test failed: {e}")
