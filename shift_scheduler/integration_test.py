"""
Full integration test: Load example and verify app behavior
"""
import sys
import pickle
from models.employee import EmployeeManager
from models.demand import DemandProfile
from views.employee_tab import EmployeeTab
from views.demand_tab import DemandTab

print("=" * 70)
print("INTEGRATION TEST: Load Example Project and Verify App Behavior")
print("=" * 70)

# Step 1: Load the .ssp file
print("\n[1/5] Loading example project file...")
try:
    with open('brew_haven_example.ssp', 'rb') as f:
        data = pickle.load(f)
    print("✓ File loaded successfully")
except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)

# Step 2: Create EmployeeManager and load data
print("\n[2/5] Loading employees into EmployeeManager...")
try:
    em = EmployeeManager()
    for emp_data in data.get('employees', []):
        em.add_employee(**emp_data)
    print(f"✓ Loaded {len(em.employees)} employees")
    for i, emp in enumerate(em.employees, 1):
        print(f"   {i}. {emp.name} (${emp.hourly_rate}/hr, {len(emp.availability)} hours available)")
except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)

# Step 3: Create DemandProfile and load data
print("\n[3/5] Loading demand profile into DemandProfile...")
try:
    dp = DemandProfile.from_dict(data.get('demand', {}))
    print(f"✓ Demand profile loaded")
    print(f"   Store hours: {dp.store_open_hour} AM - {dp.store_close_hour} (24h format)")
    print(f"   Operating hours: {dp.store_close_hour - dp.store_open_hour} hours")
    print(f"   Hourly demands configured: {len(dp.hourly_demand)} hours")
    print(f"   Min staff per hour: {dp.min_staff_per_hour}")
    print(f"   Staff/customer ratio: {dp.staff_per_customer_ratio}")
    
    # Show sample demand
    print(f"\n   Sample hourly demand:")
    for hour in sorted(list(dp.hourly_demand.keys())[:3]):
        demand = dp.get_demand(hour)
        print(f"     {hour}:00 - {demand} customers")
    print(f"     ...")
    for hour in sorted(list(dp.hourly_demand.keys())[-3:]):
        demand = dp.get_demand(hour)
        print(f"     {hour}:00 - {demand} customers")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 4: Verify tab refresh capability
print("\n[4/5] Verifying tab refresh methods...")
try:
    # Check if refresh methods exist (without actually creating GUI)
    has_refresh = hasattr(EmployeeTab, 'refresh_table')
    has_load = hasattr(DemandTab, 'load_demand_data')
    
    print(f"✓ EmployeeTab.refresh_table exists: {has_refresh}")
    print(f"✓ DemandTab.load_demand_data exists: {has_load}")
    
    if has_refresh and has_load:
        print("\n✓ Both refresh methods available for loading new data")
    else:
        print("\n✗ Missing refresh methods!")
        sys.exit(1)
except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)

# Step 5: Summary
print("\n" + "=" * 70)
print("✅ INTEGRATION TEST PASSED")
print("=" * 70)
print("\nExpected app behavior when loading example:")
print("  1. Employee Tab → Shows 8 employees with their details")
print("  2. Demand Tab → Shows hourly demand sliders from 6 AM to 7 PM")
print("  3. Schedule Tab → Ready to run optimization")
print("  4. Results Tab → Empty until optimization is run")
print("\nTo test in the actual app:")
print("  1. python -3.13 main.py")
print("  2. File → Ouvrir → brew_haven_example.ssp")
print("  3. Check Employés tab - should show 8 employees")
print("  4. Check Demande tab - should show demand profile with sliders")
print("  5. Click Schedule tab → Lancer l'optimisation")
print("  6. Check Results tab for the generated schedule")
