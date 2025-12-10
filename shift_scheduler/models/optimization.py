"""
Shift Scheduling Optimization Model
Uses Gurobi to optimize staff scheduling
"""

import gurobipy as gp
from gurobipy import GRB
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from models.employee import Employee
from models.demand import DemandProfile


@dataclass
class ScheduleResult:
    """Stores optimization results"""
    schedule: Dict[int, List[Tuple[int, int]]]  # employee_id -> [(start_hour, end_hour)]
    total_cost: float
    total_hours: Dict[int, float]  # employee_id -> hours worked
    coverage: Dict[int, int]  # hour -> staff count
    objective_value: float
    solve_time: float
    status: str
    gap: float = 0.0


class ShiftScheduler:
    """Optimizes employee shift scheduling using Gurobi"""
    
    def __init__(self, employees: List[Employee], demand: DemandProfile):
        self.employees = employees
        self.demand = demand
        self.model = None
        self.variables = {}
        self.result = None
        
    def build_model(self, 
                   objective: str = 'minimize_cost',
                   min_shift_length: int = 4,
                   max_shift_length: int = 8,
                   allow_overtime: bool = False):
        """
        Build the Gurobi optimization model
        
        Args:
            objective: 'minimize_cost' or 'maximize_coverage'
            min_shift_length: Minimum consecutive hours for a shift
            max_shift_length: Maximum consecutive hours for a shift
            allow_overtime: Allow employees to work beyond max_hours_per_day
        """
        self.model = gp.Model("ShiftScheduling")
        self.model.setParam('OutputFlag', 0)  # Suppress Gurobi output
        
        hours = range(self.demand.store_open_hour, self.demand.store_close_hour)
        employees = self.employees
        
        # Decision Variables
        # x[e, h] = 1 if employee e works hour h
        x = {}
        for emp in employees:
            for h in hours:
                x[emp.id, h] = self.model.addVar(vtype=GRB.BINARY, 
                                                 name=f"x_{emp.id}_{h}")
        
        # y[e, h] = 1 if employee e starts a shift at hour h
        y = {}
        for emp in employees:
            for h in hours:
                y[emp.id, h] = self.model.addVar(vtype=GRB.BINARY,
                                                 name=f"y_{emp.id}_{h}")
        
        # s[h] = number of staff working at hour h (for soft constraints)
        s = {}
        for h in hours:
            s[h] = self.model.addVar(vtype=GRB.INTEGER, lb=0,
                                     name=f"staff_{h}")
        
        # Shortage and surplus variables for coverage
        shortage = {}
        surplus = {}
        for h in hours:
            shortage[h] = self.model.addVar(vtype=GRB.INTEGER, lb=0,
                                           name=f"shortage_{h}")
            surplus[h] = self.model.addVar(vtype=GRB.INTEGER, lb=0,
                                          name=f"surplus_{h}")
        
        self.model.update()
        
        # CONSTRAINTS
        
        # 1. Staff count at each hour
        for h in hours:
            self.model.addConstr(
                s[h] == gp.quicksum(x[emp.id, h] for emp in employees),
                name=f"staff_count_{h}"
            )
        
        # 2. Coverage requirements with shortage/surplus
        for h in hours:
            required = self.demand.calculate_required_staff(h)
            self.model.addConstr(
                s[h] + shortage[h] - surplus[h] == required,
                name=f"coverage_{h}"
            )
        
        # 3. Employee availability
        for emp in employees:
            for h in hours:
                if not emp.is_available(h):
                    self.model.addConstr(x[emp.id, h] == 0,
                                        name=f"availability_{emp.id}_{h}")
        
        # 4. Maximum hours per day per employee
        for emp in employees:
            if allow_overtime:
                # Soft constraint with penalty
                max_hours = emp.max_hours_per_day * 1.5
            else:
                max_hours = emp.max_hours_per_day
                
            self.model.addConstr(
                gp.quicksum(x[emp.id, h] for h in hours) <= max_hours,
                name=f"max_hours_{emp.id}"
            )
        
        # 5. Shift continuity - if working, must work consecutive hours
        for emp in employees:
            for h in hours:
                if h < self.demand.store_close_hour - 1:
                    # Link x variables to shift starts
                    # If y[e,h] = 1, then x[e,h:h+min_shift] should be 1
                    for offset in range(min_shift_length):
                        if h + offset < self.demand.store_close_hour:
                            self.model.addConstr(
                                x[emp.id, h + offset] >= y[emp.id, h],
                                name=f"shift_min_{emp.id}_{h}_{offset}"
                            )
        
        # 6. One shift start per employee per day
        for emp in employees:
            self.model.addConstr(
                gp.quicksum(y[emp.id, h] for h in hours) <= 1,
                name=f"one_shift_{emp.id}"
            )
        
        # 7. Shift length limits
        for emp in employees:
            self.model.addConstr(
                gp.quicksum(x[emp.id, h] for h in hours) <= max_shift_length,
                name=f"shift_max_{emp.id}"
            )
        
        # OBJECTIVE FUNCTION
        if objective == 'minimize_cost':
            # Minimize total labor cost + penalty for shortages
            labor_cost = gp.quicksum(
                x[emp.id, h] * emp.hourly_rate
                for emp in employees
                for h in hours
            )
            shortage_penalty = 1000 * gp.quicksum(shortage[h] for h in hours)
            surplus_penalty = 10 * gp.quicksum(surplus[h] for h in hours)
            
            self.model.setObjective(
                labor_cost + shortage_penalty + surplus_penalty,
                GRB.MINIMIZE
            )
            
        elif objective == 'maximize_coverage':
            # Maximize coverage while minimizing cost as secondary
            coverage_score = gp.quicksum(s[h] for h in hours)
            labor_cost = gp.quicksum(
                x[emp.id, h] * emp.hourly_rate
                for emp in employees
                for h in hours
            )
            
            self.model.setObjective(
                1000 * coverage_score - labor_cost,
                GRB.MAXIMIZE
            )
        
        self.variables = {
            'x': x,
            'y': y,
            's': s,
            'shortage': shortage,
            'surplus': surplus
        }
        
        return self.model
    
    def solve(self, time_limit: int = 60) -> ScheduleResult:
        """
        Solve the optimization model
        
        Args:
            time_limit: Maximum solve time in seconds
            
        Returns:
            ScheduleResult object with solution
        """
        if self.model is None:
            raise ValueError("Model not built. Call build_model() first.")
        
        self.model.setParam('TimeLimit', time_limit)
        self.model.optimize()
        
        # Extract solution
        if self.model.status == GRB.OPTIMAL or self.model.status == GRB.TIME_LIMIT:
            schedule = self._extract_schedule()
            total_hours = self._calculate_total_hours(schedule)
            coverage = self._calculate_coverage(schedule)
            total_cost = self._calculate_total_cost(schedule)
            
            self.result = ScheduleResult(
                schedule=schedule,
                total_cost=total_cost,
                total_hours=total_hours,
                coverage=coverage,
                objective_value=self.model.objVal,
                solve_time=self.model.Runtime,
                status=self._get_status_string(),
                gap=self.model.MIPGap if hasattr(self.model, 'MIPGap') else 0.0
            )
        else:
            self.result = ScheduleResult(
                schedule={},
                total_cost=0.0,
                total_hours={},
                coverage={},
                objective_value=0.0,
                solve_time=self.model.Runtime,
                status=self._get_status_string()
            )
        
        return self.result
    
    def _extract_schedule(self) -> Dict[int, List[Tuple[int, int]]]:
        """Extract work schedule from solution"""
        schedule = {emp.id: [] for emp in self.employees}
        x = self.variables['x']
        
        for emp in self.employees:
            working_hours = []
            for h in range(self.demand.store_open_hour, self.demand.store_close_hour):
                if x[emp.id, h].X > 0.5:  # Binary variable is 1
                    working_hours.append(h)
            
            # Convert to shift blocks (start, end)
            if working_hours:
                shifts = []
                start = working_hours[0]
                prev = working_hours[0]
                
                for h in working_hours[1:]:
                    if h != prev + 1:  # Gap detected, new shift
                        shifts.append((start, prev + 1))
                        start = h
                    prev = h
                
                shifts.append((start, prev + 1))
                schedule[emp.id] = shifts
        
        return schedule
    
    def _calculate_total_hours(self, schedule: Dict) -> Dict[int, float]:
        """Calculate total hours worked per employee"""
        total_hours = {}
        for emp_id, shifts in schedule.items():
            hours = sum(end - start for start, end in shifts)
            total_hours[emp_id] = hours
        return total_hours
    
    def _calculate_coverage(self, schedule: Dict) -> Dict[int, int]:
        """Calculate staff coverage per hour"""
        coverage = {h: 0 for h in range(self.demand.store_open_hour, 
                                        self.demand.store_close_hour)}
        
        for emp_id, shifts in schedule.items():
            for start, end in shifts:
                for h in range(start, end):
                    coverage[h] += 1
        
        return coverage
    
    def _calculate_total_cost(self, schedule: Dict) -> float:
        """Calculate total labor cost"""
        total_cost = 0.0
        emp_dict = {emp.id: emp for emp in self.employees}
        
        for emp_id, shifts in schedule.items():
            if emp_id in emp_dict:
                hours = sum(end - start for start, end in shifts)
                total_cost += hours * emp_dict[emp_id].hourly_rate
        
        return total_cost
    
    def _get_status_string(self) -> str:
        """Get human-readable status"""
        status_map = {
            GRB.OPTIMAL: "Optimal",
            GRB.INFEASIBLE: "Infeasible",
            GRB.INF_OR_UNBD: "Infeasible or Unbounded",
            GRB.UNBOUNDED: "Unbounded",
            GRB.TIME_LIMIT: "Time Limit Reached",
        }
        return status_map.get(self.model.status, "Unknown")
    
    def get_solution_summary(self) -> str:
        """Get a text summary of the solution"""
        if self.result is None:
            return "No solution available"
        
        summary = []
        summary.append(f"=== Schedule Optimization Results ===")
        summary.append(f"Status: {self.result.status}")
        summary.append(f"Total Cost: ${self.result.total_cost:.2f}")
        summary.append(f"Solve Time: {self.result.solve_time:.2f}s")
        summary.append(f"\nEmployee Assignments:")
        
        emp_dict = {emp.id: emp for emp in self.employees}
        for emp_id, shifts in self.result.schedule.items():
            if shifts and emp_id in emp_dict:
                emp = emp_dict[emp_id]
                hours = self.result.total_hours[emp_id]
                cost = hours * emp.hourly_rate
                shift_str = ", ".join([f"{s}:00-{e}:00" for s, e in shifts])
                summary.append(f"  {emp.name}: {shift_str} ({hours}h, ${cost:.2f})")
        
        return "\n".join(summary)