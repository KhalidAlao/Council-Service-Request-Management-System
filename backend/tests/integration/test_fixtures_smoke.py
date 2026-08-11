"""
Smoke tests to verify fixture chain works.
These can be deleted once real tests are written.
"""

import pytest


def test_admin_fixture_works(admin_headers):
    """Smoke test to verify admin fixture chain works."""
    assert 'Authorization' in admin_headers
    assert admin_headers['Authorization'].startswith('Bearer ')


def test_officer_fixture_works(officer_headers):
    """Smoke test for officer fixture."""
    assert 'Authorization' in officer_headers
    assert officer_headers['Authorization'].startswith('Bearer ')


def test_resident_fixture_works(resident_headers):
    """Smoke test for resident fixture."""
    assert 'Authorization' in resident_headers
    assert resident_headers['Authorization'].startswith('Bearer ')


def test_roles_created(roles):
    """Verify all three roles were created."""
    assert roles['ADMIN'] is not None
    assert roles['SUPPORT_OFFICER'] is not None
    assert roles['RESIDENT'] is not None
    assert roles['ADMIN'].name == 'ADMIN'
    assert roles['SUPPORT_OFFICER'].name == 'SUPPORT_OFFICER'
    assert roles['RESIDENT'].name == 'RESIDENT'