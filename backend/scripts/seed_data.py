"""
Seed script for populating lookup tables (roles, departments, and admin user).

The category↔department mapping is imported from app.constants,
which is the single source of truth for the application.
"""

import sys
import os
from pathlib import Path

# Add the backend directory to Python path so we can import app
sys.path.append(str(Path(__file__).parent.parent))

from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db
from app.models import Role, Department, User
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


def seed_admin_user():
    """
    Create a default admin user for testing.
    Credentials can be overridden via environment variables.
    
    ⚠️ SECURITY WARNING: These credentials are for LOCAL DEVELOPMENT ONLY.
    In any production or staging environment, these MUST be overridden
    via environment variables (ADMIN_EMAIL, ADMIN_PASSWORD).
    """
    admin_email = os.getenv('ADMIN_EMAIL', 'admin@council.gov')
    admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
    
    # Check if admin already exists
    existing = User.query.filter_by(email=admin_email).first()
    if existing:
        print(f"[SKIP] Admin user '{admin_email}' already exists (ID: {existing.user_id})")
        return
    
    # Get the ADMIN role
    admin_role = Role.query.filter_by(name='ADMIN').first()
    if not admin_role:
        print("[ERROR] ADMIN role not found. Run seed_roles() first.")
        return
    
    password_hash = generate_password_hash(admin_password, method='pbkdf2:sha256')
    
    # Create admin user
    admin_user = User(
        full_name='System Administrator',
        email=admin_email,
        password_hash=password_hash,
        role_id=admin_role.role_id,
        is_active=True
    )
    db.session.add(admin_user)
    print(f"[CREATE] Admin user: '{admin_email}' (password: {admin_password})")


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
    
    users = User.query.all()
    print("\nUsers:")
    if users:
        for user in users:
            role_name = user.role.name if user.role else "NO ROLE"
            print(f"  - ID: {user.user_id}, Name: {user.full_name}, Email: {user.email}, Role: {role_name}")
    else:
        print("  No users found!")
    
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
        print("  ADMIN USER: admin@council.gov / admin123 (if not overridden)")
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
            seed_admin_user()  
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