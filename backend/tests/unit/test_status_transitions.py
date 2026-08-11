"""
Unit tests for status transition logic.
Tests the pure function is_valid_transition() against the single source of truth.
"""

import pytest
from app.utils.status_helpers import validate_transition
from app.constants import STATUS_TRANSITIONS, VALID_STATUSES


class TestStatusTransitions:
    """Test the status transition state machine."""

    def test_valid_transitions(self):
        """All valid transitions should return True."""
        valid_pairs = [
            ('SUBMITTED', 'UNDER_REVIEW'),
            ('SUBMITTED', 'DUPLICATE'),
            ('SUBMITTED', 'REJECTED'),
            ('UNDER_REVIEW', 'IN_PROGRESS'),
            ('UNDER_REVIEW', 'DUPLICATE'),
            ('UNDER_REVIEW', 'REJECTED'),
            ('IN_PROGRESS', 'RESOLVED'),
            ('RESOLVED', 'CLOSED'),
        ]
        
        for current, target in valid_pairs:
            is_valid, error = validate_transition(current, target)
            assert is_valid is True, f"Expected '{current}' -> '{target}' to be valid, got error: {error}"

    def test_invalid_transitions_skip_states(self):
        """Skipping states should be invalid."""
        invalid_pairs = [
            ('SUBMITTED', 'IN_PROGRESS'),
            ('SUBMITTED', 'RESOLVED'),
            ('SUBMITTED', 'CLOSED'),
            ('UNDER_REVIEW', 'RESOLVED'),
            ('UNDER_REVIEW', 'CLOSED'),
            ('IN_PROGRESS', 'CLOSED'),
            ('IN_PROGRESS', 'DUPLICATE'),
            ('IN_PROGRESS', 'REJECTED'),
        ]
        
        for current, target in invalid_pairs:
            is_valid, error = validate_transition(current, target)
            assert is_valid is False, f"Expected '{current}' -> '{target}' to be invalid"
            assert 'Invalid status transition' in error

    def test_invalid_transitions_backwards(self):
        """Going backwards should be invalid."""
        backward_pairs = [
            ('UNDER_REVIEW', 'SUBMITTED'),
            ('IN_PROGRESS', 'UNDER_REVIEW'),
            ('RESOLVED', 'IN_PROGRESS'),
            ('CLOSED', 'RESOLVED'),
        ]
        
        for current, target in backward_pairs:
            is_valid, error = validate_transition(current, target)
            assert is_valid is False, f"Expected '{current}' -> '{target}' (backwards) to be invalid"
            assert 'Invalid status transition' in error

    def test_terminal_states_allow_nothing(self):
        """Terminal states (CLOSED, DUPLICATE, REJECTED) should allow no transitions."""
        terminal_states = ['CLOSED', 'DUPLICATE', 'REJECTED']
        
        for terminal in terminal_states:
            for target in VALID_STATUSES:
                if target == terminal:
                    continue  # Self-transition is also invalid
                is_valid, error = validate_transition(terminal, target)
                assert is_valid is False, f"Expected '{terminal}' -> '{target}' to be invalid"
                assert 'Invalid status transition' in error

    def test_self_transition_invalid(self):
        """Changing to the same status should be invalid."""
        for status in VALID_STATUSES:
            is_valid, error = validate_transition(status, status)
            assert is_valid is False, f"Expected '{status}' -> '{status}' (self) to be invalid"

    def test_unknown_status_handled_gracefully(self):
        """Unknown current status should result in no valid transitions."""
        is_valid, error = validate_transition('UNKNOWN_STATUS', 'SUBMITTED')
        assert is_valid is False
        assert 'Invalid status transition' in error

    def test_transition_map_complete(self):
        """Ensure all valid statuses are covered in the transition map."""
        # All statuses should appear as keys in the transition map
        for status in VALID_STATUSES:
            assert status in STATUS_TRANSITIONS, f"Status '{status}' missing from transition map"
        
        # All target statuses in the transition map should be valid statuses
        for current, allowed_set in STATUS_TRANSITIONS.items():
            for target in allowed_set:
                assert target in VALID_STATUSES, f"Invalid target '{target}' in transition map for '{current}'"