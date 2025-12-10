"""
Models Package
Contains data models and optimization logic
"""

from .employee import Employee, EmployeeManager
from .demand import DemandProfile
from .optimization import ShiftScheduler, ScheduleResult

__all__ = [
    'Employee',
    'EmployeeManager',
    'DemandProfile',
    'ShiftScheduler',
    'ScheduleResult',
]