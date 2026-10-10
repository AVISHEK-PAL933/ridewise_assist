import unittest
import pandas as pd
import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from db_engine import execute_sql

class TestDBEngine(unittest.TestCase):

    def test_valid_select_queries(self):
        """Verify standard SELECT queries execute successfully and return DataFrames."""
        df, err = execute_sql("SELECT COUNT(*) AS total FROM customers;")
        self.assertIsNone(err)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(df.iloc[0]['total'], 200)

    def test_blocked_mutations(self):
        """Verify DML/DDL queries are strictly blocked by read-only validator."""
        forbidden_queries = [
            "INSERT INTO customers (customer_id, full_name) VALUES ('HACKER', 'Test');",
            "UPDATE customers SET full_name = 'Hacked' WHERE customer_id = 'CUST0001';",
            "DELETE FROM bookings WHERE booking_id = 'B001';",
            "DROP TABLE damage_reports;",
            "ALTER TABLE vehicles ADD COLUMN test_col TEXT;",
            "CREATE TABLE hack (id INT);"
        ]
        for query in forbidden_queries:
            df, err = execute_sql(query)
            self.assertIsNone(df, f"Query should have returned None DataFrame: {query}")
            self.assertIsNotNone(err, f"Query should have returned error: {query}")
            self.assertIn("Forbidden", err)

    def test_blocked_multi_statement_injection(self):
        """Verify multi-statement semicolon injections are caught and blocked."""
        injection = "SELECT COUNT(*) FROM customers; DROP TABLE payments;"
        df, err = execute_sql(injection)
        self.assertIsNone(df)
        self.assertIsNotNone(err)
        self.assertIn("Forbidden", err)

    def test_blocked_pragma_and_attach(self):
        """Verify PRAGMA and ATTACH commands are blocked."""
        df_pragma, err_pragma = execute_sql("PRAGMA user_version;")
        self.assertIsNone(df_pragma)
        self.assertIsNotNone(err_pragma)

        df_attach, err_attach = execute_sql("ATTACH DATABASE 'evil.db' AS evil;")
        self.assertIsNone(df_attach)
        self.assertIsNotNone(err_attach)

if __name__ == "__main__":
    unittest.main()
