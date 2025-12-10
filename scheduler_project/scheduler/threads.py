from PyQt6.QtCore import QThread, pyqtSignal as Signal
import logging
from scheduler_project.scheduler.model import solve_multi_machine

logger = logging.getLogger(__name__)

class SolveThread(QThread):
    finished_signal = Signal(object, object)
    error_signal = Signal(str)


    def __init__(self, tasks, objective="weighted_completion", time_limit=30, **kwargs):
        super().__init__()
        self.tasks = tasks
        self.objective = objective
        self.time_limit = time_limit
        self.kwargs = kwargs

    def run(self):
        try:
            sol, obj, model = solve_multi_machine(self.tasks,
                                                 time_limit=self.time_limit,
                                                 objective=self.objective,
                                                 **self.kwargs)
            self.finished_signal.emit(sol, obj)
        except Exception as e:
            logger.exception("Solver thread exception")
            self.error_signal.emit(str(e))

class CompareThread(QThread):
  
    finished_signal = Signal(object)
    error_signal = Signal(str)

    def __init__(self, tasks, objectives, time_limit=30, kwargs_per_obj=None):
        super().__init__()
        self.tasks = tasks
        self.objectives = objectives
        self.time_limit = time_limit
        self.kwargs_per_obj = kwargs_per_obj or {}

    def run(self):
        try:
            results = {}
            for obj in self.objectives:
                extra = self.kwargs_per_obj.get(obj, {})
                sol, objval, _ = solve_multi_machine(self.tasks,
                                                    time_limit=self.time_limit,
                                                    objective=obj,
                                                    **extra)
                results[obj] = (sol, objval)
            self.finished_signal.emit(results)
        except Exception as e:
            logger.exception("CompareThread exception")
            self.error_signal.emit(str(e))
