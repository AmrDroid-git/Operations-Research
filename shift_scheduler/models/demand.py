"""
Demand Profile Model
Manages hourly customer demand and required staffing levels
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple
import json


@dataclass
class DemandProfile:
    """Represents customer demand profile throughout the day"""
    
    store_open_hour: int = 8  # Store opening hour (24h format)
    store_close_hour: int = 20  # Store closing hour (24h format)
    hourly_demand: Dict[int, int] = field(default_factory=dict)  # hour -> customer count
    staff_per_customer_ratio: float = 0.05  # Staff members needed per customer
    min_staff_per_hour: int = 1  # Minimum staff at any time
    
    def __post_init__(self):
        """Initialize hourly demand with zeros if not provided"""
        if not self.hourly_demand:
            for hour in range(self.store_open_hour, self.store_close_hour):
                self.hourly_demand[hour] = 0
        
        self._validate()
    
    def _validate(self):
        """Validate demand profile parameters"""
        if self.store_open_hour < 0 or self.store_open_hour >= 24:
            raise ValueError("Store open hour must be between 0 and 23")
        if self.store_close_hour <= self.store_open_hour or self.store_close_hour > 24:
            raise ValueError("Store close hour must be after open hour and <= 24")
        if self.staff_per_customer_ratio <= 0:
            raise ValueError("Staff per customer ratio must be positive")
        if self.min_staff_per_hour < 0:
            raise ValueError("Minimum staff cannot be negative")
    
    def set_demand(self, hour: int, customer_count: int):
        """Set customer demand for a specific hour"""
        if hour < self.store_open_hour or hour >= self.store_close_hour:
            raise ValueError(f"Hour {hour} is outside store operating hours")
        if customer_count < 0:
            raise ValueError("Customer count cannot be negative")
        self.hourly_demand[hour] = customer_count
    
    def get_demand(self, hour: int) -> int:
        """Get customer demand for a specific hour"""
        return self.hourly_demand.get(hour, 0)
    
    def calculate_required_staff(self, hour: int) -> int:
        """Calculate required staff for a specific hour based on demand"""
        demand = self.get_demand(hour)
        calculated_staff = int(demand * self.staff_per_customer_ratio)
        return max(calculated_staff, self.min_staff_per_hour)
    
    def get_all_required_staff(self) -> Dict[int, int]:
        """Get required staff for all operating hours"""
        return {
            hour: self.calculate_required_staff(hour)
            for hour in range(self.store_open_hour, self.store_close_hour)
        }
    
    def get_peak_hours(self, top_n: int = 3) -> List[Tuple[int, int]]:
        """Get the top N hours with highest demand"""
        sorted_hours = sorted(
            self.hourly_demand.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_hours[:top_n]
    
    def get_low_hours(self, bottom_n: int = 3) -> List[Tuple[int, int]]:
        """Get the bottom N hours with lowest demand"""
        sorted_hours = sorted(
            self.hourly_demand.items(),
            key=lambda x: x[1]
        )
        return sorted_hours[:bottom_n]
    
    def get_total_daily_customers(self) -> int:
        """Calculate total expected customers for the day"""
        return sum(self.hourly_demand.values())
    
    def get_average_hourly_demand(self) -> float:
        """Calculate average customers per hour"""
        if not self.hourly_demand:
            return 0.0
        return self.get_total_daily_customers() / len(self.hourly_demand)
    
    def get_operating_hours(self) -> int:
        """Get total number of operating hours"""
        return self.store_close_hour - self.store_open_hour
    
    def apply_pattern(self, pattern_name: str):
        """Apply a predefined demand pattern"""
        patterns = {
            'flat': self._flat_pattern,
            'morning_peak': self._morning_peak_pattern,
            'lunch_peak': self._lunch_peak_pattern,
            'evening_peak': self._evening_peak_pattern,
            'bimodal': self._bimodal_pattern,
            'weekend': self._weekend_pattern
        }
        
        if pattern_name.lower() in patterns:
            patterns[pattern_name.lower()]()
        else:
            raise ValueError(f"Unknown pattern: {pattern_name}")
    
    def _flat_pattern(self):
        """Flat demand throughout the day"""
        for hour in range(self.store_open_hour, self.store_close_hour):
            self.hourly_demand[hour] = 50
    
    def _morning_peak_pattern(self):
        """Peak demand in morning hours"""
        for hour in range(self.store_open_hour, self.store_close_hour):
            if hour < 12:
                self.hourly_demand[hour] = 80
            else:
                self.hourly_demand[hour] = 30
    
    def _lunch_peak_pattern(self):
        """Peak demand during lunch hours (12-14)"""
        for hour in range(self.store_open_hour, self.store_close_hour):
            if 11 <= hour <= 13:
                self.hourly_demand[hour] = 100
            else:
                self.hourly_demand[hour] = 40
    
    def _evening_peak_pattern(self):
        """Peak demand in evening hours"""
        for hour in range(self.store_open_hour, self.store_close_hour):
            if hour >= 17:
                self.hourly_demand[hour] = 90
            else:
                self.hourly_demand[hour] = 35
    
    def _bimodal_pattern(self):
        """Two peaks: lunch and evening"""
        for hour in range(self.store_open_hour, self.store_close_hour):
            if 11 <= hour <= 13 or 17 <= hour <= 19:
                self.hourly_demand[hour] = 85
            else:
                self.hourly_demand[hour] = 40
    
    def _weekend_pattern(self):
        """Weekend shopping pattern - gradual increase, peak afternoon"""
        for hour in range(self.store_open_hour, self.store_close_hour):
            if hour < 12:
                self.hourly_demand[hour] = 30 + (hour - self.store_open_hour) * 5
            elif 12 <= hour <= 16:
                self.hourly_demand[hour] = 90
            else:
                self.hourly_demand[hour] = 70 - (hour - 16) * 5
    
    def scale_demand(self, factor: float):
        """Scale all demand values by a factor"""
        for hour in self.hourly_demand:
            self.hourly_demand[hour] = int(self.hourly_demand[hour] * factor)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            'store_open_hour': self.store_open_hour,
            'store_close_hour': self.store_close_hour,
            'hourly_demand': self.hourly_demand,
            'staff_per_customer_ratio': self.staff_per_customer_ratio,
            'min_staff_per_hour': self.min_staff_per_hour
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'DemandProfile':
        """Create from dictionary"""
        return cls(**data)
    
    def to_json(self) -> str:
        """Export to JSON string"""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'DemandProfile':
        """Create from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def __str__(self) -> str:
        total = self.get_total_daily_customers()
        avg = self.get_average_hourly_demand()
        return f"DemandProfile({self.store_open_hour}-{self.store_close_hour}h, Total: {total}, Avg: {avg:.1f}/hr)"