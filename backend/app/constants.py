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
VALID_STATUSES = ['SUBMITTED', 'UNDER_REVIEW', 'IN_PROGRESS', 'RESOLVED', 'CLOSED']
ROLE_NAMES = ['RESIDENT', 'SUPPORT_OFFICER', 'ADMIN']