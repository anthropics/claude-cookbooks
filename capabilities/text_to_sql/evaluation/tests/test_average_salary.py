from math import ulp

from utils import execute_sql, extract_sql

REFERENCE_SQL = """
SELECT AVG(e.salary)
FROM employees e JOIN departments d ON e.department_id = d.id
WHERE d.location = 'New York' AND d.id IN (
    SELECT department_id FROM employees GROUP BY department_id HAVING COUNT(*) > 5
)
"""


def get_assert(output, context):
    sql = extract_sql(output)

    try:
        results = execute_sql(sql)
        execution_success = True
        expected = execute_sql(REFERENCE_SQL)[0][0]
        if expected is None:
            result_valid = results == [(None,)]
        else:
            result_valid = (
                len(results) == 1
                and isinstance(results[0][0], (int, float))
                # A rounded SQL average can land one floating-point step outside half a cent.
                and abs(results[0][0] - expected) <= 0.005 + ulp(expected)
            )
    except Exception as e:
        execution_success = False
        result_valid = False
        print(f"SQL execution error: {e}")

    return {
        "pass": execution_success and result_valid,
        "score": 1 if (execution_success and result_valid) else 0,
        "reason": f"SQL {'executed successfully with valid results' if (execution_success and result_valid) else 'failed or produced invalid results'}.",
    }
