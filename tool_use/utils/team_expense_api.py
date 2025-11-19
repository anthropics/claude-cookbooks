"""
Example Mock API for Team Expense Management Demo

This is a domain-specific API used in the programmatic tool calling cookbook.
It provides mock tools for retrieving team member information, expense records,
and budget limits by employee level.
"""

import json
import random
import time
from datetime import datetime, timedelta

# Configuration
EXPENSE_LINE_ITEMS_PER_PERSON_MIN = 20
EXPENSE_LINE_ITEMS_PER_PERSON_MAX = 50
DELAY_MULTIPLIER = 0  # Adjust this to simulate API latency


def get_team_members(department: str) -> str:
    """Returns a list of team members for a given department.

    Each team member includes their ID, name, role, level, and contact information.
    Use this to get a list of people whose expenses you want to analyze.

    Args:
        department: The department name (e.g., 'engineering', 'sales', 'marketing').
            Case-insensitive.

    Returns:
        JSON string containing an array of team member objects with fields:
        - id: Unique employee identifier
        - name: Full name
        - role: Job title
        - level: Employee level (junior, mid, senior, staff, principal)
        - email: Contact email
        - department: Department name
    """
    import time

    time.sleep(DELAY_MULTIPLIER * 0.1)

    department = department.lower()

    # Mock team data by department
    teams = {
        "engineering": [
            {
                "id": "ENG001",
                "name": "Alice Chen",
                "role": "Senior Software Engineer",
                "level": "senior",
                "email": "alice.chen@company.com",
                "department": "engineering",
            },
            {
                "id": "ENG002",
                "name": "Bob Martinez",
                "role": "Staff Engineer",
                "level": "staff",
                "email": "bob.martinez@company.com",
                "department": "engineering",
            },
            {
                "id": "ENG003",
                "name": "Carol White",
                "role": "Software Engineer",
                "level": "mid",
                "email": "carol.white@company.com",
                "department": "engineering",
            },
            {
                "id": "ENG004",
                "name": "David Kim",
                "role": "Principal Engineer",
                "level": "principal",
                "email": "david.kim@company.com",
                "department": "engineering",
            },
            {
                "id": "ENG005",
                "name": "Emma Johnson",
                "role": "Junior Software Engineer",
                "level": "junior",
                "email": "emma.johnson@company.com",
                "department": "engineering",
            },
            {
                "id": "ENG006",
                "name": "Frank Liu",
                "role": "Senior Software Engineer",
                "level": "senior",
                "email": "frank.liu@company.com",
                "department": "engineering",
            },
            {
                "id": "ENG007",
                "name": "Grace Taylor",
                "role": "Software Engineer",
                "level": "mid",
                "email": "grace.taylor@company.com",
                "department": "engineering",
            },
            {
                "id": "ENG008",
                "name": "Henry Park",
                "role": "Staff Engineer",
                "level": "staff",
                "email": "henry.park@company.com",
                "department": "engineering",
            },
        ],
        "sales": [
            {
                "id": "SAL001",
                "name": "Irene Davis",
                "role": "Account Executive",
                "level": "mid",
                "email": "irene.davis@company.com",
                "department": "sales",
            },
            {
                "id": "SAL002",
                "name": "Jack Wilson",
                "role": "Senior Account Executive",
                "level": "senior",
                "email": "jack.wilson@company.com",
                "department": "sales",
            },
            {
                "id": "SAL003",
                "name": "Kelly Brown",
                "role": "Sales Development Rep",
                "level": "junior",
                "email": "kelly.brown@company.com",
                "department": "sales",
            },
            {
                "id": "SAL004",
                "name": "Leo Garcia",
                "role": "Regional Sales Director",
                "level": "staff",
                "email": "leo.garcia@company.com",
                "department": "sales",
            },
            {
                "id": "SAL005",
                "name": "Maya Patel",
                "role": "Account Executive",
                "level": "mid",
                "email": "maya.patel@company.com",
                "department": "sales",
            },
            {
                "id": "SAL006",
                "name": "Nathan Scott",
                "role": "VP of Sales",
                "level": "principal",
                "email": "nathan.scott@company.com",
                "department": "sales",
            },
        ],
        "marketing": [
            {
                "id": "MKT001",
                "name": "Olivia Thompson",
                "role": "Marketing Manager",
                "level": "senior",
                "email": "olivia.thompson@company.com",
                "department": "marketing",
            },
            {
                "id": "MKT002",
                "name": "Peter Anderson",
                "role": "Content Specialist",
                "level": "mid",
                "email": "peter.anderson@company.com",
                "department": "marketing",
            },
            {
                "id": "MKT003",
                "name": "Quinn Rodriguez",
                "role": "Marketing Coordinator",
                "level": "junior",
                "email": "quinn.rodriguez@company.com",
                "department": "marketing",
            },
            {
                "id": "MKT004",
                "name": "Rachel Lee",
                "role": "Director of Marketing",
                "level": "staff",
                "email": "rachel.lee@company.com",
                "department": "marketing",
            },
            {
                "id": "MKT005",
                "name": "Sam Miller",
                "role": "Social Media Manager",
                "level": "mid",
                "email": "sam.miller@company.com",
                "department": "marketing",
            },
        ],
    }

    if department not in teams:
        return json.dumps(
            {
                "error": f"Department '{department}' not found. Available departments: {', '.join(teams.keys())}"
            }
        )

    return json.dumps(teams[department], indent=2)


