"""
Seed script for populating lookup tables (roles and departments).


The category↔department mapping is imported from app.constants,
which is the single source of truth for the application.
"""

import sys
from pathlib import Path

# Add the backend directory to Python path so we can import app
sys.path.append(str(Path(__file__).parent.parent))

from app import create_app
from app.extensions import db
from app.models import Role, Department
from app.constants import CATEGORY_TO_DEPARTMENT, ROLE_NAMES  


def seed_roles():
    """Seed the roles table."""
    created_count = 0
    skipped_count = 0
    
    for role_name in ROLE_NAMES:
        existing = Role.query.filter_by(name=role_name).first()
        
        if existing:
            print(f"[SKIP] Role '{role_name}' already exists (ID: {existing.role_id})")
            skipped_count += 1
        else:
            role = Role(name=role_name)
            db.session.add(role)
            print(f"[CREATE] Role: '{role_name}'")
            created_count += 1
    
    print(f"\nRoles: {created_count} created, {skipped_count} skipped.")
    return created_count, skipped_count


def seed_departments():
    """Seed the departments table using the category mapping."""
    # Get departments from imported constants
    departments = list(CATEGORY_TO_DEPARTMENT.values())
    created_count = 0
    skipped_count = 0
    
    for dept_name in departments:
        existing = Department.query.filter_by(name=dept_name).first()
        
        if existing:
            print(f"[SKIP] Department '{dept_name}' already exists (ID: {existing.department_id})")
            skipped_count += 1
        else:
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
    
    roles = Role.query.all()
    print("\nRoles:")
    for role in roles:
        print(f"  - ID: {role.role_id}, Name: {role.name}")
    
    departments = Department.query.all()
    print("\nDepartments:")
    for dept in departments:
        print(f"  - ID: {dept.department_id}, Name: {dept.name}")
    
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
    
    print("\nVerification:")
    if all_found and roles:
        print("  SUCCESS: All roles and departments exist. Ready for application use.")
    else:
        print("  WARNING: Some data is missing. Please check the output above.")
    
    print("\n" + "=" * 60)


def main():
    """Main entry point."""
    print("\nStarting database seed...\n")
    
    app = create_app()
    
    with app.app_context():
        try:
            seed_roles()
            seed_departments()
            db.session.commit()
            print("\nAll changes committed successfully!")
            print_summary()
        except Exception as e:
            db.session.rollback()
            print(f"\nERROR: {e}")
            print("Rolled back all changes.")
            sys.exit(1)


if __name__ == '__main__':
    main()