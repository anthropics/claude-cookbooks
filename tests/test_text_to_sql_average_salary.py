"""Exercise the Promptfoo salary assertion against the cookbook's sample database."""

import runpy
import sqlite3
import sys
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

import pytest

EVAL_DIR = Path(__file__).resolve().parents[1] / "capabilities/text_to_sql/evaluation"
FILTERED = """
FROM employees
WHERE department_id IN (
    SELECT d.id FROM departments d JOIN employees e ON e.department_id = d.id
    WHERE d.location = 'New York' GROUP BY d.id HAVING COUNT(*) > 5
)
"""


@pytest.fixture
def grade(monkeypatch):
    monkeypatch.chdir(EVAL_DIR)
    monkeypatch.syspath_prepend(str(EVAL_DIR / "tests"))
    with patch.dict(sys.modules):
        sys.modules.pop("utils", None)
        return runpy.run_path(str(EVAL_DIR / "tests/test_average_salary.py"))["get_assert"]


@pytest.mark.parametrize(
    ("query", "passes"),
    [
        ("SELECT AVG(salary) " + FILTERED, True),
        ("SELECT ROUND(AVG(salary), 2) " + FILTERED, True),
        ("SELECT AVG(salary) FROM employees", False),
        ("SELECT 50000", False),
        ("SELECT 106710.12 UNION ALL SELECT 50000", False),
    ],
)
def test_average_salary_assertion(grade, query, passes):
    result = grade(f"<sql>{query}</sql>", {})
    assert result["pass"] is passes
    assert result["score"] == int(passes)


@pytest.mark.parametrize("has_new_york", [True, False])
def test_average_tracks_the_database(grade, monkeypatch, tmp_path, has_new_york):
    data = tmp_path / "data"
    data.mkdir()
    with closing(sqlite3.connect(data / "data.db")) as db:
        db.execute("CREATE TABLE departments (id INTEGER, location TEXT)")
        db.execute("CREATE TABLE employees (department_id INTEGER, salary REAL)")
        location = "New York" if has_new_york else "Elsewhere"
        db.executemany("INSERT INTO departments VALUES (?, ?)", [(1, location), (2, location)])
        # Only the six-person department qualifies. Its mean falls exactly on a half cent.
        salaries = [(1, 125000.00), (1, 125000.25)] * 3 + [(2, 50000.00)] * 5
        db.executemany("INSERT INTO employees VALUES (?, ?)", salaries)
        db.commit()
    evaluation = tmp_path / "evaluation"
    evaluation.mkdir()
    monkeypatch.chdir(evaluation)
    assert grade("<sql>SELECT AVG(salary) " + FILTERED + "</sql>", {})["pass"]
    assert grade("<sql>SELECT ROUND(AVG(salary), 2) " + FILTERED + "</sql>", {})["pass"]
    assert not grade("<sql>SELECT 106710.12</sql>", {})["pass"]
