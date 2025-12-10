"""
Employee Model
Data class for storing employee information
"""

from dataclasses import dataclass, field
from typing import List, Set
from datetime import time


@dataclass
class Employee:
    """Represents a retail store employee"""
    
    id: int
    name: str
    hourly_rate: float
    max_hours_per_day: int = 8
    max_hours_per_week: int = 40
    availability: Set[int] = field(default_factory=set)  # Set of available hours (0-23)
    skills: List[str] = field(default_factory=list)
    preferred_shifts: List[str] = field(default_factory=list)  # 'morning', 'afternoon', 'evening'
    
    def __post_init__(self):
        """Validate employee data after initialization"""
        if self.hourly_rate <= 0:
            raise ValueError("Hourly rate must be positive")
        if self.max_hours_per_day <= 0 or self.max_hours_per_day > 24:
            raise ValueError("Max hours per day must be between 1 and 24")
        if not self.name.strip():
            raise ValueError("Employee name cannot be empty")
            
    def is_available(self, hour: int) -> bool:
        """Check if employee is available at a specific hour"""
        return hour in self.availability
    
    def add_availability(self, start_hour: int, end_hour: int):
        """Add availability for a time range"""
        for hour in range(start_hour, end_hour):
            self.availability.add(hour)
    
    def remove_availability(self, hour: int):
        """Remove availability for a specific hour"""
        self.availability.discard(hour)
    
    def has_skill(self, skill: str) -> bool:
        """Check if employee has a specific skill"""
        return skill.lower() in [s.lower() for s in self.skills]
    
    def get_daily_cost(self, hours: float) -> float:
        """Calculate cost for working specified hours"""
        return hours * self.hourly_rate
    
    def to_dict(self) -> dict:
        """Convert employee to dictionary for serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'hourly_rate': self.hourly_rate,
            'max_hours_per_day': self.max_hours_per_day,
            'max_hours_per_week': self.max_hours_per_week,
            'availability': list(self.availability),
            'skills': self.skills,
            'preferred_shifts': self.preferred_shifts
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Employee':
        """Create employee from dictionary"""
        data['availability'] = set(data.get('availability', []))
        return cls(**data)
    
    def __str__(self) -> str:
        return f"Employee({self.id}: {self.name}, ${self.hourly_rate}/hr)"
    
    def __repr__(self) -> str:
        return self.__str__()


class EmployeeManager:
    """Manager class for handling multiple employees"""
    
    def __init__(self):
        self.employees: List[Employee] = []
        self._next_id = 1
    
    def add_employee(self, name: str, hourly_rate: float, **kwargs) -> Employee:
        """Add a new employee"""
        employee = Employee(
            id=self._next_id,
            name=name,
            hourly_rate=hourly_rate,
            **kwargs
        )
        self.employees.append(employee)
        self._next_id += 1
        return employee
    
    def remove_employee(self, employee_id: int) -> bool:
        """Remove an employee by ID"""
        for i, emp in enumerate(self.employees):
            if emp.id == employee_id:
                self.employees.pop(i)
                return True
        return False
    
    def get_employee(self, employee_id: int) -> Employee:
        """Get employee by ID"""
        for emp in self.employees:
            if emp.id == employee_id:
                return emp
        return None
    
    def get_all_employees(self) -> List[Employee]:
        """Get all employees"""
        return self.employees.copy()
    
    def get_available_employees(self, hour: int) -> List[Employee]:
        """Get all employees available at a specific hour"""
        return [emp for emp in self.employees if emp.is_available(hour)]
    
    def get_employees_with_skill(self, skill: str) -> List[Employee]:
        """Get all employees with a specific skill"""
        return [emp for emp in self.employees if emp.has_skill(skill)]
    
    def clear(self):
        """Remove all employees"""
        self.employees.clear()
        self._next_id = 1
    
    def get_total_labor_capacity(self) -> int:
        """Get total available labor hours per day"""
        return sum(emp.max_hours_per_day for emp in self.employees)
    
    def get_average_hourly_rate(self) -> float:
        """Calculate average hourly rate across all employees"""
        if not self.employees:
            return 0.0
        return sum(emp.hourly_rate for emp in self.employees) / len(self.employees)
    
    def __len__(self) -> int:
        return len(self.employees)
    
    def __iter__(self):
        return iter(self.employees)