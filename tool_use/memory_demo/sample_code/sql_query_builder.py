"""
SQL query builder with SQL injection vulnerability.
Demonstrates dangerous string formatting in SQL queries.
"""

from typing import List, Optional


class UserDatabase:
    """Simple database interface (mock)."""

    def execute(self, query: str) -> List[dict]:
        """Mock execute - just returns the query for inspection."""
        print(f"Executing: {query}")
        return []


class QueryBuilder:
    """Build SQL queries for user operations."""

    def __init__(self, db: UserDatabase):
        self.db = db

    def get_user_by_name(self, username: str) -> Optional[dict]:
        """
        Get user by username.

        BUG: SQL INJECTION VULNERABILITY!
        Using string formatting with user input allows SQL injection.
        """
        # DANGEROUS: Never use f-strings or % formatting with user input!
        query = f"SELECT * FROM users WHERE username = '{username}'"
        results = self.db.execute(query)
        return results[0] if results else None

    def get_user_by_name_safe(self, username: str) -> Optional[dict]:
        """Safe version using parameterized queries."""
        # Use parameterized queries (this is pseudo-code for the concept)
        query = "SELECT * FROM users WHERE username = ?"
        # In real code: self.db.execute(query, (username,))
        print(f"Safe query with parameter: {query}, params: ({username},)")
        return None

    def search_users(self, search_term: str, limit: int = 10) -> List[dict]:
        """
        Search users by term.

        BUG: SQL INJECTION through LIKE clause!
        """
        # DANGEROUS: User input directly in LIKE clause
        query = f"SELECT * FROM users WHERE name LIKE '%{search_term}%' LIMIT {limit}"
        return self.db.execute(query)

    def delete_user(self, user_id: str) -> bool:
        """
        Delete a user.

        BUG: SQL INJECTION in DELETE statement!
        This is especially dangerous as it can lead to data loss.
        """
        # DANGEROUS: Unvalidated user input in DELETE
        query = f"DELETE FROM users WHERE id = {user_id}"
        self.db.execute(query)
        return True

    def get_users_by_role(self, role: str, order_by: str = "name") -> List[dict]:
        """
        Get users by role.

        BUG: SQL INJECTION in ORDER BY clause!
        Even the ORDER BY clause can be exploited.
        """
        # DANGEROUS: User-controlled ORDER BY
        query = f"SELECT * FROM users WHERE role = '{role}' ORDER BY {order_by}"
        return self.db.execute(query)


if __name__ == "__main__":
    db = UserDatabase()
    qb = QueryBuilder(db)

    print("=== Demonstrating SQL Injection Vulnerabilities ===\n")

    # Example 1: Basic injection
    print("1. Basic username injection:")
    qb.get_user_by_name("admin' OR '1'='1")
    # Executes: SELECT * FROM users WHERE username = 'admin' OR '1'='1'
    # Returns ALL users!

    print("\n2. Search term injection:")
    qb.search_users("test%' OR 1=1--")
    # Can bypass the LIKE and return everything

    print("\n3. DELETE injection:")
    qb.delete_user("1 OR 1=1")
    # Executes: DELETE FROM users WHERE id = 1 OR 1=1
    # DELETES ALL USERS!

    print("\n4. ORDER BY injection:")
    qb.get_users_by_role("admin", "name; DROP TABLE users--")
    # Can execute arbitrary SQL commands!

    print("\n=== Safe Version ===")
    qb.get_user_by_name_safe("admin' OR '1'='1")
    # Parameters are properly escaped