def get_expenses(employee_id: str, quarter: str) -> str:
    """Returns all expense line items for a given employee in a specific quarter.

    Each expense includes date, category, description, amount, and status.
    An employee may have anywhere from a few to 150+ expense line items per quarter.

    Args:
        employee_id: The unique employee identifier (e.g., 'ENG001', 'SAL002')
        quarter: Quarter identifier (e.g., 'Q1', 'Q2', 'Q3', 'Q4')

    Returns:
        JSON string containing an array of expense objects with fields:
        - expense_id: Unique expense identifier
        - date: ISO format date when expense occurred
        - category: Expense type (travel, meals, lodging, software, equipment, etc.)
        - description: Details about the expense
        - amount: Dollar amount (float)
        - currency: Currency code (default 'USD')
        - status: Approval status (approved, pending, rejected)
    """

    time.sleep(DELAY_MULTIPLIER * 0.2)

    # Generate a deterministic but varied number of expenses based on employee_id
    random.seed(hash(employee_id + quarter))
    num_expenses = random.randint(
        EXPENSE_LINE_ITEMS_PER_PERSON_MIN, EXPENSE_LINE_ITEMS_PER_PERSON_MAX
    )

    # Quarter date ranges
    quarter_dates = {
        "Q1": (datetime(2024, 1, 1), datetime(2024, 3, 31)),
        "Q2": (datetime(2024, 4, 1), datetime(2024, 6, 30)),
        "Q3": (datetime(2024, 7, 1), datetime(2024, 9, 30)),
        "Q4": (datetime(2024, 10, 1), datetime(2024, 12, 31)),
    }

    if quarter.upper() not in quarter_dates:
        return json.dumps({"error": f"Invalid quarter '{quarter}'. Must be Q1, Q2, Q3, or Q4"})

    start_date, end_date = quarter_dates[quarter.upper()]

    # Expense categories and typical amounts
    expense_categories = [
        ("travel", "Flight to client meeting", 400, 1500),
        ("travel", "Train ticket", 100, 500),
        ("travel", "Rental car", 100, 500),
        ("travel", "Taxi/Uber", 15, 200),
        ("travel", "Parking fee", 10, 50),
        ("lodging", "Hotel stay", 150, 900),
        ("lodging", "Airbnb rental", 100, 950),
        ("meals", "Client dinner", 50, 250),
        ("meals", "Team lunch", 20, 100),
        ("meals", "Conference breakfast", 15, 40),
        ("meals", "Coffee meeting", 5, 25),
        ("software", "SaaS subscription", 10, 200),
        ("software", "API credits", 50, 500),
        ("equipment", "Monitor", 200, 800),
        ("equipment", "Keyboard", 50, 200),
        ("equipment", "Webcam", 50, 150),
        ("equipment", "Headphones", 100, 300),
        ("conference", "Conference ticket", 500, 2500),
        ("conference", "Workshop registration", 200, 1000),
        ("office", "Office supplies", 10, 100),
        ("office", "Books", 20, 80),
        ("internet", "Mobile data", 30, 100),
        ("internet", "WiFi hotspot", 20, 60),
    ]

    expenses = []
    for i in range(num_expenses):
        category, desc_template, min_amt, max_amt = random.choice(expense_categories)

        # Generate random date within quarter
        days_diff = (end_date - start_date).days
        random_days = random.randint(0, days_diff)
        expense_date = start_date + timedelta(days=random_days)

        # Generate amount
        amount = round(random.uniform(min_amt, max_amt), 2)

        # Status (most are approved)
        status = random.choices(["approved", "pending", "rejected"], weights=[0.85, 0.10, 0.05])[0]

        expenses.append(
            {
                "expense_id": f"{employee_id}_{quarter}_{i:03d}",
                "date": expense_date.strftime("%Y-%m-%d"),
                "category": category,
                "description": desc_template,
                "amount": amount,
                "currency": "USD",
                "status": status,
            }
        )

    # Sort by date
    expenses.sort(key=lambda x: x["date"])

    return json.dumps(expenses, indent=2)


