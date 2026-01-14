"""Helper utilities for data processing."""


def validate_id(item_id):
    """Validate item ID is positive."""
    return item_id > 0


def format_response(data):
    """Format data for API response."""
    return {"success": True, "data": data}
