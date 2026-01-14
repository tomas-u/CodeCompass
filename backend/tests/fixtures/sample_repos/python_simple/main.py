"""Main module for Python sample project."""

import os
import sys
from utils import helper_function
from data_processor import DataProcessor


def main():
    """Main entry point."""
    print("Starting application...")

    # Use helper function
    result = helper_function()

    # Create processor
    processor = DataProcessor()
    data = processor.process()

    return result, data


if __name__ == "__main__":
    main()
