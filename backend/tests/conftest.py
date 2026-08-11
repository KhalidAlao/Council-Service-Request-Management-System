import pytest
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash

from app import create_app
from app.config import TestConfig
from app.extensions import db
from app.models import Role, User, Department, ServiceRequest


# ===== App and Client Fixtures =====

@pytest.fixture(scope='function')
def app():
    """Create a Flask app with test configuration and in-memory database."""
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """Flask test client."""
    return app.test_client()


# ===== Roles Fixture =====

@pytest.fixture(scope='function')
def roles(app):
    """Create all three roles once per test."""
    roles_data = ['ADMIN', 'SUPPORT_OFFICER', 'RESIDENT']
    created_roles = {}
    for role_name in roles_data:
        role = Role(name=role_name)
        db.session.add(role)
        created_roles[role_name] = role
    db.session.commit()
    return {
        'ADMIN': Role.query.filter_by(name='ADMIN').first(),
        'SUPPORT_OFFICER': Role.query.filter_by(name='SUPPORT_OFFICER').first(),
        'RESIDENT': Role.query.filter_by(name='RESIDENT').first()
    }


# ===== Department Fixture =====

@pytest.fixture(scope='function')
def department(app):
    """Create a test department with a name that matches the ROADS category."""
    dept = Department(name='Roads Maintenance')  
    db.session.add(dept)
    db.session.commit()
    return dept


# ===== User Fixtures =====

@pytest.fixture(scope='function')
def admin_user(roles):
    """Create an admin user."""
    role = roles['ADMIN']
    user = User(
        full_name='Test Admin',
        email='admin@test.com',
        password_hash=generate_password_hash('admin123', method='pbkdf2:sha256'),
        role_id=role.role_id,
        is_active=True
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture(scope='function')
def officer_user(roles, department):
    """Create a support officer user with department."""
    role = roles['SUPPORT_OFFICER']
    user = User(
        full_name='Test Officer',
        email='officer@test.com',
        password_hash=generate_password_hash('officer123', method='pbkdf2:sha256'),
        role_id=role.role_id,
        department_id=department.department_id,
        is_active=True
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture(scope='function')
def resident_user(roles):
    """Create a resident user."""
    role = roles['RESIDENT']
    user = User(
        full_name='Test Resident',
        email='resident@test.com',
        password_hash=generate_password_hash('resident123', method='pbkdf2:sha256'),
        role_id=role.role_id,
        is_active=True
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture(scope='function')
def second_officer_user(roles, department):
    """Create a second support officer for handoff tests."""
    role = roles['SUPPORT_OFFICER']
    user = User(
        full_name='Second Test Officer',
        email='officer2@test.com',
        password_hash=generate_password_hash('officer2123', method='pbkdf2:sha256'),
        role_id=role.role_id,
        department_id=department.department_id,
        is_active=True
    )
    db.session.add(user)
    db.session.commit()
    return user


# ===== Auth Header Fixtures =====

@pytest.fixture(scope='function')
def admin_headers(admin_user):
    """Return Authorization headers for admin user."""
    token = create_access_token(
        identity=str(admin_user.user_id),
        additional_claims={'role': 'ADMIN'}
    )
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture(scope='function')
def officer_headers(officer_user):
    """Return Authorization headers for officer user."""
    token = create_access_token(
        identity=str(officer_user.user_id),
        additional_claims={'role': 'SUPPORT_OFFICER'}
    )
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture(scope='function')
def resident_headers(resident_user):
    """Return Authorization headers for resident user."""
    token = create_access_token(
        identity=str(resident_user.user_id),
        additional_claims={'role': 'RESIDENT'}
    )
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture(scope='function')
def second_officer_headers(second_officer_user):
    """Return Authorization headers for second officer user."""
    token = create_access_token(
        identity=str(second_officer_user.user_id),
        additional_claims={'role': 'SUPPORT_OFFICER'}
    )
    return {'Authorization': f'Bearer {token}'}


# ===== Request Fixtures =====

@pytest.fixture(scope='function')
def sample_request(app, admin_user):
    """Create a simple SUBMITTED request for testing."""
    request_obj = ServiceRequest(
        reference_number='SR-2026-TEST9999',
        title='Integration Test Request',
        description='Used for status endpoint tests',
        location='Test Location',
        category='ROADS',
        priority='MEDIUM',
        status='SUBMITTED',
        submitted_by_user_id=admin_user.user_id
    )
    db.session.add(request_obj)
    db.session.commit()
    return request_obj


@pytest.fixture(scope='function')
def unassigned_request(app, admin_user):
    """Create an unassigned request (assigned_officer_id = NULL)."""
    request_obj = ServiceRequest(
        reference_number='SR-2026-UNASSIGNED',
        title='Unassigned Test Request',
        description='This request has no officer assigned',
        location='Unassigned Street',
        category='ROADS',
        priority='MEDIUM',
        status='SUBMITTED',
        submitted_by_user_id=admin_user.user_id
    )
    db.session.add(request_obj)
    db.session.commit()
    return request_obj


@pytest.fixture(scope='function')
def assigned_request(app, admin_user, officer_user):
    """Create a request assigned to officer_user."""
    request_obj = ServiceRequest(
        reference_number='SR-2026-ASSIGNED',
        title='Assigned Test Request',
        description='This request is assigned to an officer',
        location='Assigned Street',
        category='WASTE',
        priority='MEDIUM',
        status='SUBMITTED',
        submitted_by_user_id=admin_user.user_id,
        assigned_officer_id=officer_user.user_id
    )
    db.session.add(request_obj)
    db.session.commit()
    return request_obj


@pytest.fixture(scope='function')
def resident_request(app, resident_user):
    """Create a request submitted by the resident."""
    request_obj = ServiceRequest(
        reference_number='SR-2026-RESIDENT',
        title='Resident Own Request',
        description='This request belongs to the resident',
        location='Resident Street',
        category='WASTE',
        priority='MEDIUM',
        status='SUBMITTED',
        submitted_by_user_id=resident_user.user_id
    )
    db.session.add(request_obj)
    db.session.commit()
    return request_obj