def get_budget_by_level(level: str) -> str:
    """Returns budget limits for a given employee level.

    Budget limits include quarterly caps for different expense categories like travel,
    meals, equipment, software, and conferences.

    Args:
        level: Employee level (junior, mid, senior, staff, principal)

    Returns:
        JSON string containing budget limits object with fields:
        - level: Employee level
        - quarterly_limits: Dictionary of category limits
        - travel_limit: Total quarterly travel budget (includes flights, lodging, ground transport)
        - meals_limit: Quarterly meals and entertainment budget
        - equipment_limit: Quarterly equipment budget
        - software_limit: Quarterly software/tools budget
        - conference_limit: Quarterly conference/training budget
        - total_limit: Overall quarterly expense limit
    """
    import time

    time.sleep(DELAY_MULTIPLIER * 0.05)

    level = level.lower()

    # Budget structures by level
    budgets = {
        "junior": {
            "level": "junior",
            "travel_limit": 2000,
            "meals_limit": 500,
            "equipment_limit": 1000,
            "software_limit": 300,
            "conference_limit": 1500,
            "total_limit": 5300,
            "currency": "USD",
        },
        "mid": {
            "level": "mid",
            "travel_limit": 4000,
            "meals_limit": 1000,
            "equipment_limit": 1500,
            "software_limit": 500,
            "conference_limit": 2500,
            "total_limit": 9500,
            "currency": "USD",
        },
        "senior": {
            "level": "senior",
            "travel_limit": 6000,
            "meals_limit": 1500,
            "equipment_limit": 2000,
            "software_limit": 800,
            "conference_limit": 3500,
            "total_limit": 13800,
            "currency": "USD",
        },
        "staff": {
            "level": "staff",
            "travel_limit": 8000,
            "meals_limit": 2000,
            "equipment_limit": 2500,
            "software_limit": 1200,
            "conference_limit": 5000,
            "total_limit": 18700,
            "currency": "USD",
        },
        "principal": {
            "level": "principal",
            "travel_limit": 12000,
            "meals_limit": 3000,
            "equipment_limit": 3000,
            "software_limit": 1500,
            "conference_limit": 7500,
            "total_limit": 27000,
            "currency": "USD",
        },
    }

    if level not in budgets:
        return json.dumps(
            {"error": f"Invalid level '{level}'. Must be one of: {', '.join(budgets.keys())}"}
        )

    return json.dumps(budgets[level], indent=2)


# Helper function to get all available tools
def get_expense_tools():
    """Returns a list of all expense management tools for use with Claude API."""
    return [get_team_members, get_expenses, get_budget_by_level]


if __name__ == "__main__":
    # Example usage demonstrating the toy example from the request
    print("=== Team Expense Analysis Example ===\n")

    # Get team members
    team = json.loads(get_team_members("engineering"))

    exceeded = []
    for member in team[:5]:  # Just check first 3 for demo
        print(f"Checking expenses for {member['name']}...")

        # Fetch this person's expenses (could be 100+ line items)
        expenses = json.loads(get_expenses(member["id"], "Q3"))

        # Get budget for their level
        budget = json.loads(get_budget_by_level(member["level"]))

        # Sum all their expense line items
        total = sum(exp["amount"] for exp in expenses if exp["status"] == "approved")

        print(f"  - Found {len(expenses)} expense line items")
        print(f"  - Total approved expenses: ${total:,.2f}")
        print(f"  - Travel limit: ${budget['travel_limit']:,}\n")

        if total > budget["travel_limit"]:
            exceeded.append(
                {"name": member["name"], "spent": total, "limit": budget["travel_limit"]}
            )

    print("\n=== Summary: Employees Over Budget ===")
    print(json.dumps(exceeded, indent=2))
