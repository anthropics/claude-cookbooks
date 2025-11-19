"""
Shared utilities for Claude tool use cookbooks.

This package contains reusable components for creating cookbook demonstrations:
- visualize: Rich terminal visualization for Claude API responses
- drone_delivery_api: Example mock API for demonstration purposes
- team_expense_api: Example mock API for team expense management demonstrations
"""

from .visualize import visualize, show_response

__all__ = ["visualize", "show_response"]
