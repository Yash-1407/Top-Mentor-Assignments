import csv
import mysql.connector
from mysql.connector import Error
import pandas as pd

# ============================================================
# TOPMENTOR - RELATIONAL DATA INGESTION & SQL ANALYTICS
# ============================================================
# Install if needed:
# pip install mysql-connector-python pandas
#
# Create the database once in MySQL:
# CREATE DATABASE company_db;
#
# Update these credentials before running.
# ============================================================

DB_CONFIG = {
    "host": "localhost",
    "user": "your_username",
    "password": "your_password",
    "database": "company_db"
}

CSV_FILE = "employees_data.csv"


def ingest_csv_to_mysql():
    conn = None
    cursor = None

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute("DROP TABLE IF EXISTS employees;")

        create_table_query = """
        CREATE TABLE employees (
            employee_id INT AUTO_INCREMENT PRIMARY KEY,
            first_name VARCHAR(50) NOT NULL,
            last_name VARCHAR(50) NOT NULL,
            department VARCHAR(50) NOT NULL,
            salary DECIMAL(10, 2) NOT NULL,
            hire_date DATE NOT NULL,
            Day_of_Week VARCHAR(15),
            Day_of_month INT,
            Month INT,
            Year INT
        );
        """
        cursor.execute(create_table_query)

        with open(CSV_FILE, mode="r", newline="", encoding="utf-8") as file:
            csv_reader = csv.reader(file)
            next(csv_reader)

            insert_query = """
            INSERT INTO employees (
                employee_id, first_name, last_name, department, salary,
                hire_date, Day_of_Week, Day_of_month, Month, Year
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """

            records_to_insert = [tuple(row) for row in csv_reader]
            cursor.executemany(insert_query, records_to_insert)

        conn.commit()
        print(f"Successfully ingested {cursor.rowcount} records into employees.")

    except (Error, FileNotFoundError) as e:
        print(f"Error during ingestion: {e}")
        raise

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()


# ============================================================
# 20 SQL BUSINESS QUESTIONS
# ============================================================

