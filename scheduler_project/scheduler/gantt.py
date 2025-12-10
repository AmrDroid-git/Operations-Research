import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt


class GanttCanvas(FigureCanvas):
    def __init__(self, parent=None):
        fig = Figure(figsize=(10,5), tight_layout=True)
        super().__init__(fig)
        self.axes = fig.add_subplot(111)

    def plot_gantt(self, solution, title='Planning'):
        self.axes.clear()
        if not solution:
            self.draw()
            return
        machines = sorted(list({s['machine'] for s in solution}))
        machine_to_idx = {m:i for i,m in enumerate(machines)}
        palette = [plt.cm.tab20(i%20) for i in range(len(machines))]

        for s in solution:
            if s['start'] is None: 
                continue
            mi = machine_to_idx[s['machine']]
            self.axes.barh(mi, s['duration'], left=s['start'], height=0.5, edgecolor='black', color=palette[mi])
            self.axes.text(s['start']+s['duration']/2, mi, str(s['id']), va='center', ha='center', color='white', fontsize=8)

        self.axes.set_yticks(range(len(machines)))
        self.axes.set_yticklabels(machines)
        self.axes.set_xlabel('Temps (minutes)')
        self.axes.set_title(title)
        self.axes.invert_yaxis()
        self.draw()
