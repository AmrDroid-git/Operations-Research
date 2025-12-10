from typing import List, Tuple, Optional
import numpy as np


class PuzzleState:
    def __init__(self, size: int = 3, board: Optional[np.ndarray] = None):
        self.size = size
        if board is None:
            self.board = self._create_goal_state()
        else:
            self.board = board.copy()
        self.empty_pos = self._find_empty()
    
    def _create_goal_state(self) -> np.ndarray:
        board = np.arange(1, self.size * self.size + 1).reshape(self.size, self.size)
        board[-1, -1] = 0
        return board
    
    def _find_empty(self) -> Tuple[int, int]:
        pos = np.where(self.board == 0)
        return (int(pos[0][0]), int(pos[1][0]))
    
    def is_goal(self) -> bool:
        goal = self._create_goal_state()
        return np.array_equal(self.board, goal)
    
    def get_valid_moves(self) -> List[Tuple[int, int]]:
        moves = []
        row, col = self.empty_pos
        
        if row > 0:
            moves.append((row - 1, col))
        if row < self.size - 1:
            moves.append((row + 1, col))
        if col > 0:
            moves.append((row, col - 1))
        if col < self.size - 1:
            moves.append((row, col + 1))
        
        return moves
    
    def apply_move(self, tile_pos: Tuple[int, int]) -> 'PuzzleState':
        new_board = self.board.copy()
        empty_row, empty_col = self.empty_pos
        tile_row, tile_col = tile_pos
        
        new_board[empty_row, empty_col] = new_board[tile_row, tile_col]
        new_board[tile_row, tile_col] = 0
        
        return PuzzleState(self.size, new_board)
    
    def is_valid_move(self, tile_pos: Tuple[int, int]) -> bool:
        return tile_pos in self.get_valid_moves()
    
    def get_tile_at(self, pos: Tuple[int, int]) -> int:
        return int(self.board[pos[0], pos[1]])
    
    def get_position_of_tile(self, tile: int) -> Tuple[int, int]:
        pos = np.where(self.board == tile)
        if len(pos[0]) == 0:
            return (-1, -1)
        return (int(pos[0][0]), int(pos[1][0]))
    
    def shuffle(self, num_moves: int = 100) -> None:
        import random
        for _ in range(num_moves):
            valid_moves = self.get_valid_moves()
            move = random.choice(valid_moves)
            new_state = self.apply_move(move)
            self.board = new_state.board
            self.empty_pos = new_state.empty_pos
    
    def is_solvable(self) -> bool:
        flat = self.board.flatten()
        inversions = 0
        
        for i in range(len(flat)):
            if flat[i] == 0:
                continue
            for j in range(i + 1, len(flat)):
                if flat[j] == 0:
                    continue
                if flat[i] > flat[j]:
                    inversions += 1
        
        if self.size % 2 == 1:
            return inversions % 2 == 0
        else:
            empty_row_from_bottom = self.size - self.empty_pos[0]
            if empty_row_from_bottom % 2 == 1:
                return inversions % 2 == 0
            else:
                return inversions % 2 == 1
    
    def __hash__(self) -> int:
        return hash(self.board.tobytes())
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, PuzzleState):
            return False
        return np.array_equal(self.board, other.board)
    
    def __str__(self) -> str:
        result = []
        for row in self.board:
            result.append(" ".join(f"{val:2d}" if val != 0 else " ." for val in row))
        return "\n".join(result)
    
    def copy(self) -> 'PuzzleState':
        return PuzzleState(self.size, self.board)