QUERIES = {
    1: """
        SELECT
            department,
            first_name,
            salary,
            DENSE_RANK() OVER (
                PARTITION BY department
                ORDER BY salary DESC
            ) AS salary_rank
        FROM employees
        ORDER BY department, salary_rank, first_name;
    """,

    2: """
        SELECT
            employee_id,
            first_name,
            last_name,
            department,
            salary,
            LEAD(salary) OVER (
                PARTITION BY department
                ORDER BY salary
            ) AS next_highest_salary,
            LEAD(salary) OVER (
                PARTITION BY department
                ORDER BY salary
            ) - salary AS salary_difference
        FROM employees
        ORDER BY department, salary;
    """,

    3: """
        WITH department_salary AS (
            SELECT
                department,
                SUM(salary) AS total_salary
            FROM employees
            GROUP BY department
        ),
        average_department_salary AS (
            SELECT AVG(total_salary) AS avg_total_salary
            FROM department_salary
        )
        SELECT
            ds.department,
            ds.total_salary,
            ads.avg_total_salary
        FROM department_salary ds
        CROSS JOIN average_department_salary ads
        WHERE ds.total_salary > ads.avg_total_salary
        ORDER BY ds.total_salary DESC;
    """,

    4: """
        SELECT
            employee_id,
            first_name,
            last_name,
            department,
            salary
        FROM employees
        WHERE salary > (
            SELECT MAX(salary)
            FROM employees
            WHERE department = 'HR'
        )
        ORDER BY salary DESC;
    """,

    5: """
        SELECT
            department,
            first_name,
            last_name,
            hire_date,
            salary,
            SUM(salary) OVER (
                PARTITION BY department
                ORDER BY hire_date, employee_id
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            ) AS cumulative_department_salary
        FROM employees
        ORDER BY department, hire_date, employee_id;
    """,

    6: """
        WITH ranked_employees AS (
            SELECT
                employee_id,
                first_name,
                last_name,
                department,
                salary,
                DENSE_RANK() OVER (
                    PARTITION BY department
                    ORDER BY salary DESC
                ) AS salary_rank
            FROM employees
        )
        SELECT
            employee_id,
            first_name,
            last_name,
            department,
            salary
        FROM ranked_employees
        WHERE salary_rank = 2
        ORDER BY department;
    """,

    7: """
        WITH monthly_hires AS (
            SELECT
                Year AS hire_year,
                Month AS hire_month,
                COUNT(*) AS hire_count
            FROM employees
            GROUP BY Year, Month
        ),
        yearly_monthly_average AS (
            SELECT
                hire_year,
                AVG(hire_count) AS avg_monthly_hires
            FROM monthly_hires
            GROUP BY hire_year
        )
        SELECT
            mh.hire_year,
            mh.hire_month,
            mh.hire_count,
            yma.avg_monthly_hires
        FROM monthly_hires mh
        JOIN yearly_monthly_average yma
            ON mh.hire_year = yma.hire_year
        WHERE mh.hire_count > yma.avg_monthly_hires
        ORDER BY mh.hire_year, mh.hire_month;
    """,

    8: """
        SELECT
            employee_id,
            first_name,
            last_name,
            department,
            salary,
            NTILE(4) OVER (
                PARTITION BY department
                ORDER BY salary
            ) AS salary_quartile
        FROM employees
        ORDER BY department, salary;
    """,

    9: """
        SELECT
            employee_id,
            first_name,
            last_name,
            department,
            salary,
            ROUND(
                100 * salary /
                SUM(salary) OVER (PARTITION BY department),
                2
            ) AS department_salary_percentage
        FROM employees
        ORDER BY department, salary DESC;
    """,

    10: """
        SELECT
            employee_id,
            first_name,
            last_name,
            department,
            hire_date,
            salary,
            ROUND(
                AVG(salary) OVER (
                    PARTITION BY department
                    ORDER BY hire_date, employee_id
                    ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING
                ),
                2
            ) AS rolling_3_employee_avg
        FROM employees
        ORDER BY department, hire_date, employee_id;
    """,

    11: """
        SELECT
            department,
            MAX(salary) AS highest_salary,
            MIN(salary) AS lowest_salary,
            MAX(salary) - MIN(salary) AS salary_spread
        FROM employees
        GROUP BY department
        HAVING MAX(salary) - MIN(salary) = (
            SELECT MAX(salary_spread)
            FROM (
                SELECT
                    MAX(salary) - MIN(salary) AS salary_spread
                FROM employees
                GROUP BY department
            ) AS department_spreads
        );
    """,

    12: """
        SELECT
            employee_id,
            first_name,
            last_name,
            department,
            salary,
            hire_date
        FROM employees
        WHERE YEAR(hire_date) = (
            SELECT YEAR(hire_date)
            FROM employees
            ORDER BY salary ASC, employee_id
            LIMIT 1
        )
        AND MONTH(hire_date) = (
            SELECT MONTH(hire_date)
            FROM employees
            ORDER BY salary ASC, employee_id
            LIMIT 1
        )
        ORDER BY hire_date, employee_id;
    """,

    13: """
        WITH ranked_employees AS (
            SELECT
                employee_id,
                first_name,
                last_name,
                department,
                salary,
                DENSE_RANK() OVER (
                    PARTITION BY department
                    ORDER BY salary DESC
                ) AS dense_salary_rank
            FROM employees
        )
        SELECT
            employee_id,
            first_name,
            last_name,
            department,
            salary,
            dense_salary_rank
        FROM ranked_employees
        WHERE dense_salary_rank <= 3
        ORDER BY department, dense_salary_rank, salary DESC;
    """,

    14: """
        SELECT DISTINCT e.department
        FROM employees e
        WHERE EXISTS (
            SELECT 1
            FROM employees e2
            WHERE e2.department = e.department
              AND e2.salary > 120000
        )
        ORDER BY e.department;
    """,

    15: """
        WITH department_bookends AS (
            SELECT
                department,
                MIN(hire_date) AS earliest_hire_date,
                MAX(hire_date) AS latest_hire_date
            FROM employees
            GROUP BY department
        ),
        earliest_employees AS (
            SELECT
                db.department,
                'Earliest Hired' AS hire_type,
                e.first_name,
                e.last_name,
                e.hire_date
            FROM department_bookends db
            JOIN employees e
              ON e.department = db.department
             AND e.hire_date = db.earliest_hire_date
        ),
        latest_employees AS (
            SELECT
                db.department,
                'Latest Hired' AS hire_type,
                e.first_name,
                e.last_name,
                e.hire_date
            FROM department_bookends db
            JOIN employees e
              ON e.department = db.department
             AND e.hire_date = db.latest_hire_date
        )
        SELECT * FROM earliest_employees
        UNION ALL
        SELECT * FROM latest_employees
        ORDER BY department, hire_type;
    """,

    16: """
        SELECT
            employee_id,
            first_name,
            last_name,
            department,
            salary,
            FIRST_VALUE(
                CONCAT(first_name, ' ', last_name)
            ) OVER (
                PARTITION BY department
                ORDER BY salary DESC, employee_id
            ) AS highest_paid_individual
        FROM employees
        ORDER BY department, salary DESC, employee_id;
    """,

    17: """
        WITH yearly_hires AS (
            SELECT
                Year AS hire_year,
                COUNT(*) AS headcount_hired
            FROM employees
            GROUP BY Year
        ),
        yearly_with_previous AS (
            SELECT
                hire_year,
                headcount_hired,
                LAG(headcount_hired) OVER (
                    ORDER BY hire_year
                ) AS previous_year_headcount
            FROM yearly_hires
        )
        SELECT
            hire_year,
            headcount_hired,
            previous_year_headcount,
            headcount_hired - previous_year_headcount AS yoy_change
        FROM yearly_with_previous
        ORDER BY hire_year;
    """,

    18: """
        WITH monthly_hires AS (
            SELECT
                Year AS hire_year,
                Month AS hire_month,
                COUNT(*) AS total_hires
            FROM employees
            GROUP BY Year, Month
        ),
        peak_period AS (
            SELECT MAX(total_hires) AS peak_hires
            FROM monthly_hires
        )
        SELECT
            e.employee_id,
            e.first_name,
            e.last_name,
            e.department,
            e.hire_date,
            mh.total_hires AS hires_in_month
        FROM employees e
        JOIN monthly_hires mh
          ON e.Year = mh.hire_year
         AND e.Month = mh.hire_month
        CROSS JOIN peak_period pp
        WHERE mh.total_hires = pp.peak_hires
        ORDER BY e.hire_date, e.employee_id;
    """,

    19: """
        WITH ranked AS (
            SELECT
                employee_id,
                department,
                salary,
                ROW_NUMBER() OVER (
                    PARTITION BY department
                    ORDER BY salary DESC, employee_id
                ) AS rn_high,
                ROW_NUMBER() OVER (
                    PARTITION BY department
                    ORDER BY salary ASC, employee_id
                ) AS rn_low,
                COUNT(*) OVER (
                    PARTITION BY department
                ) AS dept_count
            FROM employees
        ),
        top_10 AS (
            SELECT department, AVG(salary) AS top_10_avg
            FROM ranked
            WHERE rn_high <= CEIL(dept_count * 0.10)
            GROUP BY department
        ),
        bottom_10 AS (
            SELECT department, AVG(salary) AS bottom_10_avg
            FROM ranked
            WHERE rn_low <= CEIL(dept_count * 0.10)
            GROUP BY department
        )
        SELECT
            t.department,
            ROUND(t.top_10_avg, 2) AS top_10_avg_salary,
            ROUND(b.bottom_10_avg, 2) AS bottom_10_avg_salary,
            ROUND(t.top_10_avg - b.bottom_10_avg, 2) AS polarization_index
        FROM top_10 t
        JOIN bottom_10 b
          ON t.department = b.department
        ORDER BY polarization_index DESC;
    """,

    20: """
        WITH salary_ranked AS (
            SELECT
                employee_id,
                first_name,
                last_name,
                department,
                salary,
                AVG(salary) OVER (
                    PARTITION BY department
                ) AS department_average_salary,
                RANK() OVER (
                    PARTITION BY department
                    ORDER BY salary DESC
                ) AS department_rank,
                ROW_NUMBER() OVER (
                    PARTITION BY department
                    ORDER BY salary, employee_id
                ) AS median_row_asc,
                COUNT(*) OVER (
                    PARTITION BY department
                ) AS department_count
            FROM employees
        ),
        department_medians AS (
            SELECT
                department,
                AVG(salary) AS median_salary
            FROM salary_ranked
            WHERE median_row_asc IN (
                FLOOR((department_count + 1) / 2),
                FLOOR((department_count + 2) / 2)
            )
            GROUP BY department
        )
        SELECT
            sr.first_name,
            sr.last_name,
            sr.department,
            sr.salary,
            ROUND(sr.department_average_salary, 2) AS department_average_salary,
            sr.department_rank,
            CASE
                WHEN sr.salary > dm.median_salary THEN 'Above'
                ELSE 'Below'
            END AS median_flag
        FROM salary_ranked sr
        JOIN department_medians dm
          ON sr.department = dm.department
        ORDER BY sr.department, sr.department_rank, sr.employee_id;
    """
}


def run_assignment():
    conn = None
    cursor = None

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        for question_number, query in QUERIES.items():
            print("\n" + "=" * 80)
            print(f"QUESTION {question_number}")
            print("=" * 80)

            # Step 1: Native SQL execution and raw tuple printing
            cursor.execute(query)
            rows = cursor.fetchall()

            print("SQL RESULT:")
            for row in rows:
                print(row)

            # Step 2: Pandas verification of the exact same SQL query
            verify_conn = mysql.connector.connect(**DB_CONFIG)
            try:
                verified_df = pd.read_sql(query, verify_conn)
                print("\nPANDAS VERIFICATION:")
                print(f"Rows: {len(verified_df)}")
                print(f"Columns: {list(verified_df.columns)}")
                print(verified_df.to_string(index=False))
            finally:
                verify_conn.close()

    except Error as e:
        print(f"Error while running assignment: {e}")
        raise

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()


if __name__ == "__main__":
    # Run ingestion once when the table needs to be recreated.
    ingest_csv_to_mysql()

    # Run all 20 SQL business questions.
    run_assignment()
