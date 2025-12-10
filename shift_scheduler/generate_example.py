"""
Generate Example Project: Brew Haven Coffee Shop

This script creates sample data for the Shift Scheduler app.
Run this to auto-populate the app with example data.

Usage:
    python generate_example.py
"""

import pickle
import os

def create_brew_haven_project():
    """Create Brew Haven Coffee Shop example project"""
    
    # Define employees (without ID - EmployeeManager will assign them)
    employees = [
        {
            'name': 'Sarah Johnson',
            'hourly_rate': 22.00,
            'max_hours_per_day': 8,
            'max_hours_per_week': 40,
            'availability': list(range(6, 18)),  # 6 AM - 6 PM
            'skills': ['Manager', 'Barista', 'Customer Service']
        },
        {
            'name': 'Mike Chen',
            'hourly_rate': 18.00,
            'max_hours_per_day': 8,
            'max_hours_per_week': 40,
            'availability': list(range(6, 20)),  # 6 AM - 8 PM
            'skills': ['Barista', 'Training', 'Customer Service']
        },
        {
            'name': 'Jessica Martinez',
            'hourly_rate': 16.00,
            'max_hours_per_day': 8,
            'max_hours_per_week': 38,
            'availability': list(range(10, 20)),  # 10 AM - 8 PM
            'skills': ['Barista', 'POS', 'Customer Service']
        },
        {
            'name': 'Tom Wilson',
            'hourly_rate': 15.00,
            'max_hours_per_day': 6,
            'max_hours_per_week': 30,
            'availability': list(range(8, 18)),  # 8 AM - 6 PM
            'skills': ['Barista', 'Cleaning', 'Stocking']
        },
        {
            'name': 'Emma Davis',
            'hourly_rate': 14.00,
            'max_hours_per_day': 5,
            'max_hours_per_week': 20,
            'availability': list(range(11, 17)),  # 11 AM - 5 PM
            'skills': ['Barista', 'Customer Service']
        },
        {
            'name': 'Alex Rodriguez',
            'hourly_rate': 13.50,
            'max_hours_per_day': 4,
            'max_hours_per_week': 16,
            'availability': list(range(12, 18)),  # 12 PM - 6 PM
            'skills': ['Cashier', 'Stocking', 'Customer Service']
        },
        {
            'name': 'Lisa Anderson',
            'hourly_rate': 14.50,
            'max_hours_per_day': 6,
            'max_hours_per_week': 24,
            'availability': list(range(16, 20)),  # 4 PM - 8 PM
            'skills': ['Barista', 'Cashier', 'Cleaning']
        },
        {
            'name': 'David Kim',
            'hourly_rate': 13.50,
            'max_hours_per_day': 5,
            'max_hours_per_week': 18,
            'availability': list(range(12, 20)),  # 12 PM - 8 PM
            'skills': ['Barista', 'Customer Service', 'Stocking']
        }
    ]
    
    # Define demand profile (format matches DemandProfile class)
    demand = {
        'store_open_hour': 6,
        'store_close_hour': 20,
        'staff_per_customer_ratio': 0.05,
        'min_staff_per_hour': 2,  # Minimum 2 staff at any time
        'hourly_demand': {
            6: 10,   # 6 AM - early birds
            7: 40,   # 7 AM - morning rush
            8: 80,   # 8 AM - heavy
            9: 90,   # 9 AM - peak morning
            10: 70,  # 10 AM
            11: 80,  # 11 AM - lunch prep
            12: 120, # 12 PM - lunch peak
            13: 110, # 1 PM - lunch continues
            14: 75,  # 2 PM
            15: 60,  # 3 PM
            16: 65,  # 4 PM
            17: 85,  # 5 PM
            18: 95,  # 6 PM - evening peak
            19: 80,  # 7 PM
        }
    }
    
    # Create project data
    project_data = {
        'name': 'Brew Haven Coffee Shop',
        'description': 'Example scheduling project for a coffee shop',
        'employees': employees,
        'demand': demand,
        'metadata': {
            'created': '2025-12-08',
            'version': '1.0',
            'notes': 'Example: 8 employees, 14-hour store, double peak demand'
        }
    }
    
    return project_data

def save_project(filename='brew_haven_example.ssp'):
    """Save project to file"""
    
    project = create_brew_haven_project()
    
    try:
        with open(filename, 'wb') as f:
            pickle.dump(project, f)
        print(f"✓ Project saved: {filename}")
        print(f"  Employees: {len(project['employees'])}")
        print(f"  Store hours: {project['demand']['store_open_hour']} AM - {project['demand']['store_close_hour']} (24h)")
        print(f"  Demand profile: 10-120 customers/hour")
        print(f"\nTo load in app:")
        print(f"  1. Launch: py -3.13 main.py")
        print(f"  2. File → Ouvrir → Select {filename}")
        print(f"  3. All employees and demand will be loaded!")
        return True
    except Exception as e:
        print(f"✗ Error saving project: {e}")
        return False

def display_project_info():
    """Display project information"""
    
    project = create_brew_haven_project()
    
    print("=" * 60)
    print("BREW HAVEN COFFEE SHOP - EXAMPLE PROJECT")
    print("=" * 60)
    
    print("\nEMPLOYEES:")
    print("-" * 60)
    for i, emp in enumerate(project['employees'], 1):
        print(f"{i}. {emp['name']:20} | ${emp['hourly_rate']:6.2f}/hr | {emp['max_hours_per_day']}-{emp['max_hours_per_week']} hrs")
    
    print("\nSTORE HOURS:")
    print("-" * 60)
    print(f"Open: {project['demand']['store_open_hour']} AM")
    print(f"Close: {project['demand']['store_close_hour']} PM (8 PM)")
    print(f"Operating hours: 14 hours")
    
    print("\nDEMAND PROFILE:")
    print("-" * 60)
    print("Hour | Customers")
    print("-" * 60)
    for hour in sorted(project['demand']['hourly_demand'].keys()):
        customers = project['demand']['hourly_demand'][hour]
        hour_label = f"{hour}:00"
        print(f"{hour_label:5} | {customers:9}")
    
    print("\nEXPECTED RESULTS:")
    print("-" * 60)
    print("Total daily cost: ~$850-900")
    print("Total staff hours: ~50-55 hours")
    print("Peak coverage: 3-4 staff (12-2 PM)")
    print("Min coverage: 1 staff (6 AM)")
    
    print("\n" + "=" * 60)

if __name__ == '__main__':
    # Display info
    display_project_info()
    
    # Save project
    print("\nSaving project file...")
    if save_project():
        print("\n✓ Ready to use! Load 'brew_haven_example.ssp' in the app")
