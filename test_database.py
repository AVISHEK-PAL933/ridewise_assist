
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "ridewise.db"

EXPECTED_TABLES = {
    "customers": 200,
    "vehicles": 60,
    "bookings": 1800,
    "payments": 3289,
    "damage_reports": 80,
}

def test_database():
    if not DB_PATH.exists():
        print(f"FAIL: Database not found at {DB_PATH}")
        return

    # Open the database in read-only mode
    db_uri = DB_PATH.as_uri() + "?mode=ro"

    try:
        with sqlite3.connect(db_uri, uri=True) as conn:
            cursor = conn.cursor()

            # Check database integrity
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()[0]
            print(f"Database integrity: {result}")

            # List available tables
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type = 'table'
                AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)
            tables = {row[0] for row in cursor.fetchall()}

            print("\n--- TABLE VALIDATION ---")

            for table, expected_count in EXPECTED_TABLES.items():
                if table not in tables:
                    print(f"FAIL: Missing table {table}")
                    continue

                # Table names come from our fixed allowlist above.
                cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
                actual_count = cursor.fetchone()[0]

                status = "PASS" if actual_count == expected_count else "CHECK"
                print(
                    f"{status}: {table}: {actual_count} records "
                    f"(expected {expected_count})"
                )

            unexpected = tables - set(EXPECTED_TABLES)
            if unexpected:
                print(f"\nAdditional tables found: {sorted(unexpected)}")

            # Check foreign key consistency
            print("\n--- FOREIGN KEY VALIDATION ---")
            for table in EXPECTED_TABLES:
                cursor.execute(f'PRAGMA foreign_key_check("{table}")')
                violations = cursor.fetchall()
                print(
                    f"{'PASS' if not violations else 'FAIL'}: "
                    f"{table}: {len(violations)} foreign-key violations"
                )

    except sqlite3.Error as exc:
        print(f"DATABASE ERROR: {exc}")


if __name__ == "__main__":
    test_database()
