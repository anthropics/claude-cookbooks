"""
Data processor with multiple concurrency and thread-safety issues.
Used for Session 3 to demonstrate context editing with multiple bugs.
"""

import json
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List, Dict, Any


class DataProcessor:
    """Process data files concurrently with various thread-safety issues."""

    def __init__(self, max_workers: int = 5):
        self.max_workers = max_workers
        self.processed_count = 0  # BUG: Race condition on counter
        self.results = []  # BUG: Shared list without locking
        self.errors = {}  # BUG: Shared dict without locking
        self.lock = threading.Lock()  # Available but not used!

    def process_file(self, file_path: str) -> Dict[str, Any]:
        """Process a single file."""
        try:
            with open(file_path, "r") as f:
                data = json.load(f)

            # Simulate some processing
            processed = {
                "file": file_path,
                "record_count": len(data) if isinstance(data, list) else 1,
                "size_bytes": Path(file_path).stat().st_size,
            }

            return processed

        except Exception as e:
            return {"file": file_path, "error": str(e)}

    def process_batch(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """
        Process multiple files concurrently.

        MULTIPLE BUGS:
        1. self.processed_count is incremented without locking
        2. self.results is appended to from multiple threads
        3. self.errors is modified from multiple threads
        4. We have a lock but don't use it!
        """
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(self.process_file, fp) for fp in file_paths]

            for future in futures:
                result = future.result()

                # RACE CONDITION: Increment counter without lock
                self.processed_count += 1  # BUG!

                if "error" in result:
                    # RACE CONDITION: Modify dict without lock
                    self.errors[result["file"]] = result["error"]  # BUG!
                else:
                    # RACE CONDITION: Append to list without lock
                    self.results.append(result)  # BUG!

        return self.results

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get processing statistics.

        BUG: Accessing shared state without ensuring thread-safety.
        If called while processing, could get inconsistent values.
        """
        total_files = self.processed_count
        successful = len(self.results)
        failed = len(self.errors)

        # BUG: These counts might not add up correctly due to race conditions
        return {
            "total_processed": total_files,
            "successful": successful,
            "failed": failed,
            "success_rate": successful / total_files if total_files > 0 else 0,
        }

    def reset(self):
        """
        Reset processor state.

        BUG: No locking - if called during processing, causes corruption.
        """
        self.processed_count = 0  # RACE CONDITION
        self.results = []  # RACE CONDITION
        self.errors = {}  # RACE CONDITION


class SharedCache:
    """
    A shared cache with thread-safety issues.

    BUG: Classic read-modify-write race condition pattern.
    """

    def __init__(self):
        self.cache = {}  # BUG: Shared dict without locking
        self.hit_count = 0  # BUG: Race condition
        self.miss_count = 0  # BUG: Race condition

    def get(self, key: str) -> Any:
        """Get from cache - RACE CONDITION on hit/miss counts."""
        if key in self.cache:
            self.hit_count += 1  # BUG: Not atomic!
            return self.cache[key]
        else:
            self.miss_count += 1  # BUG: Not atomic!
            return None

    def set(self, key: str, value: Any):
        """Set in cache - RACE CONDITION on dict modification."""
        self.cache[key] = value  # BUG: Dict access not synchronized!

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics - may be inconsistent."""
        total = self.hit_count + self.miss_count
        return {
            "hits": self.hit_count,
            "misses": self.miss_count,
            "hit_rate": self.hit_count / total if total > 0 else 0,
        }


if __name__ == "__main__":
    # Create some test files (not included)
    processor = DataProcessor(max_workers=10)

    # Simulate processing many files
    file_paths = [f"data/file_{i}.json" for i in range(100)]

    print("Processing files concurrently...")
    results = processor.process_batch(file_paths)

    print(f"\nStatistics: {processor.get_statistics()}")
    print("\nNote: Counts may be inconsistent due to race conditions!")
