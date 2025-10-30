"""
Concurrent web scraper with a race condition bug.
Multiple threads modify shared state without synchronization.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any

import requests


class WebScraper:
    """Web scraper that fetches multiple URLs concurrently."""

    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers
        self.results = []  # BUG: Shared mutable state accessed by multiple threads!
        self.failed_urls = []  # BUG: Another race condition!

    def fetch_url(self, url: str) -> Dict[str, Any]:
        """Fetch a single URL and return the result."""
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            return {
                "url": url,
                "status": response.status_code,
                "content_length": len(response.content),
            }
        except requests.exceptions.RequestException as e:
            return {"url": url, "error": str(e)}

    def scrape_urls(self, urls: List[str]) -> List[Dict[str, Any]]:
        """
        Scrape multiple URLs concurrently.

        BUG: self.results is accessed from multiple threads without locking!
        This causes race conditions where results can be lost or corrupted.
        """
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(self.fetch_url, url) for url in urls]

            for future in as_completed(futures):
                result = future.result()

                # RACE CONDITION: Multiple threads append to self.results simultaneously
                if "error" in result:
                    self.failed_urls.append(result["url"])  # RACE CONDITION
                else:
                    self.results.append(result)  # RACE CONDITION

        return self.results

    def get_stats(self) -> Dict[str, int]:
        """Get scraping statistics."""
        return {
            "total_results": len(self.results),
            "failed_urls": len(self.failed_urls),
            "success_rate": (
                len(self.results) / (len(self.results) + len(self.failed_urls))
                if (len(self.results) + len(self.failed_urls)) > 0
                else 0
            ),
        }


if __name__ == "__main__":
    # Test with multiple URLs
    urls = [
        "https://httpbin.org/delay/1",
        "https://httpbin.org/status/200",
        "https://httpbin.org/status/404",
        "https://httpbin.org/delay/2",
        "https://httpbin.org/status/500",
    ] * 10  # 50 URLs total to increase race condition probability

    scraper = WebScraper(max_workers=10)
    results = scraper.scrape_urls(urls)

    print("Expected: 50 results")
    print(f"Got: {len(results)} results")
    print(f"Stats: {scraper.get_stats()}")
    print("\nNote: Results count may be less than expected due to race condition!")
