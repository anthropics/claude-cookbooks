"""
Async API client with similar concurrency issues.
This demonstrates Claude applying thread-safety patterns to async code.
"""

import asyncio
from typing import List, Dict, Any

import aiohttp


class AsyncAPIClient:
    """Async API client for fetching data from multiple endpoints."""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.responses = []  # BUG: Shared state accessed from multiple coroutines!
        self.error_count = 0  # BUG: Race condition on counter increment!

    async def fetch_endpoint(self, session: aiohttp.ClientSession, endpoint: str) -> Dict[str, Any]:
        """Fetch a single endpoint."""
        url = f"{self.base_url}/{endpoint}"
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                data = await response.json()
                return {
                    "endpoint": endpoint,
                    "status": response.status,
                    "data": data,
                }
        except Exception as e:
            return {
                "endpoint": endpoint,
                "error": str(e),
            }

    async def fetch_all(self, endpoints: List[str]) -> List[Dict[str, Any]]:
        """
        Fetch multiple endpoints concurrently.

        BUG: Similar to the threading issue, multiple coroutines
        modify self.responses and self.error_count without coordination!
        While Python's GIL prevents some race conditions in threads,
        async code can still have interleaving issues.
        """
        async with aiohttp.ClientSession() as session:
            tasks = [self.fetch_endpoint(session, endpoint) for endpoint in endpoints]

            for coro in asyncio.as_completed(tasks):
                result = await coro

                # RACE CONDITION: Multiple coroutines modify shared state
                if "error" in result:
                    self.error_count += 1  # Not atomic!
                else:
                    self.responses.append(result)  # Not thread-safe in async context!

        return self.responses

    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics."""
        return {
            "total_responses": len(self.responses),
            "errors": self.error_count,
            "success_rate": (
                len(self.responses) / (len(self.responses) + self.error_count)
                if (len(self.responses) + self.error_count) > 0
                else 0
            ),
        }


async def main():
    """Test the async API client."""
    client = AsyncAPIClient("https://jsonplaceholder.typicode.com")

    endpoints = [
        "posts/1",
        "posts/2",
        "posts/3",
        "users/1",
        "users/2",
        "invalid/endpoint",  # Will error
    ] * 20  # 120 requests total

    results = await client.fetch_all(endpoints)

    print("Expected: ~100 successful responses")
    print(f"Got: {len(results)} responses")
    print(f"Summary: {client.get_summary()}")
    print("\nNote: Counts may be incorrect due to race conditions!")


if __name__ == "__main__":
    asyncio.run(main())
