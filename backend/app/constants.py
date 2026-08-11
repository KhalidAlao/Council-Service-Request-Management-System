"""
Application-wide constants and mappings.
"""

CATEGORY_TO_DEPARTMENT = {
    'ROADS': 'Roads Maintenance',
    'WASTE': 'Waste Management',
    'PARKS': 'Parks and Recreation',
    'STREET_LIGHTING': 'Street Lighting',
    'BUILDINGS': 'Buildings Maintenance',
    'OTHER': 'Other Services',
}

VALID_CATEGORIES = list(CATEGORY_TO_DEPARTMENT.keys())
VALID_PRIORITIES = ['LOW', 'MEDIUM', 'HIGH', 'URGENT']
VALID_STATUSES = ['SUBMITTED', 'UNDER_REVIEW', 'IN_PROGRESS', 'RESOLVED', 'CLOSED', 'DUPLICATE', 'REJECTED'] 
ROLE_NAMES = ['RESIDENT', 'SUPPORT_OFFICER', 'ADMIN']

# Role → Allowed statuses mapping
ROLE_ALLOWED_STATUSES = {
    'SUPPORT_OFFICER': {
        'UNDER_REVIEW', 'IN_PROGRESS', 'DUPLICATE', 'REJECTED'
    },
    'ADMIN': {
        'RESOLVED', 'CLOSED'
    }
}

# State transition map: current_status → allowed next statuses
STATUS_TRANSITIONS = {
    'SUBMITTED': {'UNDER_REVIEW', 'DUPLICATE', 'REJECTED'},
    'UNDER_REVIEW': {'IN_PROGRESS', 'DUPLICATE', 'REJECTED'},
    'IN_PROGRESS': {'RESOLVED'},
    'RESOLVED': {'CLOSED'},
    'DUPLICATE': set(),      # Terminal — no further transitions
    'REJECTED': set(),        # Terminal — no further transitions
    'CLOSED': set()           # Terminal — no further transitions
}
