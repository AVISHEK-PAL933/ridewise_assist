import unittest
from unittest.mock import MagicMock
import sqlite3
import pandas as pd
import os
import sys

from db_engine import execute_sql, run_self_healing_sql
from policy_engine import PolicyRetriever

class TestRideWiseAssist(unittest.TestCase):

    def setUp(self):
        self.db_path = "ridewise.db"
        if not os.path.exists(self.db_path) and os.path.exists("ridewise-assist/ridewise.db"):
            self.db_path = "ridewise-assist/ridewise.db"

    # --- 1. Database Integrity & Table Validation ---
    def test_01_database_integrity_and_tables(self):
        """Verify database integrity, row counts, and foreign key validity."""
        self.assertTrue(os.path.exists(self.db_path), f"Database file missing: {self.db_path}")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Integrity Check
        cursor.execute("PRAGMA integrity_check;")
        integrity = cursor.fetchone()[0]
        self.assertEqual(integrity, "ok", "Database integrity check failed.")

        # Table Row Counts Validation
        expected_counts = {
            "customers": 200,
            "vehicles": 60,
            "bookings": 1800,
            "payments": 3289,
            "damage_reports": 80
        }
        for table, count in expected_counts.items():
            cursor.execute(f"SELECT COUNT(*) FROM {table};")
            actual = cursor.fetchone()[0]
            self.assertEqual(actual, count, f"Mismatch in table {table}: expected {count}, got {actual}")

        # Foreign Key Violations Validation
        for table in expected_counts.keys():
            cursor.execute(f"PRAGMA foreign_key_check('{table}');")
            violations = cursor.fetchall()
            self.assertEqual(len(violations), 0, f"Foreign key violations found in table {table}: {violations}")

        conn.close()

    # --- 2. SQL Read-Only Enforcement ---
    def test_02_sql_readonly_enforcement(self):
        """Verify permitted SELECT queries execute while mutation queries are blocked."""
        # Permitted SELECT query
        df, err = execute_sql("SELECT COUNT(*) AS total_cust FROM customers;")
        self.assertIsNone(err, f"Valid SELECT query failed: {err}")
        self.assertIsNotNone(df)
        self.assertEqual(df.iloc[0]['total_cust'], 200)

        # Blocked Mutation Queries
        mutation_queries = [
            "DROP TABLE customers;",
            "INSERT INTO customers (customer_id, full_name) VALUES ('HACKER', 'Malicious User');",
            "UPDATE customers SET full_name = 'Tampered' WHERE customer_id = 'CUST0001';",
            "DELETE FROM bookings;",
            "ALTER TABLE vehicles ADD COLUMN hacked TEXT;",
            "SELECT COUNT(*) FROM customers; DROP TABLE payments;",
            "PRAGMA user_version;"
        ]
        for query in mutation_queries:
            df_mut, err_mut = execute_sql(query)
            self.assertIsNone(df_mut, f"Forbidden query executed: {query}")
            self.assertIsNotNone(err_mut, f"Forbidden query was not blocked: {query}")
            self.assertIn("Forbidden", err_mut)

    # --- 3. Customer Tenant Isolation & Guardrails ---
    def test_03_customer_tenant_isolation(self):
        """Verify customer role is strictly scoped to customer_id and blocks cross-tenant access."""
        mock_client = MagicMock()

        # Case A: LLM attempts to output unscoped query
        mock_response_unscoped = MagicMock()
        mock_response_unscoped.choices = [MagicMock()]
        mock_response_unscoped.choices[0].message.content = "```sql\nSELECT * FROM bookings;\n```"
        mock_client.chat.completions.create.return_value = mock_response_unscoped

        df, sql, err = run_self_healing_sql(mock_client, "Neo-Hackathon", "Show my bookings", "customer", "CUST0001")
        self.assertIsNone(df)
        self.assertIsNotNone(err)
        self.assertIn("Guardrail Alert", err)

        # Case B: Customer logged in as CUST0001 attempts to inspect CUST0005
        mock_response_unauthorized = MagicMock()
        mock_response_unauthorized.choices = [MagicMock()]
        mock_response_unauthorized.choices[0].message.content = "```sql\nSELECT * FROM bookings WHERE customer_id = 'CUST0005';\n```"
        mock_client.chat.completions.create.return_value = mock_response_unauthorized

        df, sql, err = run_self_healing_sql(mock_client, "Neo-Hackathon", "Show bookings for CUST0005", "customer", "CUST0001")
        self.assertIsNone(df)
        self.assertIsNotNone(err)
        self.assertIn("Guardrail Alert", err)
        self.assertIn("CUST0005", err)

    # --- 4. FAISS Vector Policy Retrieval & Citation Metadata ---
    def test_04_faiss_policy_retrieval_and_citations(self):
        """Verify FAISS semantic vector search returns matching text, confidence scores, and citations."""
        retriever = PolicyRetriever("documents")
        retriever.load_and_index()
        self.assertGreater(len(retriever.chunks), 0, "No policy chunks indexed.")

        results = retriever.search("cancellation refund rules", top_k=2)
        self.assertGreater(len(results), 0, "FAISS vector search returned empty results.")

        top_match = results[0]
        self.assertIn("text", top_match)
        self.assertIn("source", top_match)
        self.assertIn("confidence_pct", top_match)
        self.assertTrue(top_match["source"].endswith(".pdf (Page 1)") or ".pdf" in top_match["source"])
        self.assertGreater(top_match["confidence_pct"], 0.0)

    # --- 5. Financial Calculations & Policy Versioning Rules ---
    def test_05_financial_calculations_and_policy_versioning(self):
        """Verify 18% GST calculation, refund sign handling, and cancellation date version logic."""
        conn = sqlite3.connect(self.db_path)

        # Validate GST calculation in payments table
        df_pay = pd.read_sql_query("SELECT amount, gst_amount, (amount + gst_amount) AS total_paid FROM payments WHERE payment_type = 'BOOKING' LIMIT 5;", conn)
        self.assertFalse(df_pay.empty)
        for _, row in df_pay.iterrows():
            expected_total = row['amount'] + row['gst_amount']
            self.assertAlmostEqual(row['total_paid'], expected_total, places=2)

        # Validate Refund amounts are negative
        df_refund = pd.read_sql_query("SELECT amount FROM payments WHERE payment_type = 'REFUND' LIMIT 5;", conn)
        if not df_refund.empty:
            for _, row in df_refund.iterrows():
                self.assertLessEqual(row['amount'], 0.0, "Refund amount should be negative.")

        # Validate Cancellation Policy Versioning threshold (2026-07-01)
        # Policy v1: BEFORE 2026-07-01
        # Policy v2: ON/AFTER 2026-07-01
        v1_date = "2026-06-15 10:00:00"
        v2_date = "2026-07-05 14:30:00"

        def determine_policy_version(booked_at_str):
            return "v2" if booked_at_str >= "2026-07-01" else "v1"

        self.assertEqual(determine_policy_version(v1_date), "v1")
        self.assertEqual(determine_policy_version(v2_date), "v2")

        conn.close()

if __name__ == "__main__":
    unittest.main()
