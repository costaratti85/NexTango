def public_portal_launch_allowed(security_review_passed: bool) -> bool:
    """Public portal is blocked until explicit security review passes."""
    return bool(security_review_passed)
