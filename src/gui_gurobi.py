# src/gui_gurobi.py
import sys, os
import pandas as pd
from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QFileDialog, QMessageBox
import matplotlib
# ensure using Qt backend
matplotlib.use("QtAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from gurobi_maxkcover import solve_max_k_coverage_with_gurobi
from greedy_fast import greedy_max_k_cover_fast

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Billboard selection — Gurobi / Greedy")
        self.resize(1000, 700)

        self.candidates = None
        self.population = None

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)

        hl = QtWidgets.QHBoxLayout()
        self.btn_load_cand = QtWidgets.QPushButton("Load candidates CSV")
        self.btn_load_pop = QtWidgets.QPushButton("Load population CSV")
        self.spin_k = QtWidgets.QSpinBox(); self.spin_k.setMinimum(1); self.spin_k.setValue(3)
        self.spin_radius = QtWidgets.QDoubleSpinBox(); self.spin_radius.setMinimum(0.01); self.spin_radius.setMaximum(1e6); self.spin_radius.setDecimals(2); self.spin_radius.setValue(5.0)
        self.btn_solve = QtWidgets.QPushButton("Solve (Gurobi preferred)")
        hl.addWidget(self.btn_load_cand); hl.addWidget(self.btn_load_pop)
        hl.addWidget(QtWidgets.QLabel("k:")); hl.addWidget(self.spin_k)
        hl.addWidget(QtWidgets.QLabel("radius:")); hl.addWidget(self.spin_radius)
        hl.addWidget(self.btn_solve)
        layout.addLayout(hl)

        self.table = QtWidgets.QTableWidget()
        layout.addWidget(self.table, 1)

        self.fig, self.ax = plt.subplots(figsize=(6,4))
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas, 3)

        self.btn_load_cand.clicked.connect(self.load_candidates)
        self.btn_load_pop.clicked.connect(self.load_population)
        self.btn_solve.clicked.connect(self.solve_problem)

        self.statusBar().showMessage("Ready")

    def load_candidates(self):
        fn, _ = QFileDialog.getOpenFileName(self, "Open candidates CSV", "", "CSV Files (*.csv);;All Files (*)")
        if not fn: return
        try:
            df = pd.read_csv(fn)
            if not set(['id','x','y']).issubset(df.columns):
                QMessageBox.critical(self, "Error", "Candidates CSV must have columns id,x,y")
                return
            self.candidates = df
            self.statusBar().showMessage(f"Loaded {len(df)} candidates")
            self.spin_k.setMaximum(max(1, len(df)))
            self.refresh_plot()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def load_population(self):
        fn, _ = QFileDialog.getOpenFileName(self, "Open population CSV", "", "CSV Files (*.csv);;All Files (*)")
        if not fn: return
        try:
            df = pd.read_csv(fn)
            if not set(['id','x','y','pop']).issubset(df.columns):
                QMessageBox.critical(self, "Error", "Population CSV must have columns id,x,y,pop")
                return
            self.population = df
            self.statusBar().showMessage(f"Loaded {len(df)} population points")
            self.refresh_plot()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def refresh_plot(self):
        # Draw base plot only (no solution circles)
        self.ax.clear()
        if self.population is not None:
            self.ax.scatter(self.population['x'], self.population['y'], s=20, alpha=0.6, label='population')
        if self.candidates is not None:
            self.ax.scatter(self.candidates['x'], self.candidates['y'], marker='s', s=60, label='candidates')
        self.ax.legend()
        self.ax.set_xlabel("x")
        self.ax.set_ylabel("y")
        self.canvas.draw()

    def solve_problem(self):
        if self.candidates is None or self.population is None:
            QMessageBox.warning(self, "Missing data", "Load candidates and population first")
            return
        k = int(self.spin_k.value())
        radius = float(self.spin_radius.value())
        self.btn_solve.setEnabled(False)
        self.statusBar().showMessage("Solving... (may take time)")

        selected_ids = []
        total_cov = 0.0
        covered_mask = None
        method = "None"

        # Try Gurobi first
        try:
            selected_ids, total_cov, model = solve_max_k_coverage_with_gurobi(self.candidates, self.population, k, radius)
            method = "Gurobi (exact)"
            # model may be None if not solved; it's okay
        except Exception as e:
            # fallback to greedy, capture exception text in status
            self.statusBar().showMessage(f"Gurobi failed or not available: {str(e)} — using greedy")
            selected_ids, total_cov, covered_mask = greedy_max_k_cover_fast(self.candidates, self.population, k, radius)
            method = "Greedy fallback"

        # Fill table with selected candidates
        self.table.clear()
        self.table.setRowCount(len(selected_ids))
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["rank","id","coords"])
        for i, cid in enumerate(selected_ids):
            try:
                coords = self.candidates[self.candidates['id']==cid][['x','y']].iloc[0]
                coord_text = f"{coords['x']:.3f}, {coords['y']:.3f}"
            except Exception:
                coord_text = ""
            self.table.setItem(i,0, QtWidgets.QTableWidgetItem(str(i+1)))
            self.table.setItem(i,1, QtWidgets.QTableWidgetItem(str(cid)))
            self.table.setItem(i,2, QtWidgets.QTableWidgetItem(coord_text))

        # Plot everything and circles
        self.ax.clear()
        if self.population is not None:
            self.ax.scatter(self.population['x'], self.population['y'], s=20, alpha=0.6, label='population')
        if self.candidates is not None:
            self.ax.scatter(self.candidates['x'], self.candidates['y'], marker='s', s=60, label='candidates')

        # plot selected candidates and circles
        for cid in selected_ids:
            rows = self.candidates[self.candidates['id']==cid]
            if rows.empty:
                continue
            row = rows.iloc[0]
            cx, cy = float(row['x']), float(row['y'])
            # draw two concentric circles for visibility
            circle1 = plt.Circle((cx, cy), radius, fill=False, edgecolor='red', linewidth=1.2)
            circle2 = plt.Circle((cx, cy), radius*0.6, fill=False, edgecolor='red', linewidth=0.8, linestyle='--')
            self.ax.add_patch(circle1)
            self.ax.add_patch(circle2)
            self.ax.scatter([cx],[cy], color='red', s=80)

        self.ax.legend()
        # autoscale limits a bit to include circles
        try:
            all_x = []
            all_y = []
            if self.population is not None:
                all_x += list(self.population['x'].values)
                all_y += list(self.population['y'].values)
            if self.candidates is not None:
                all_x += list(self.candidates['x'].values)
                all_y += list(self.candidates['y'].values)
            if all_x and all_y:
                xmin, xmax = min(all_x), max(all_x)
                ymin, ymax = min(all_y), max(all_y)
                pad_x = max(1.0, (xmax - xmin) * 0.05)
                pad_y = max(1.0, (ymax - ymin) * 0.05)
                self.ax.set_xlim(xmin - pad_x - radius, xmax + pad_x + radius)
                self.ax.set_ylim(ymin - pad_y - radius, ymax + pad_y + radius)
        except Exception:
            pass

        self.canvas.draw()
        self.statusBar().showMessage(f"Solved with {method}. Covered pop: {total_cov:.1f}")
        self.btn_solve.setEnabled(True)

def main():
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
