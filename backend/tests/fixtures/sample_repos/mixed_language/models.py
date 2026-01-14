"""Data models for the application."""

from dataclasses import dataclass


@dataclass
class DataModel:
    """Represents a data item."""
    id: int
    name: str
