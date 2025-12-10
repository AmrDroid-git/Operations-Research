import unittest
import numpy as np
from puzzle_state import PuzzleState


class TestPuzzleState(unittest.TestCase):
    
    def test_goal_state_creation(self):
        puzzle = PuzzleState(3)
        self.assertTrue(puzzle.is_goal())
    
    def test_goal_state_4x4(self):
        puzzle = PuzzleState(4)
        self.assertTrue(puzzle.is_goal())
    
    def test_valid_moves_corner(self):
        puzzle = PuzzleState(3)
        moves = puzzle.get_valid_moves()
        self.assertEqual(len(moves), 2)
        self.assertIn((2, 1), moves)
        self.assertIn((1, 2), moves)
    
    def test_valid_moves_center(self):
        board = np.array([[1, 2, 3], [4, 0, 5], [6, 7, 8]])
        puzzle = PuzzleState(3, board)
        moves = puzzle.get_valid_moves()
        self.assertEqual(len(moves), 4)
    
    def test_apply_move(self):
        puzzle = PuzzleState(3)
        initial_empty = puzzle.empty_pos
        moves = puzzle.get_valid_moves()
        new_puzzle = puzzle.apply_move(moves[0])
        self.assertNotEqual(initial_empty, new_puzzle.empty_pos)
    
    def test_is_valid_move(self):
        puzzle = PuzzleState(3)
        self.assertTrue(puzzle.is_valid_move((2, 1)))
        self.assertFalse(puzzle.is_valid_move((0, 0)))
    
    def test_get_tile_at(self):
        puzzle = PuzzleState(3)
        self.assertEqual(puzzle.get_tile_at((0, 0)), 1)
        self.assertEqual(puzzle.get_tile_at((2, 2)), 0)
    
    def test_get_position_of_tile(self):
        puzzle = PuzzleState(3)
        pos = puzzle.get_position_of_tile(1)
        self.assertEqual(pos, (0, 0))
        pos = puzzle.get_position_of_tile(0)
        self.assertEqual(pos, (2, 2))
    
    def test_solvable_goal_state(self):
        puzzle = PuzzleState(3)
        self.assertTrue(puzzle.is_solvable())
    
    def test_solvable_shuffled(self):
        puzzle = PuzzleState(3)
        puzzle.shuffle(20)
        self.assertTrue(puzzle.is_solvable())
    
    def test_unsolvable_3x3(self):
        board = np.array([[1, 2, 3], [4, 5, 6], [8, 7, 0]])
        puzzle = PuzzleState(3, board)
        self.assertFalse(puzzle.is_solvable())
    
    def test_copy(self):
        puzzle = PuzzleState(3)
        puzzle_copy = puzzle.copy()
        self.assertEqual(puzzle, puzzle_copy)
        self.assertIsNot(puzzle, puzzle_copy)
    
    def test_hash_equality(self):
        puzzle1 = PuzzleState(3)
        puzzle2 = PuzzleState(3)
        self.assertEqual(hash(puzzle1), hash(puzzle2))
    
    def test_simple_solve_sequence(self):
        board = np.array([[1, 2, 3], [4, 5, 6], [7, 0, 8]])
        puzzle = PuzzleState(3, board)
        
        puzzle = puzzle.apply_move((2, 2))
        
        self.assertTrue(puzzle.is_goal())


if __name__ == '__main__':
    unittest.main()
