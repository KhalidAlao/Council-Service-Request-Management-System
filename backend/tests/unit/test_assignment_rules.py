"""
Unit tests for assignment permission logic.
Tests the pure function can_assign_officer() against the single source of truth.
"""

import pytest
from unittest.mock import Mock
from app.utils.status_helpers import can_assign_officer


class TestAssignmentRules:
    """Test the assignment permission matrix."""

    def test_admin_assign_anyone_true(self):
        """Admin can assign any request to any officer, regardless of state."""
        # Admin assigning to any target
        result, msg = can_assign_officer(
            current_user_id=1,
            current_user_role='ADMIN',
            request_obj=Mock(assigned_officer_id=None),
            target_user_id=5
        )
        assert result is True
        assert msg is None

        # Admin assigning when request is already assigned to someone else
        result, msg = can_assign_officer(
            current_user_id=1,
            current_user_role='ADMIN',
            request_obj=Mock(assigned_officer_id=3),
            target_user_id=5
        )
        assert result is True
        assert msg is None

    def test_officer_self_assign_unassigned_true(self):
        """Officer can self-assign to an unassigned request."""
        result, msg = can_assign_officer(
            current_user_id=3,
            current_user_role='SUPPORT_OFFICER',
            request_obj=Mock(assigned_officer_id=None),
            target_user_id=3
        )
        assert result is True
        assert msg is None

    def test_officer_self_assign_already_assigned_to_self_false(self):
        """Officer trying to self-assign when already assigned to them should fail."""
        result, msg = can_assign_officer(
            current_user_id=3,
            current_user_role='SUPPORT_OFFICER',
            request_obj=Mock(assigned_officer_id=3),
            target_user_id=3
        )
        assert result is False
        assert msg == "You are already assigned to this request"

    def test_officer_self_assign_already_assigned_to_other_false(self):
        """Officer trying to self-assign when assigned to someone else should fail."""
        result, msg = can_assign_officer(
            current_user_id=3,
            current_user_role='SUPPORT_OFFICER',
            request_obj=Mock(assigned_officer_id=5),
            target_user_id=3
        )
        assert result is False
        assert msg == "This request is already assigned to someone else"

    def test_officer_assign_other_to_unassigned_false(self):
        """Officer cannot assign someone else to an unassigned request."""
        result, msg = can_assign_officer(
            current_user_id=3,
            current_user_role='SUPPORT_OFFICER',
            request_obj=Mock(assigned_officer_id=None),
            target_user_id=5
        )
        assert result is False
        assert msg == "You can only self-assign unassigned requests or hand off requests assigned to you"

    def test_officer_handoff_true(self):
        """Officer can hand off a request currently assigned to them."""
        result, msg = can_assign_officer(
            current_user_id=3,
            current_user_role='SUPPORT_OFFICER',
            request_obj=Mock(assigned_officer_id=3),
            target_user_id=5
        )
        assert result is True
        assert msg is None

    def test_uninvolved_officer_assign_false(self):
        """Officer with no relationship to the request cannot assign."""
        # Request assigned to someone else, officer tries to assign someone else
        result, msg = can_assign_officer(
            current_user_id=4,
            current_user_role='SUPPORT_OFFICER',
            request_obj=Mock(assigned_officer_id=3),
            target_user_id=5
        )
        assert result is False
        assert msg == "You can only self-assign unassigned requests or hand off requests assigned to you"

    def test_resident_assign_false(self):
        """Resident cannot assign any officer."""
        result, msg = can_assign_officer(
            current_user_id=2,
            current_user_role='RESIDENT',
            request_obj=Mock(assigned_officer_id=None),
            target_user_id=3
        )
        assert result is False
        assert msg == "You do not have permission to assign officers"

    def test_resident_assign_even_with_permission_false(self):
        """Resident cannot assign even if they have a valid target."""
        result, msg = can_assign_officer(
            current_user_id=2,
            current_user_role='RESIDENT',
            request_obj=Mock(assigned_officer_id=3),
            target_user_id=3
        )
        assert result is False
        assert msg == "You do not have permission to assign officers"