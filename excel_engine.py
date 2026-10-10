import pandas as pd
import numpy as np
import os
import re

EXCEL_PATH = "ridewise_data.xlsx"

def get_excel_path():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        "ridewise_data.xlsx",
        "ridewise-assist/ridewise_data.xlsx",
        "../ridewise_data.xlsx",
        os.path.join(base_dir, "ridewise_data.xlsx"),
        os.path.join(base_dir, "ridewise-assist", "ridewise_data.xlsx"),
        os.path.join(base_dir, "..", "ridewise_data.xlsx")
    ]
    for p in candidates:
        if os.path.exists(p) and os.path.getsize(p) > 1000:
            return p
    return EXCEL_PATH

class ExcelEngine:
    def __init__(self, excel_path: str = None):
        self.excel_path = excel_path or get_excel_path()
        self.sheets = {}
        self.load_workbook()

    def load_workbook(self):
        """Loads ridewise_data.xlsx sheets safely using pandas and openpyxl."""
        if not os.path.exists(self.excel_path):
            return
        try:
            xl = pd.ExcelFile(self.excel_path)
            for sheet in xl.sheet_names:
                df = pd.read_excel(xl, sheet_name=sheet)
                self.sheets[sheet] = df
        except Exception as e:
            print(f"Error loading Excel workbook: {e}")

    def get_summary(self):
        """Returns metadata summary of sheets, shapes, and column names."""
        summary = {}
        for name, df in self.sheets.items():
            summary[name] = {
                "rows": len(df),
                "cols": len(df.columns),
                "columns": list(df.columns),
                "null_counts": df.isnull().sum().to_dict(),
                "preview": df.head(3)
            }
        return summary

    def query_excel(self, query: str, role: str = "support_agent", customer_id: str = None):
        """Executes deterministic pandas operations on Excel sheets based on query intent."""
        if not self.sheets:
            return None, "Excel workbook is not loaded or missing.", {}

        q_lower = query.lower()
        explanation = ""
        result_df = None

        # Determine target sheet
        target_sheet = "bookings"
        if "customer" in q_lower or "tier" in q_lower or "kyc" in q_lower:
            target_sheet = "customers"
        elif "vehicle" in q_lower or "hub" in q_lower or "battery" in q_lower or "model" in q_lower:
            target_sheet = "vehicles"
        elif "payment" in q_lower or "gst" in q_lower or "paid" in q_lower or "refund" in q_lower:
            target_sheet = "payments"
        elif "damage" in q_lower or "penalty" in q_lower or "severity" in q_lower:
            target_sheet = "damage_reports"

        df = self.sheets[target_sheet].copy()

        # Enforce Customer Security Scoping
        if role == "customer" and customer_id:
            if target_sheet == "customers":
                df = df[df['customer_id'].astype(str).str.upper() == customer_id.upper()]
            elif target_sheet == "bookings":
                df = df[df['customer_id'].astype(str).str.upper() == customer_id.upper()]
            elif target_sheet == "payments":
                b_df = self.sheets['bookings']
                cust_b_ids = b_df[b_df['customer_id'].astype(str).str.upper() == customer_id.upper()]['booking_id']
                df = df[df['booking_id'].isin(cust_b_ids)]
            elif target_sheet == "damage_reports":
                b_df = self.sheets['bookings']
                cust_b_ids = b_df[b_df['customer_id'].astype(str).str.upper() == customer_id.upper()]['booking_id']
                df = df[df['booking_id'].isin(cust_b_ids)]

            if df.empty:
                return None, f"No Excel records found matching your customer ID ({customer_id}).", {"sheet": target_sheet}

        # Deterministic Analysis Operations
        if "count" in q_lower or "how many" in q_lower or "number of" in q_lower:
            count_val = len(df)
            result_df = pd.DataFrame([{"Record Count": count_val, "Target Sheet": target_sheet}])
            explanation = f"Counted total rows in Excel sheet '{target_sheet}'."
        elif "sum" in q_lower or "total" in q_lower or "amount" in q_lower:
            if target_sheet == "payments":
                df['total_paid'] = df['amount'] + df['gst_amount']
                total_sum = df['total_paid'].sum()
                result_df = pd.DataFrame([{
                    "Total Base Amount (INR)": round(df['amount'].sum(), 2),
                    "Total GST 18% (INR)": round(df['gst_amount'].sum(), 2),
                    "Grand Total Paid (INR)": round(total_sum, 2)
                }])
                explanation = f"Calculated deterministic sum across {len(df)} payment rows in Excel sheet '{target_sheet}'."
            elif "assessed_cost" in df.columns:
                total_cost = df['assessed_cost'].sum()
                result_df = pd.DataFrame([{"Total Damage Assessed Cost (INR)": round(total_cost, 2)}])
                explanation = f"Summed assessed damage costs across {len(df)} records in sheet '{target_sheet}'."
            else:
                result_df = df.head(10)
                explanation = f"Retrieved top rows from sheet '{target_sheet}'."
        elif "average" in q_lower or "mean" in q_lower or "avg" in q_lower:
            num_cols = df.select_dtypes(include=[np.number]).columns
            if len(num_cols) > 0:
                avg_df = df[num_cols].mean().round(2).to_frame("Average Value").reset_index()
                result_df = avg_df
                explanation = f"Computed arithmetic averages for numerical columns in sheet '{target_sheet}'."
            else:
                result_df = df.head(10)
                explanation = f"Preview of sheet '{target_sheet}'."
        else:
            result_df = df.head(10)
            explanation = f"Extracted matching rows from Excel sheet '{target_sheet}'."

        meta = {
            "source_file": "ridewise_data.xlsx",
            "sheet_used": target_sheet,
            "total_rows_evaluated": len(df),
            "role_scope": f"CUSTOMER ({customer_id})" if role == "customer" else "SUPPORT AGENT"
        }

        return result_df, explanation, meta
