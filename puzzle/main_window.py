from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QRadioButton, QButtonGroup,
                             QTextEdit, QStatusBar, QMenuBar, QMenu, QMessageBox)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QAction, QFont
from .puzzle_widget import PuzzleWidget
from .puzzle_state import PuzzleState
from .gurobi_solver import GurobiSolver, SolverMode
from typing import Optional, List, Tuple
import threading


class SolverSignals(QObject):
    finished = pyqtSignal(object, object)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.puzzle_state: Optional[PuzzleState] = None
        self.solver: Optional[GurobiSolver] = None
        self.solution_moves: Optional[List[Tuple[int, int]]] = None
        self.current_move_index = 0
        self.solver_mode = SolverMode.PLNE
        self.puzzle_size = 3
        
        self.solver_signals = SolverSignals()
        self.solver_signals.finished.connect(self.on_solve_complete)
        
        self.init_ui()
        self.new_puzzle()
    
    def init_ui(self):
        self.setWindowTitle("Sliding Blocks Puzzle Solver")
        self.setGeometry(100, 100, 900, 700)
        
        self._create_menu_bar()
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        
        left_panel = self._create_left_panel()
        right_panel = self._create_right_panel()
        
        main_layout.addLayout(left_panel, 2)
        main_layout.addLayout(right_panel, 1)
        
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.update_status("Ready")
    
    def _create_menu_bar(self):
        menubar = self.menuBar()
        
        puzzle_menu = menubar.addMenu("Puzzle")
        
        size_3x3_action = QAction("3x3 Puzzle", self)
        size_3x3_action.triggered.connect(lambda: self.change_puzzle_size(3))
        puzzle_menu.addAction(size_3x3_action)
        
        size_4x4_action = QAction("4x4 Puzzle", self)
        size_4x4_action.triggered.connect(lambda: self.change_puzzle_size(4))
        puzzle_menu.addAction(size_4x4_action)
        
        puzzle_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        puzzle_menu.addAction(exit_action)
    
    def _create_left_panel(self) -> QVBoxLayout:
        layout = QVBoxLayout()
        
        title = QLabel(f"Sliding Blocks Puzzle ({self.puzzle_size}x{self.puzzle_size})")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        self.title_label = title
        
        self.puzzle_widget = PuzzleWidget(self.puzzle_size)
        self.puzzle_widget.tile_clicked.connect(self.on_tile_clicked)
        layout.addWidget(self.puzzle_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addStretch()
        
        return layout
    
    def _create_right_panel(self) -> QVBoxLayout:
        layout = QVBoxLayout()
        
        size_label = QLabel("Puzzle Size:")
        size_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(size_label)
        
        self.size_group = QButtonGroup()
        
        size_3x3_radio = QRadioButton("3×3 (8-puzzle)")
        size_3x3_radio.setChecked(True)
        size_3x3_radio.toggled.connect(lambda: self.change_puzzle_size(3))
        self.size_group.addButton(size_3x3_radio)
        layout.addWidget(size_3x3_radio)
        
        size_4x4_radio = QRadioButton("4×4 (15-puzzle)")
        size_4x4_radio.toggled.connect(lambda: self.change_puzzle_size(4))
        self.size_group.addButton(size_4x4_radio)
        layout.addWidget(size_4x4_radio)
        
        layout.addSpacing(20)
        
        solver_label = QLabel("Solver Mode:")
        solver_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(solver_label)
        
        self.solver_group = QButtonGroup()
        
        plne_radio = QRadioButton("PLNE (Integer Linear Programming)")
        plne_radio.setChecked(True)
        plne_radio.toggled.connect(lambda: self.set_solver_mode(SolverMode.PLNE))
        self.solver_group.addButton(plne_radio)
        layout.addWidget(plne_radio)
        
        plm_radio = QRadioButton("PLM (Mixed Linear Programming)")
        plm_radio.toggled.connect(lambda: self.set_solver_mode(SolverMode.PLM))
        self.solver_group.addButton(plm_radio)
        layout.addWidget(plm_radio)
        
        layout.addSpacing(20)
        
        controls_label = QLabel("Controls:")
        controls_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(controls_label)
        
        self.shuffle_btn = QPushButton("Shuffle Puzzle")
        self.shuffle_btn.clicked.connect(self.shuffle_puzzle)
        layout.addWidget(self.shuffle_btn)
        
        self.solve_btn = QPushButton("Solve Puzzle")
        self.solve_btn.clicked.connect(self.solve_puzzle)
        layout.addWidget(self.solve_btn)
        
        self.play_btn = QPushButton("Play Solution")
        self.play_btn.clicked.connect(self.play_solution)
        self.play_btn.setEnabled(False)
        layout.addWidget(self.play_btn)
        
        self.step_btn = QPushButton("Step Forward")
        self.step_btn.clicked.connect(self.step_solution)
        self.step_btn.setEnabled(False)
        layout.addWidget(self.step_btn)
        
        self.reset_btn = QPushButton("Reset Puzzle")
        self.reset_btn.clicked.connect(self.new_puzzle)
        layout.addWidget(self.reset_btn)
        
        layout.addSpacing(20)
        
        solution_label = QLabel("Solution & Statistics:")
        solution_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(solution_label)
        
        self.solution_text = QTextEdit()
        self.solution_text.setReadOnly(True)
        self.solution_text.setMaximumHeight(200)
        layout.addWidget(self.solution_text)
        
        layout.addStretch()
        
        return layout
    
    def set_solver_mode(self, mode: str):
        self.solver_mode = mode
        self.update_status(f"Solver mode: {mode}")
    
    def change_puzzle_size(self, size: int):
        self.puzzle_size = size
        self.new_puzzle()
        self.title_label.setText(f"Sliding Blocks Puzzle ({size}x{size})")
        self.puzzle_widget.size = size
        self.puzzle_widget.set_puzzle_state(self.puzzle_state)
    
    def new_puzzle(self):
        self.puzzle_state = PuzzleState(self.puzzle_size)
        self.puzzle_widget.set_puzzle_state(self.puzzle_state)
        self.solution_moves = None
        self.current_move_index = 0
        self.play_btn.setEnabled(False)
        self.step_btn.setEnabled(False)
        self.solution_text.clear()
        self.update_status("New puzzle created")
    
    def shuffle_puzzle(self):
        if self.puzzle_state:
            num_moves = 6 if self.puzzle_size == 4 else 8
            self.puzzle_state.shuffle(num_moves)
            self.puzzle_widget.set_puzzle_state(self.puzzle_state)
            self.solution_moves = None
            self.current_move_index = 0
            self.play_btn.setEnabled(False)
            self.step_btn.setEnabled(False)
            self.solution_text.clear()
            self.update_status(f"Puzzle shuffled ({num_moves} moves)")
    
    def solve_puzzle(self):
        if not self.puzzle_state:
            return
        
        if self.puzzle_state.is_goal():
            QMessageBox.information(self, "Already Solved", "The puzzle is already in the goal state!")
            return
        
        if not self.puzzle_state.is_solvable():
            QMessageBox.warning(self, "Unsolvable", "This puzzle configuration is not solvable!")
            return
        
        self.update_status(f"Solving with {self.solver_mode}...")
        self.solve_btn.setEnabled(False)
        self.shuffle_btn.setEnabled(False)
        
        def solve_thread():
            solver = GurobiSolver(self.puzzle_state, mode=self.solver_mode, max_steps=12)
            solution = solver.solve()
            stats = solver.get_statistics()
            
            print(f"Solver finished. Solution: {solution}")
            print(f"Stats: {stats}")
            
            self.solver_signals.finished.emit(solution, stats)
        
        thread = threading.Thread(target=solve_thread)
        thread.start()
    
    def on_solve_complete(self, solution: Optional[List[Tuple[int, int]]], stats: dict):
        print(f"on_solve_complete called with solution: {solution}")
        self.solve_btn.setEnabled(True)
        self.shuffle_btn.setEnabled(True)
        
        if solution is None:
            error_msg = stats.get('last_error', '')
            
            if "too large" in error_msg.lower() or "size-limited" in error_msg.lower():
                msg = f"Gurobi License Error: {error_msg}\n\nThe puzzle is too complex for your size-limited license. Resetting to a simpler puzzle..."
                QMessageBox.warning(self, "License Limit Exceeded", msg)
                print(f"License error detected: {error_msg}")
                self.new_puzzle()
                self.update_status("Puzzle reset due to license limit")
            else:
                msg = f"Could not find a solution within {self.solver_mode} horizon limit (max 12 moves).\n\nTry shuffling less or use a simpler configuration."
                QMessageBox.warning(self, "No Solution", msg)
                self.update_status("Solving failed - no solution found")
            return
        
        self.solution_moves = solution
        self.current_move_index = 0
        self.play_btn.setEnabled(True)
        self.step_btn.setEnabled(True)
        
        stats_text = f"Solution found!\n\n"
        stats_text += f"Solver Mode: {stats.get('mode', 'N/A')}\n"
        stats_text += f"Number of Moves: {stats.get('num_moves', 0)}\n"
        stats_text += f"Solve Time: {stats.get('solve_time', 0):.2f} seconds\n"
        stats_text += f"Variables: {stats.get('num_variables', 0)}\n"
        stats_text += f"Constraints: {stats.get('num_constraints', 0)}\n"
        
        if stats.get('objective_value') is not None:
            stats_text += f"Objective Value: {stats.get('objective_value'):.2f}\n"
        
        self.solution_text.setText(stats_text)
        self.update_status(f"Solution found: {len(solution)} moves")
    
    def play_solution(self):
        if not self.solution_moves:
            return
        
        self.current_move_index = 0
        self.play_btn.setEnabled(False)
        self.step_btn.setEnabled(False)
        self.solve_btn.setEnabled(False)
        self.shuffle_btn.setEnabled(False)
        
        self._play_next_move()
    
    def _play_next_move(self):
        if self.current_move_index >= len(self.solution_moves):
            self.play_btn.setEnabled(True)
            self.step_btn.setEnabled(True)
            self.solve_btn.setEnabled(True)
            self.shuffle_btn.setEnabled(True)
            self.update_status("Solution playback complete")
            
            if self.puzzle_state.is_goal():
                QMessageBox.information(self, "Success", "Puzzle solved successfully!")
            return
        
        move = self.solution_moves[self.current_move_index]
        empty_pos = self.puzzle_state.empty_pos
        
        self.puzzle_widget.animate_move(move, empty_pos)
        
        self.puzzle_state = self.puzzle_state.apply_move(move)
        self.current_move_index += 1
        
        self.update_status(f"Playing move {self.current_move_index}/{len(self.solution_moves)}")
        
        QTimer.singleShot(300, self._on_animation_complete)
    
    def _on_animation_complete(self):
        self.puzzle_widget.set_puzzle_state(self.puzzle_state)
        QTimer.singleShot(200, self._play_next_move)
    
    def step_solution(self):
        if not self.solution_moves or self.current_move_index >= len(self.solution_moves):
            return
        
        move = self.solution_moves[self.current_move_index]
        self.puzzle_state = self.puzzle_state.apply_move(move)
        self.puzzle_widget.set_puzzle_state(self.puzzle_state)
        self.current_move_index += 1
        
        self.update_status(f"Step {self.current_move_index}/{len(self.solution_moves)}")
        
        if self.current_move_index >= len(self.solution_moves):
            self.step_btn.setEnabled(False)
            if self.puzzle_state.is_goal():
                QMessageBox.information(self, "Success", "Puzzle solved successfully!")
    
    def on_tile_clicked(self, row: int, col: int):
        if self.puzzle_state and self.puzzle_state.is_valid_move((row, col)):
            self.puzzle_state = self.puzzle_state.apply_move((row, col))
            self.puzzle_widget.set_puzzle_state(self.puzzle_state)
            
            if self.puzzle_state.is_goal():
                QMessageBox.information(self, "Success", "You solved the puzzle manually!")
                self.update_status("Puzzle solved manually!")
    
    def update_status(self, message: str):
        self.status_bar.showMessage(f"{message} | Mode: {self.solver_mode}")
