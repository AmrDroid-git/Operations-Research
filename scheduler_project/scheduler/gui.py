import json
import logging
from PyQt6.QtWidgets import QComboBox
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QTableWidget, QTableWidgetItem, QFileDialog, QMessageBox,  
    QProgressBar, QLineEdit
)
from PyQt6.QtWidgets import QHeaderView


from scheduler_project.scheduler.threads import SolveThread, CompareThread
from scheduler_project.scheduler.utils import setup_logging, export_json, export_pdf, export_compare_pdf
from scheduler_project.scheduler.gantt import GanttCanvas

from PyQt6.QtWidgets import QDialog, QDoubleSpinBox, QGridLayout

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Scheduler - Imagerie Médicale 🏥')
        self.resize(500, 690)

        self._apply_styles()

        central = QWidget()
        self.setCentralWidget(central)
        v = QVBoxLayout(central)

       
        toolbar = QHBoxLayout()
        
        load_json_btn = QPushButton('🔁 Import JSON')
        load_json_btn.clicked.connect(self.import_json)
        export_json_btn = QPushButton('💾 Export JSON')
        export_json_btn.clicked.connect(self.export_json)
        self.solve_btn = QPushButton('▶ Résoudre (Gurobi)')
        self.solve_btn.clicked.connect(self.start_solve)
        self.pdf_btn = QPushButton('📄 Export PDF')
        self.pdf_btn.clicked.connect(self.export_pdf)
        self.pdf_btn.setEnabled(False)
        self.obj_selector = QComboBox()
        self.obj_selector.addItems([
            "Weighted completion", 
            "Makespan", 
            "Multi-criteria (makespan + staff)"
        ])

        toolbar.addWidget(QLabel("Objectif:"))
        toolbar.addWidget(self.obj_selector)
        self.alpha_spin = QDoubleSpinBox()
        self.alpha_spin.setRange(0.0, 1000.0)
        self.alpha_spin.setValue(1.0)
        self.beta_spin = QDoubleSpinBox()
        self.beta_spin.setRange(0.0, 1000.0)
        self.beta_spin.setValue(0.5)
        toolbar.addWidget(QLabel("α:"))
        toolbar.addWidget(self.alpha_spin)
        toolbar.addWidget(QLabel("β:"))
        toolbar.addWidget(self.beta_spin)

        self.compare_btn = QPushButton('🔍 Comparer objectifs')
        self.compare_btn.clicked.connect(self.start_compare)
        toolbar.addWidget(self.compare_btn)



        for w in [load_json_btn, export_json_btn, self.solve_btn, self.pdf_btn]:
            toolbar.addWidget(w)
        toolbar.addStretch()
        v.addLayout(toolbar)

        self.table = QTableWidget(0, 9)
        headers = ['ID','Durée','Machine','Priorité','Release','Deadline','StaffGroup','SetupAfter(JSON)','Notes']
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        v.addWidget(self.table, 5)

        
        lower = QHBoxLayout()
        left = QVBoxLayout()
        self.gantt = GanttCanvas(self)
        left.addWidget(self.gantt, 3)
        self.info = QLabel('Prêt')
        left.addWidget(self.info)
        lower.addLayout(left, 3)

        right = QVBoxLayout()
        self.res_table = QTableWidget(0,5)
        self.res_table.setHorizontalHeaderLabels(['ID','Machine','Start','End','Staff'])
        self.res_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        right.addWidget(self.res_table)
        self.progress = QProgressBar()
        self.progress.setRange(0,0)
        self.progress.setVisible(False)
        right.addWidget(self.progress)
        lower.addLayout(right,2)
        v.addLayout(lower,4)

        footer = QHBoxLayout()
        footer.addWidget(QLabel('Recherche ID:'))
        self.search_input = QLineEdit()
        self.search_input.textChanged.connect(self.search_table)
        footer.addWidget(self.search_input)
        v.addLayout(footer)

        

    # --- Styles ---
    def _apply_styles(self):
        qss = """
        QMainWindow { 
            background-color: #1e1e2f;  /* Dark blue-purple base */
            font-family: 'Segoe UI', Arial, sans-serif;
            color: #e0e0e0;
        }
        QPushButton { 
            padding: 6px 12px; 
            border-radius: 6px; 
            background-color: #6a5acd;  /* Slate purple */
            color: white; 
            font-weight: bold;
        }
        QPushButton:hover { 
            background-color: #836fff;  /* Lighter purple on hover */
        }
        QPushButton:disabled {
            background-color: #555573;
            color: #cccccc;
        }
        QTableWidget { 
            font-size: 12px; 
            background-color: #2a2a3e;  /* Slightly lighter dark blue */
            gridline-color: #444466; 
            alternate-background-color: #35354b;
            color: #e0e0e0;
        }
        QTableWidget::item:selected { 
            background-color: #836fff;  /* Highlight selection in mauve */
            color: white;
        }
        QHeaderView::section { 
            background-color: #3b3b5c; 
            padding: 4px;
            border: 1px solid #555573;
            font-weight: bold;
            color: #e0e0e0;
        }
        QLabel { 
            font-size: 12px; 
            color: #e0e0e0; 
        }
        QLineEdit { 
            background-color: #2a2a3e; 
            border: 1px solid #555573; 
            padding: 4px;
            border-radius: 4px;
            color: #e0e0e0;
        }
        QLineEdit:focus {
            border: 1px solid #836fff;
        }
        QProgressBar { 
            background-color: #2a2a3e; 
            border: 1px solid #555573;
            border-radius: 5px;
            text-align: center;
            color: #e0e0e0;
        }
        QProgressBar::chunk { 
            background-color: #6a5acd; 
            border-radius: 5px;
        }
        """
        self.setStyleSheet(qss)




    

    def import_json(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Ouvrir JSON', '', 'JSON Files (*.json)')
        if not path:
            return
        try:
            with open(path,'r',encoding='utf-8') as f:
                data = json.load(f)
            self.table.setRowCount(0)
            for t in data:
                r = self.table.rowCount()
                self.table.insertRow(r)
                self.table.setItem(r,0,QTableWidgetItem(str(t.get('id',''))))
                self.table.setItem(r,1,QTableWidgetItem(str(float(t.get('duration',1.0)))))
                self.table.setItem(r,2,QTableWidgetItem(str(t.get('machine',''))))
                self.table.setItem(r,3,QTableWidgetItem(str(float(t.get('priority',1.0)))))
                self.table.setItem(r,4,QTableWidgetItem(str(float(t.get('release',0.0)))))
                self.table.setItem(r,5,QTableWidgetItem(str(t.get('deadline',''))))
                self.table.setItem(r,6,QTableWidgetItem(str(t.get('staff_group',''))))
                self.table.setItem(r,7,QTableWidgetItem(json.dumps(t.get('setup_after',{}))))
                self.table.setItem(r,8,QTableWidgetItem(''))
        except Exception as e:
            QMessageBox.critical(self,'Erreur import',str(e))

   

    def export_json(self):
        tasks = self.read_table_tasks()
        if not tasks:
            return
        path, _ = QFileDialog.getSaveFileName(self,'Enregistrer JSON','', 'JSON Files (*.json)')
        if not path: 
            return
        export_json(tasks, path)
        QMessageBox.information(self,'Export','Exporté avec succès')
    
    
    def read_table_tasks(self):
        tasks = []
        for r in range(self.table.rowCount()):
            try:
                tid = self.table.item(r, 0).text().strip() if self.table.item(r, 0) else f'P{r+1}'
                duration = self._to_float(self.table.item(r, 1).text(), default=1.0)
                machine = self.table.item(r, 2).text().strip() if self.table.item(r, 2) else 'M1'
                priority = self._to_float(self.table.item(r, 3).text(), default=1.0)
                release = self._to_float(self.table.item(r, 4).text(), default=0.0)
                deadline_text = self.table.item(r, 5).text().strip() if self.table.item(r, 5) else ''
                deadline = None
                if deadline_text:
                    deadline = self._to_float(deadline_text, default=None)
                staff_group = self.table.item(r, 6).text().strip() if self.table.item(r, 6) else None
                setup_json = self.table.item(r, 7).text() if self.table.item(r, 7) else '{}'
                try:
                    setup_after = json.loads(setup_json)
                    if not isinstance(setup_after, dict):
                        raise ValueError("setup_after must be a JSON object")
                except Exception:
                    setup_after = {}
                setup_after_float = {str(k): self._to_float(v, default=0.0) for k,v in setup_after.items()}
                task_dict = {
                    'id': tid,
                    'duration': duration,
                    'machine': machine,
                    'priority': priority,
                    'release': release,
                    'staff_group': staff_group,
                    'setup_after': setup_after_float
                }
                if deadline is not None:
                    task_dict['deadline'] = deadline
                tasks.append(task_dict)
            except Exception as e:
                QMessageBox.warning(self,'Erreur données',f'Ligne {r+1} invalide: {e}')
                return []
        return tasks

    def _to_float(self, val, default=0.0):
        
        if val is None or str(val).strip() == '':
            return default
        try:
            return float(val)
        except (ValueError, TypeError):
            return default

    def start_solve(self):
        tasks = self.read_table_tasks()
        if not tasks:
            return
        self.solve_btn.setEnabled(False)
        self.progress.setVisible(True)
        # get selected objective
        obj_map = {
            "Weighted completion": "weighted_completion",
            "Makespan": "makespan",
            "Multi-criteria (makespan + staff)": "multi_criteria"
        }
        selected_obj = obj_map.get(self.obj_selector.currentText(), "weighted_completion")
        self.thread = SolveThread(tasks, objective=selected_obj)
        self.thread.finished_signal.connect(self.on_solved)
        self.thread.error_signal.connect(self.on_error)
        self.thread.start()

        self.info.setText(f'Résolution en cours... Objectif: {self.obj_selector.currentText()}')

    def on_solved(self, solution, obj):
        logger.info('Received solution with %d items', len(solution))
        self.progress.setVisible(False)
        self.solve_btn.setEnabled(True)
        self.pdf_btn.setEnabled(True)
        self.info.setText(f'Terminé - objectif: {obj:.2f}')
        # populate result table
        self.res_table.setRowCount(0)
        for s in sorted(solution, key=lambda x: (x['machine'], x['start'] if x['start'] is not None else 0)):
            r = self.res_table.rowCount()
            self.res_table.insertRow(r)
            self.res_table.setItem(r,0,QTableWidgetItem(str(s['id'])))
            self.res_table.setItem(r,1,QTableWidgetItem(str(s['machine'])))
            self.res_table.setItem(r,2,QTableWidgetItem(f"{s['start']:.2f}" if s['start'] is not None else ''))
            self.res_table.setItem(r,3,QTableWidgetItem(f"{s['end']:.2f}" if s['end'] is not None else ''))
            self.res_table.setItem(r,4,QTableWidgetItem(str(s.get('staff_group',''))))
        self.gantt.plot_gantt(solution, title=f'Planning - Obj {obj:.2f}')
        self._last_solution = solution

    def on_error(self, msg):
        logger.error('Solver error: %s', msg)
        QMessageBox.critical(self,'Erreur solveur', str(msg))
        self.progress.setVisible(False)
        self.solve_btn.setEnabled(True)

    def export_pdf(self):
        if not hasattr(self,'_last_solution') or not self._last_solution:
            QMessageBox.warning(self,'PDF','Pas de solution à exporter')
            return
        path, _ = QFileDialog.getSaveFileName(self,'Exporter PDF','planning.pdf','PDF Files (*.pdf)')
        if not path:
            return
        export_pdf(self._last_solution, path)

    def search_table(self, text):
        t = text.strip().lower()
        for r in range(self.table.rowCount()):
            idv = self.table.item(r,0).text().lower() if self.table.item(r,0) else ''
            self.table.setRowHidden(r, t not in idv)

    def start_compare(self):
        tasks = self.read_table_tasks()
        if not tasks:
            QMessageBox.warning(self, "Comparer", "Aucune tâche valide.")
            return

        # define objectives to compare
        alpha = float(self.alpha_spin.value())
        beta = float(self.beta_spin.value())
        objs = [
            "makespan",
            "weighted_completion",
            f"weighted_sum:{alpha}:{beta}"
        ]
        kwargs_map = {
            "makespan": {},
            "weighted_completion": {},
            f"weighted_sum:{alpha}:{beta}": {}
        }

        self.compare_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.compare_thread = CompareThread(tasks, objectives=objs, time_limit=30, kwargs_per_obj=kwargs_map)
        self.compare_thread.finished_signal.connect(self.on_compare_done)
        self.compare_thread.error_signal.connect(self.on_error)
        self.compare_thread.start()
        self.info.setText("Comparaison en cours...")

    def on_compare_done(self, results):
        self.progress.setVisible(False)
        self.compare_btn.setEnabled(True)
        self.info.setText("Comparaison terminée")
        # results: dict objective -> (sol, obj)
        # create and show dialog
        dlg = CompareDialog(self, results)
        dlg.exec()

class CompareDialog(QDialog):
    def __init__(self, parent, results: dict):
        super().__init__(parent)
        self.setWindowTitle("Comparaison des objectifs")
        self.resize(1000, 600)
        layout = QVBoxLayout(self)

        # top: two Gantt canvases side-by-side (take first two objectives)
        objs = list(results.keys())
        left_obj = objs[0]
        right_obj = objs[1] if len(objs) > 1 else objs[0]

        grid = QGridLayout()
        self.gantt_left = GanttCanvas(self)
        self.gantt_right = GanttCanvas(self)
        grid.addWidget(QLabel(left_obj), 0, 0)
        grid.addWidget(QLabel(right_obj), 0, 1)
        grid.addWidget(self.gantt_left, 1, 0)
        grid.addWidget(self.gantt_right, 1, 1)
        layout.addLayout(grid, 3)

        self.kpi_table = QTableWidget(0, 5)
        self.kpi_table.setHorizontalHeaderLabels(['ID', f'Start ({left_obj})', f'Start ({right_obj})', 'Duration', 'Delta Start'])
        layout.addWidget(self.kpi_table, 2)

        footer = QHBoxLayout()
        export_left_btn = QPushButton(f'Export {left_obj} JSON')
        export_left_btn.clicked.connect(lambda: self._export_solution(results[left_obj][0]))
        export_right_btn = QPushButton(f'Export {right_obj} JSON')
        export_right_btn.clicked.connect(lambda: self._export_solution(results[right_obj][0]))

        export_pdf_btn = QPushButton("Export PDF comparatif")
        export_pdf_btn.clicked.connect(lambda: self._export_pdf(results, left_obj, right_obj))

        footer.addWidget(export_left_btn)
        footer.addWidget(export_right_btn)
        footer.addWidget(export_pdf_btn)  
        footer.addStretch()
        layout.addLayout(footer)



        self.populate(results, left_obj, right_obj)


    def _export_pdf(self, results, left_obj, right_obj):
        path, _ = QFileDialog.getSaveFileName(self, 'Exporter PDF comparatif','comparatif.pdf','PDF Files (*.pdf)')
        if not path:
            return
        export_compare_pdf(results, left_obj, right_obj, path)
        QMessageBox.information(self, 'Export PDF', 'PDF comparatif exporté avec succès')

    def populate(self, results, left_obj, right_obj):
        left_sol, left_val = results[left_obj]
        right_sol, right_val = results[right_obj]
        self.gantt_left.plot_gantt(left_sol, title=f'{left_obj} - Obj {left_val:.2f}' if left_val is not None else left_obj)
        self.gantt_right.plot_gantt(right_sol, title=f'{right_obj} - Obj {right_val:.2f}' if right_val is not None else right_obj)

        # build map id->start for quick compare
        map_left = {s['id']: s for s in (left_sol or [])}
        map_right = {s['id']: s for s in (right_sol or [])}
        ids = sorted(set(map_left.keys()).union(map_right.keys()))
        self.kpi_table.setRowCount(0)
        for tid in ids:
            left_task = map_left.get(tid, {})
            r = map_right.get(tid, {})
            lstart = left_task.get('start')
            rstart = r.get('start')
            dur = left_task.get('duration') or r.get('duration') or ''
            delta = ''
            if lstart is not None and rstart is not None:
                delta = f"{(rstart - lstart):.2f}"
            rr = self.kpi_table.rowCount()
            self.kpi_table.insertRow(rr)
            self.kpi_table.setItem(rr, 0, QTableWidgetItem(str(tid)))
            self.kpi_table.setItem(rr, 1, QTableWidgetItem(f"{lstart:.2f}" if lstart is not None else ''))
            self.kpi_table.setItem(rr, 2, QTableWidgetItem(f"{rstart:.2f}" if rstart is not None else ''))
            self.kpi_table.setItem(rr, 3, QTableWidgetItem(str(dur)))
            self.kpi_table.setItem(rr, 4, QTableWidgetItem(str(delta)))

    def _export_solution(self, sol):
        path, _ = QFileDialog.getSaveFileName(self, 'Enregistrer JSON','solution.json','JSON Files (*.json)')
        if not path:
            return
        export_json(sol, path)
        QMessageBox.information(self, 'Export', 'Exporté avec succès')




def main():
    import sys
    from PyQt6.QtWidgets import QApplication

    setup_logging()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
