import unittest
import sqlite3
import os
from pathlib import Path

class TestDatabaseIntegrity(unittest.TestCase):

    def setUp(self):
        root_dir = Path(__file__).resolve().parent.parent
        self.db_path = root_dir / "ridewise.db"
        if not self.db_path.exists():
            self.db_path = root_dir / "ridewise-assist" / "ridewise.db"

    def test_database_file_exists(self):
        """Verify SQLite database file exists and is populated."""
        self.assertTrue(self.db_path.exists(), f"Database not found at {self.db_path}")
        self.assertGreater(os.path.getsize(self.db_path), 10000, "Database file is empty or placeholder.")

    def test_database_integrity_check(self):
        """Verify PRAGMA integrity_check returns ok."""
        db_uri = self.db_path.as_uri() + "?mode=ro"
        with sqlite3.connect(db_uri, uri=True) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()[0]
            self.assertEqual(result, "ok", "Database integrity check failed.")

    def test_table_row_counts(self):
        """Verify expected record counts across all 5 core domain tables."""
        expected_counts = {
            "customers": 200,
            "vehicles": 60,
            "bookings": 1800,
            "payments": 3289,
            "damage_reports": 80
        }
        db_uri = self.db_path.as_uri() + "?mode=ro"
        with sqlite3.connect(db_uri, uri=True) as conn:
            cursor = conn.cursor()
            for table, expected in expected_counts.items():
                cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
                actual = cursor.fetchone()[0]
                self.assertEqual(actual, expected, f"Table {table} row count mismatch: expected {expected}, got {actual}")

    def test_foreign_key_integrity(self):
        """Verify no foreign key constraint violations exist in any table."""
        tables = ["customers", "vehicles", "bookings", "payments", "damage_reports"]
        db_uri = self.db_path.as_uri() + "?mode=ro"
        with sqlite3.connect(db_uri, uri=True) as conn:
            cursor = conn.cursor()
            for table in tables:
                cursor.execute(f'PRAGMA foreign_key_check("{table}")')
                violations = cursor.fetchall()
                self.assertEqual(len(violations), 0, f"Foreign key violations found in table {table}: {violations}")

if __name__ == "__main__":
    unittest.main()
