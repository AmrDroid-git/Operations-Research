"""
Sample Test Data and Examples
=============================

This file contains sample data configurations for testing the scheduler.
Copy and modify these as needed for your use case.
"""

from models import Employee, EmployeeManager, DemandProfile


def create_sample_employees() -> EmployeeDatabase:
    """Create a sample employee database for testing."""
    db = EmployeeDatabase()
    
    # Full-time employees
    employees = [
        {
            'id': 'EMP001',
            'name': 'Alice Johnson',
            'rate': 18.0,
            'max_daily': 8,
            'max_weekly': 40,
            'skills': [Skill.CASHIER, Skill.CUSTOMER_SERVICE],
            'available_hours': list(range(6, 23))  # 6 AM - 10 PM
        },
        {
            'id': 'EMP002',
            'name': 'Bob Smith',
            'rate': 16.0,
            'max_daily': 8,
            'max_weekly': 40,
            'skills': [Skill.STOCK, Skill.CUSTOMER_SERVICE],
            'available_hours': list(range(6, 23))
        },
        {
            'id': 'EMP003',
            'name': 'Carol Davis',
            'rate': 20.0,
            'max_daily': 8,
            'max_weekly': 40,
            'skills': [Skill.MANAGER, Skill.CASHIER],
            'available_hours': list(range(6, 23))
        },
        # Part-time employees
        {
            'id': 'EMP004',
            'name': 'David Martinez',
            'rate': 14.0,
            'max_daily': 4,
            'max_weekly': 20,
            'skills': [Skill.STOCK, Skill.CASHIER],
            'available_hours': list(range(15, 23))  # Afternoon/evening only
        },
        {
            'id': 'EMP005',
            'name': 'Emma Wilson',
            'rate': 15.0,
            'max_daily': 6,
            'max_weekly': 30,
            'skills': [Skill.CUSTOMER_SERVICE, Skill.CASHIER],
            'available_hours': [6, 7, 8, 9, 10, 11] + list(range(17, 23))  # Morning and evening
        },
        {
            'id': 'EMP006',
            'name': 'Frank Brown',
            'rate': 15.0,
            'max_daily': 5,
            'max_weekly': 25,
            'skills': [Skill.STOCK],
            'available_hours': [6, 7, 8, 9, 10, 11, 12] + list(range(20, 23))
        },
    ]
    
    for emp_data in employees:
        emp = Employee(
            employee_id=emp_data['id'],
            name=emp_data['name'],
            hourly_rate=emp_data['rate'],
            max_hours_per_day=emp_data['max_daily'],
            max_hours_per_week=emp_data['max_weekly']
        )
        
        # Set availability
        for hour in range(6, 23):
            emp.set_availability(hour, hour in emp_data['available_hours'])
        
        # Add skills
        for skill in emp_data['skills']:
            emp.add_skill(skill)
        
        db.add_employee(emp)
    
    return db


def create_sample_demand() -> DemandProfile:
    """Create a realistic sample demand profile."""
    demand = DemandProfile()
    
    # Realistic retail demand pattern
    hourly_demand = {
        6: 5,      # 6 AM - Light opening traffic
        7: 10,     # 7 AM - Early birds
        8: 15,     # 8 AM - Pre-work shoppers
        9: 20,     # 9 AM - Regular shoppers
        10: 25,    # 10 AM - Mid-morning peak
        11: 30,    # 11 AM - Pre-lunch rush
        12: 35,    # 12 PM - Lunch rush (PEAK)
        13: 32,    # 1 PM - Post-lunch
        14: 25,    # 2 PM - Afternoon slower
        15: 20,    # 3 PM - Afternoon lull
        16: 18,    # 4 PM - Before work hours
        17: 25,    # 5 PM - After work begins
        18: 40,    # 6 PM - Evening peak (PEAK)
        19: 45,    # 7 PM - Evening peak (PEAK)
        20: 35,    # 8 PM - Winding down
        21: 20,    # 9 PM - Late shoppers
        22: 8,     # 10 PM - Closing time
    }
    
    demand.hourly_demand = hourly_demand
    
    # Auto-calculate min staff based on demand
    for hour, customers in hourly_demand.items():
        min_staff = max(1, (customers // 15) + 1)
        demand.set_min_staff(hour, min_staff)
    
    return demand


def create_sample_store_params() -> StoreParameters:
    """Create sample store parameters."""
    return StoreParameters(
        store_name="Downtown Store",
        opening_hour=6,
        closing_hour=22,
        daily_budget=800.0,  # Realistic for retail with 3-5 employees/shift
        weekly_budget=5000.0,
        allow_overtime=False
    )


def print_sample_summary():
    """Print summary of sample data."""
    print("=" * 60)
    print("SAMPLE RETAIL STAFF SCHEDULER DATA")
    print("=" * 60)
    
    # Employees
    emp_db = create_sample_employees()
    print(f"\nEmployees ({len(emp_db.get_all_employees())} total):")
    for emp in emp_db.get_all_employees():
        available_hours = [h for h in range(6, 23) if emp.is_available(h)]
        print(f"  {emp.name:20} ${emp.hourly_rate:5.2f}/hr "
              f"Max {emp.max_hours_per_day}h/day "
              f"Available: {len(available_hours)}/17 hours")
    
    # Demand
    demand = create_sample_demand()
    print(f"\nDemand Profile:")
    stats = demand.get_statistics()
    print(f"  Total Daily Customers: {stats['total_demand']}")
    print(f"  Average per Hour: {stats['avg_demand']:.1f}")
    print(f"  Peak Demand: {stats['peak_demand']}")
    print(f"  Peak Hours: {demand.get_peak_hours()}")
    
    # Store
    store = create_sample_store_params()
    print(f"\nStore Parameters:")
    print(f"  Hours: {store.opening_hour}:00 - {store.closing_hour}:00 "
          f"({store.get_daily_hours()} hours)")
    print(f"  Daily Budget: ${store.daily_budget:.2f}")
    print(f"  Weekly Budget: ${store.weekly_budget:.2f}")
    
    print("\n" + "=" * 60)


if __name__ == '__main__':
    print_sample_summary()
