"""
Test helpers — pure functions extracted for unit testing.
"""

# State transition map: current_status → allowed next statuses
STATUS_TRANSITIONS = {
    'SUBMITTED': {'UNDER_REVIEW', 'DUPLICATE', 'REJECTED'},
    'UNDER_REVIEW': {'IN_PROGRESS', 'DUPLICATE', 'REJECTED'},
    'IN_PROGRESS': {'RESOLVED'},
    'RESOLVED': {'CLOSED'},
    'DUPLICATE': set(),
    'REJECTED': set(),
    'CLOSED': set()
}


def is_valid_transition(current_status, target_status):
    """
    Pure function to validate a status transition.
    
    Args:
        current_status: Current status of the request
        target_status: Desired new status
    
    Returns:
        bool: True if transition is allowed, False otherwise
    """
    allowed = STATUS_TRANSITIONS.get(current_status, set())
    return target_status in allowed