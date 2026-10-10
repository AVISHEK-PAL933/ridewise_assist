import unittest
import pandas as pd
import os

from excel_engine import ExcelEngine

class TestExcelEngine(unittest.TestCase):

    def setUp(self):
        self.engine = ExcelEngine()

    def test_01_excel_loading_and_summary(self):
        """Verify ridewise_data.xlsx loads all 5 sheets and returns metadata summary."""
        summary = self.engine.get_summary()
        self.assertIn("customers", summary)
        self.assertIn("vehicles", summary)
        self.assertIn("bookings", summary)
        self.assertIn("payments", summary)
        self.assertIn("damage_reports", summary)

        self.assertEqual(summary["customers"]["rows"], 200)
        self.assertEqual(summary["vehicles"]["rows"], 60)
        self.assertEqual(summary["bookings"]["rows"], 1800)
        self.assertEqual(summary["payments"]["rows"], 3289)
        self.assertEqual(summary["damage_reports"]["rows"], 80)

    def test_02_excel_deterministic_queries(self):
        """Verify deterministic pandas operations for sums, counts, and averages."""
        df_sum, exp_sum, meta_sum = self.engine.query_excel("total payments", role="support_agent")
        self.assertIsNotNone(df_sum)
        self.assertIn("Grand Total Paid (INR)", df_sum.columns)
        self.assertGreater(df_sum.iloc[0]["Grand Total Paid (INR)"], 0.0)

        df_cnt, exp_cnt, meta_cnt = self.engine.query_excel("how many total bookings", role="support_agent")
        self.assertIsNotNone(df_cnt)
        self.assertEqual(df_cnt.iloc[0]["Record Count"], 1800)

    def test_03_excel_customer_scoping(self):
        """Verify Excel engine enforces customer ID scoping."""
        df_cust, exp_cust, meta_cust = self.engine.query_excel("total payments", role="customer", customer_id="CUST0001")
        self.assertIsNotNone(df_cust)
        self.assertEqual(meta_cust["role_scope"], "CUSTOMER (CUST0001)")
        self.assertLess(meta_cust["total_rows_evaluated"], 3289, "Customer scope should filter payment records.")

if __name__ == "__main__":
    unittest.main()
