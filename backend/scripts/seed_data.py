"""
Seed script for populating lookup tables (roles and departments).

"""

import sys
from pathlib import Path

# Add the backend directory to Python path so we can import app
sys.path.append(str(Path(__file__).parent.parent))

from app import create_app
from app.extensions import db
from app.models import Role, Department


# --- Configuration ---

# Category to Department Name mapping
# This is the single source of truth for the mapping.
# Application code can import this dict if needed.
CATEGORY_TO_DEPARTMENT = {
    'ROADS': 'Roads Maintenance',
    'WASTE': 'Waste Management',
    'PARKS': 'Parks and Recreation',
    'STREET_LIGHTING': 'Street Lighting',
    'BUILDINGS': 'Buildings Maintenance',
    'OTHER': 'Other Services',
}

# Role names
ROLE_NAMES = ['RESIDENT', 'SUPPORT_OFFICER', 'ADMIN']

# Valid enum values (can be imported by application code)
VALID_CATEGORIES = list(CATEGORY_TO_DEPARTMENT.keys())
VALID_PRIORITIES = ['LOW', 'MEDIUM', 'HIGH', 'URGENT']
VALID_STATUSES = ['SUBMITTED', 'UNDER_REVIEW', 'IN_PROGRESS', 'RESOLVED', 'CLOSED']


# --- Seed Functions ---

def seed_roles():
    """
    Seed the roles table with RESIDENT, SUPPORT_OFFICER, ADMIN.
    Idempotent: checks if each role exists before inserting.
    """
    created_count = 0
    skipped_count = 0
    
    for role_name in ROLE_NAMES:
        # Check if the role already exists
        existing = Role.query.filter_by(name=role_name).first()
        
        if existing:
            print(f"[SKIP] Role '{role_name}' already exists (ID: {existing.role_id})")
            skipped_count += 1
        else:
            # Create and add the new role
            role = Role(name=role_name)
            db.session.add(role)
            print(f"[CREATE] Role: '{role_name}'")
            created_count += 1
    
    print(f"\nRoles: {created_count} created, {skipped_count} skipped.")
    return created_count, skipped_count


def seed_departments():
    """
    Seed the departments table using the category mapping.
    Idempotent: checks if each department exists before inserting.
    """
    # Get unique department names from the mapping
    departments = list(CATEGORY_TO_DEPARTMENT.values())
    created_count = 0
    skipped_count = 0
    
    for dept_name in departments:
        # Check if the department already exists
        existing = Department.query.filter_by(name=dept_name).first()
        
        if existing:
            print(f"[SKIP] Department '{dept_name}' already exists (ID: {existing.department_id})")
            skipped_count += 1
        else:
            # Create and add the new department
            department = Department(name=dept_name)
            db.session.add(department)
            print(f"[CREATE] Department: '{dept_name}'")
            created_count += 1
    
    print(f"\nDepartments: {created_count} created, {skipped_count} skipped.")
    return created_count, skipped_count


def print_summary():
    """Print a summary of what's in the database after seeding."""
    print("\n" + "=" * 60)
    print("SEED COMPLETE - Current Database State")
    print("=" * 60)
    
    # Show all roles
    roles = Role.query.all()
    print("\nRoles:")
    if roles:
        for role in roles:
            print(f"  - ID: {role.role_id}, Name: {role.name}")
    else:
        print("  WARNING: No roles found!")
    
    # Show all departments
    departments = Department.query.all()
    print("\nDepartments:")
    if departments:
        for dept in departments:
            print(f"  - ID: {dept.department_id}, Name: {dept.name}")
    else:
        print("  WARNING: No departments found!")
    
    # Show the category-to-department mapping
    print("\nCategory -> Department Mapping:")
    all_found = True
    for category, dept_name in CATEGORY_TO_DEPARTMENT.items():
        dept = Department.query.filter_by(name=dept_name).first()
        if dept:
            dept_id = dept.department_id
            status = "[OK]"
        else:
            dept_id = "NOT FOUND"
            status = "[MISSING]"
            all_found = False
        print(f"  {status} {category} -> {dept_name} (ID: {dept_id})")
    
    # Verification summary
    print("\nVerification:")
    if all_found and roles:
        print("  SUCCESS: All roles and departments exist. Ready for application use.")
    elif all_found and not roles:
        print("  WARNING: Departments exist but roles are missing.")
    elif not all_found and roles:
        print("  WARNING: Roles exist but some departments are missing.")
    else:
        print("  ERROR: Both roles and departments are missing. Something went wrong.")
    
    print("\n" + "=" * 60)


def main():
    """Main entry point for the seed script."""
    print("\nStarting database seed...\n")
    
    # Create the Flask app
    app = create_app()
    
    # Run seeding inside the app context
    with app.app_context():
        try:
            # Seed the tables
            seed_roles()
            seed_departments()
            
            # Commit all changes at once
            db.session.commit()
            print("\nAll changes committed successfully!")
            
            # Print summary
            print_summary()
            
        except Exception as e:
            # Rollback on any error
            db.session.rollback()
            print(f"\nERROR: {e}")
            print("Rolled back all changes.")
            sys.exit(1)


if __name__ == '__main__':
    main()