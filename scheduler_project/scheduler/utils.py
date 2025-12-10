import json
import os
import logging
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

# ---------------- Logging ----------------
def setup_logging(log_dir="logs"):
    os.makedirs(log_dir, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(
                os.path.join(log_dir, f"scheduler_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
            ),
            logging.StreamHandler()
        ]
    )

# ---------------- JSON Export ----------------
def export_json(tasks, path):
    with open(path,'w',encoding='utf-8') as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)

# ---------------- PDF Export (Single Solution) ----------------
def export_pdf(solution, path):
    if not solution:
        logging.warning("Empty solution: nothing to export")
        return

    with PdfPages(path) as pdf:
        # --- Gantt chart ---
        fig, ax = plt.subplots(figsize=(11,6))
        machines = sorted(list({s['machine'] for s in solution if s.get('machine') is not None}))
        machine_to_idx = {m:i for i,m in enumerate(machines)}
        palette = [plt.cm.tab20(i%20) for i in range(len(machines))]

        for s in solution:
            if s.get('start') is None or s.get('machine') not in machine_to_idx:
                continue
            mi = machine_to_idx[s['machine']]
            ax.barh(mi, s['duration'], left=s['start'], height=0.5, edgecolor='black', color=palette[mi])
            ax.text(s['start']+s['duration']/2, mi, str(s.get('id','')), va='center', ha='center', color='white', fontsize=8)

        ax.set_yticks(range(len(machines)))
        ax.set_yticklabels(machines)
        ax.set_xlabel('Temps (minutes)')
        ax.set_title('Diagramme de Gantt - Planning patients')
        ax.invert_yaxis()
        pdf.savefig(fig)
        plt.close(fig)

        # --- Task Table ---
        df = pd.DataFrame([
            {
                'ID': s.get('id',''),
                'Machine': s.get('machine',''),
                'Start': s.get('start',''),
                'End': s.get('end',''),
                'Staff': s.get('staff_group','')
            }
            for s in solution
        ])
        fig2, ax2 = plt.subplots(figsize=(11,6))
        ax2.axis('off')
        tbl = ax2.table(cellText=df.values, colLabels=df.columns, loc='center')
        tbl.auto_set_font_size(False)
        tbl.set_fontsize(8)
        tbl.scale(1,1.5)
        ax2.set_title('Détail des tâches')
        pdf.savefig(fig2)
        plt.close(fig2)

# ---------------- PDF Export (Compare Objectives) ----------------
def export_compare_pdf(results: dict, left_obj: str, right_obj: str, path: str):
    left_sol, left_val = results.get(left_obj, ([], None))
    right_sol, right_val = results.get(right_obj, ([], None))

    if not left_sol and not right_sol:
        logging.warning("Empty solutions for comparison: nothing to export")
        return

    with PdfPages(path) as pdf:
        # --- Gantt charts side by side ---
        fig, axs = plt.subplots(1, 2, figsize=(16,6), sharey=True)
        for ax, sol, obj_name, val in zip(axs, [left_sol, right_sol], [left_obj, right_obj], [left_val, right_val]):
            machines = sorted(list({s['machine'] for s in sol if s.get('machine') is not None}))
            machine_to_idx = {m:i for i,m in enumerate(machines)}
            palette = [plt.cm.tab20(i%20) for i in range(len(machines))]

            for s in sol:
                if s.get('start') is None or s.get('machine') not in machine_to_idx:
                    continue
                mi = machine_to_idx[s['machine']]
                ax.barh(mi, s['duration'], left=s['start'], height=0.5, edgecolor='black', color=palette[mi])
                ax.text(s['start']+s['duration']/2, mi, str(s.get('id','')), va='center', ha='center', color='white', fontsize=8)

            ax.set_yticks(range(len(machines)))
            ax.set_yticklabels(machines)
            ax.set_xlabel('Temps (minutes)')
            title_val = val if val is not None else 0.0
            ax.set_title(f'{obj_name} - Obj {title_val:.2f}')
            ax.invert_yaxis()

        pdf.savefig(fig)
        plt.close(fig)

        # --- KPI Table ---
        map_left = {s['id']: s for s in (left_sol or [])}
        map_right = {s['id']: s for s in (right_sol or [])}
        ids = sorted(set(map_left.keys()).union(map_right.keys()))
        data = []

        for tid in ids:
            left_task = map_left.get(tid, {})
            r = map_right.get(tid, {})
            lstart = left_task.get('start')
            rstart = r.get('start')
            dur = left_task.get('duration') or r.get('duration') or ''
            delta = f"{(rstart - lstart):.2f}" if lstart is not None and rstart is not None else ''
            data.append([tid, f"{lstart:.2f}" if lstart is not None else '', f"{rstart:.2f}" if rstart is not None else '', dur, delta])

        df = pd.DataFrame(data, columns=['ID', f'Start ({left_obj})', f'Start ({right_obj})', 'Duration', 'Delta Start'])
        fig2, ax2 = plt.subplots(figsize=(11,6))
        ax2.axis('off')
        tbl = ax2.table(cellText=df.values, colLabels=df.columns, loc='center')
        tbl.auto_set_font_size(False)
        tbl.set_fontsize(8)
        tbl.scale(1,1.5)
        ax2.set_title('Comparaison des tâches et delta start')
        pdf.savefig(fig2)
        plt.close(fig2)
