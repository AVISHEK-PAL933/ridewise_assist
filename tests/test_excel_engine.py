import unittest
import pandas as pd
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from excel_engine import ExcelEngine

class TestExcelEngine(unittest.TestCase):

    def setUp(self):
        excel_path = root_dir / "ridewise_data.xlsx"
        self.engine = ExcelEngine(str(excel_path))

    def test_excel_sheet_loading_and_summary(self):
        """Verify ridewise_data.xlsx loads all 5 expected sheets with correct row counts."""
        summary = self.engine.get_summary()
        expected_sheets = ["customers", "vehicles", "bookings", "payments", "damage_reports"]
        for sheet in expected_sheets:
            self.assertIn(sheet, summary)

        self.assertEqual(summary["customers"]["rows"], 200)
        self.assertEqual(summary["vehicles"]["rows"], 60)
        self.assertEqual(summary["bookings"]["rows"], 1800)
        self.assertEqual(summary["payments"]["rows"], 3289)
        self.assertEqual(summary["damage_reports"]["rows"], 80)

    def test_deterministic_sums_and_counts(self):
        """Verify pandas deterministic calculations for totals and record counts."""
        # Sum
        df_sum, exp_sum, meta_sum = self.engine.query_excel("total payments", role="support_agent")
        self.assertIsNotNone(df_sum)
        self.assertIn("Grand Total Paid (INR)", df_sum.columns)
        self.assertGreater(df_sum.iloc[0]["Grand Total Paid (INR)"], 0.0)

        # Count
        df_cnt, exp_cnt, meta_cnt = self.engine.query_excel("how many total bookings", role="support_agent")
        self.assertIsNotNone(df_cnt)
        self.assertEqual(df_cnt.iloc[0]["Record Count"], 1800)

    def test_excel_customer_scoping(self):
        """Verify Excel queries filter payment records when scoped to a customer ID."""
        df_cust, exp_cust, meta_cust = self.engine.query_excel("total payments", role="customer", customer_id="CUST0001")
        self.assertIsNotNone(df_cust)
        self.assertEqual(meta_cust["role_scope"], "CUSTOMER (CUST0001)")
        self.assertLess(meta_cust["total_rows_evaluated"], 3289)

if __name__ == "__main__":
    unittest.main()
