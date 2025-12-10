from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, pyqtSignal, QRect, QTimer
from PyQt6.QtGui import QPainter, QColor, QFont, QPen
from .puzzle_state import PuzzleState
from typing import Optional, List, Tuple


class PuzzleWidget(QWidget):
    tile_clicked = pyqtSignal(int, int)
    
    def __init__(self, size: int = 3, parent=None):
        super().__init__(parent)
        self.size = size
        self.puzzle_state: Optional[PuzzleState] = None
        self.tile_size = 80
        self.margin = 10
        self.animating = False
        self.animation_progress = 0
        self.animation_from = None
        self.animation_to = None
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self._update_animation)
        
        self.setMinimumSize(
            self.size * self.tile_size + 2 * self.margin,
            self.size * self.tile_size + 2 * self.margin
        )
    
    def set_puzzle_state(self, state: PuzzleState):
        self.puzzle_state = state
        self.size = state.size
        self.setMinimumSize(
            self.size * self.tile_size + 2 * self.margin,
            self.size * self.tile_size + 2 * self.margin
        )
        self.update()
    
    def animate_move(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int]):
        self.animation_from = from_pos
        self.animation_to = to_pos
        self.animation_progress = 0
        self.animating = True
        self.animation_timer.start(16)
    
    def _update_animation(self):
        self.animation_progress += 0.1
        if self.animation_progress >= 1.0:
            self.animation_progress = 1.0
            self.animating = False
            self.animation_timer.stop()
        self.update()
    
    def paintEvent(self, event):
        if self.puzzle_state is None:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        for row in range(self.size):
            for col in range(self.size):
                tile = self.puzzle_state.get_tile_at((row, col))
                
                if tile == 0:
                    continue
                
                x = self.margin + col * self.tile_size
                y = self.margin + row * self.tile_size
                
                if self.animating and (row, col) == self.animation_from:
                    from_row, from_col = self.animation_from
                    to_row, to_col = self.animation_to
                    x = self.margin + (from_col + (to_col - from_col) * self.animation_progress) * self.tile_size
                    y = self.margin + (from_row + (to_row - from_row) * self.animation_progress) * self.tile_size
                
                self._draw_tile(painter, x, y, tile, (row, col))
        
        self._draw_grid(painter)
    
    def _draw_tile(self, painter: QPainter, x: float, y: float, tile: int, pos: Tuple[int, int]):
        rect = QRect(int(x) + 2, int(y) + 2, self.tile_size - 4, self.tile_size - 4)
        
        is_valid_move = pos in self.puzzle_state.get_valid_moves() if self.puzzle_state else False
        
        if is_valid_move:
            painter.setBrush(QColor(100, 150, 255))
        else:
            painter.setBrush(QColor(70, 130, 180))
        
        painter.setPen(QPen(QColor(30, 60, 100), 2))
        painter.drawRoundedRect(rect, 8, 8)
        
        painter.setPen(QColor(255, 255, 255))
        font = QFont("Arial", 24, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, str(tile))
    
    def _draw_grid(self, painter: QPainter):
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        
        for i in range(self.size + 1):
            x = self.margin + i * self.tile_size
            y = self.margin + i * self.tile_size
            painter.drawLine(
                self.margin, y,
                self.margin + self.size * self.tile_size, y
            )
            painter.drawLine(
                x, self.margin,
                x, self.margin + self.size * self.tile_size
            )
    
    def mousePressEvent(self, event):
        if self.puzzle_state is None or self.animating:
            return
        
        x = event.pos().x() - self.margin
        y = event.pos().y() - self.margin
        
        if x < 0 or y < 0:
            return
        
        col = x // self.tile_size
        row = y // self.tile_size
        
        if row >= self.size or col >= self.size:
            return
        
        if self.puzzle_state.is_valid_move((row, col)):
            self.tile_clicked.emit(row, col)
