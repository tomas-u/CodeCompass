"""Sample Python application for testing code analysis."""

import os
import sys
from utils import calculate_sum, format_output


def main():
    """Main entry point for the application."""
    numbers = [1, 2, 3, 4, 5]
    total = calculate_sum(numbers)
    output = format_output("Total", total)
    print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
