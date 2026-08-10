"""
Reference number generation for service requests.
"""

import secrets
import string
from datetime import datetime


def generate_reference_number():
    """
    Generate a unique reference number for a service request.
    
    Format: SR-YYYY-XXXXXXXX
    Example: SR-2026-A7X92B3F
    
    Returns:
        str: A unique reference number
    """
    year = datetime.now().year
    # 8-character random alphanumeric string
    random_suffix = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
    return f"SR-{year}-{random_suffix}"