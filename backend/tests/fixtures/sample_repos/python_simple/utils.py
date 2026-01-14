"""Utility functions."""

import json
from typing import Dict, Any


def helper_function() -> str:
    """Helper function that returns a greeting."""
    return "Hello from helper!"


def process_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Process configuration dictionary."""
    return {
        "processed": True,
        "data": config
    }


def load_json_file(file_path: str) -> Dict:
    """Load JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)
