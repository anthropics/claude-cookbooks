"""
Cache manager with mutable default argument bug.
This is one of Python's most common gotchas.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any


class CacheManager:
    """Manage cached data with TTL support."""

    def __init__(self):
        self.cache = {}

    def add_items(
        self,
        key: str,
        items: List[str] = [],  # BUG: Mutable default argument!
    ) -> None:
        """
        Add items to cache.

        BUG: Using [] as default creates a SHARED list across all calls!
        This is one of Python's classic gotchas.
        """
        # The items list is shared across ALL calls that don't provide items
        items.append(f"Added at {datetime.now()}")
        self.cache[key] = items

    def add_items_fixed(self, key: str, items: Optional[List[str]] = None) -> None:
        """Add items with proper default handling."""
        if items is None:
            items = []
        items = items.copy()  # Also make a copy to avoid mutation
        items.append(f"Added at {datetime.now()}")
        self.cache[key] = items

    def merge_configs(
        self,
        name: str,
        overrides: Dict[str, Any] = {},  # BUG: Mutable default!
    ) -> Dict[str, Any]:
        """
        Merge configuration with overrides.

        BUG: The default dict is shared across all calls!
        """
        defaults = {"timeout": 30, "retries": 3, "cache_enabled": True}

        # This modifies the SHARED overrides dict
        overrides.update(defaults)
        return overrides

    def merge_configs_fixed(
        self, name: str, overrides: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Merge configs properly."""
        if overrides is None:
            overrides = {}

        defaults = {"timeout": 30, "retries": 3, "cache_enabled": True}

        # Create new dict to avoid mutation
        result = {**defaults, **overrides}
        return result


class DataProcessor:
    """Another example of the mutable default bug."""

    def process_batch(
        self,
        data: List[int],
        filters: List[str] = [],  # BUG: Mutable default!
    ) -> List[int]:
        """
        Process data with optional filters.

        BUG: filters list is shared across calls!
        """
        filters.append("default_filter")  # Modifies shared list!

        result = []
        for item in data:
            if "positive" in filters and item < 0:
                continue
            result.append(item * 2)
        return result


if __name__ == "__main__":
    cache = CacheManager()

    # Demonstrate the bug
    print("=== Demonstrating Mutable Default Argument Bug ===\n")

    # First call with no items
    cache.add_items("key1")
    print(f"key1: {cache.cache['key1']}")

    # Second call with no items - SURPRISE! Gets the same list
    cache.add_items("key2")
    print(f"key2: {cache.cache['key2']}")  # Will have TWO timestamps!

    # Third call - even worse!
    cache.add_items("key3")
    print(f"key3: {cache.cache['key3']}")  # Will have THREE timestamps!

    print("\nAll keys share the same list object!")
    print(f"key1 is key2: {cache.cache['key1'] is cache.cache['key2']}")

    print("\n=== Using Fixed Version ===\n")
    cache2 = CacheManager()
    cache2.add_items_fixed("key1")
    cache2.add_items_fixed("key2")
    cache2.add_items_fixed("key3")
    print(f"key1: {cache2.cache['key1']}")
    print(f"key2: {cache2.cache['key2']}")
    print(f"key3: {cache2.cache['key3']}")
    print(f"\nkey1 is key2: {cache2.cache['key1'] is cache2.cache['key2']}")
