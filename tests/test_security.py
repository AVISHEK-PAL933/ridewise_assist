import unittest
from unittest.mock import MagicMock
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from db_engine import run_self_healing_sql

class TestSecurityGuardrails(unittest.TestCase):

    def setUp(self):
        self.mock_client = MagicMock()
        self.deployment = "Neo-Hackathon"

    def test_unscoped_customer_query_blocked(self):
        """Verify LLM generated queries lacking customer_id filter for customer role are blocked."""
        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock()]
        mock_resp.choices[0].message.content = "```sql\nSELECT * FROM bookings;\n```"
        self.mock_client.chat.completions.create.return_value = mock_resp

        df, sql, err = run_self_healing_sql(
            client=self.mock_client,
            model_name=self.deployment,
            query="Show all bookings",
            role="customer",
            customer_id="CUST0001"
        )
        self.assertIsNone(df)
        self.assertIsNotNone(err)
        self.assertIn("Guardrail Alert", err)

    def test_cross_tenant_customer_access_blocked(self):
        """Verify logged-in customer CUST0001 cannot query data belonging to CUST0005."""
        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock()]
        mock_resp.choices[0].message.content = "```sql\nSELECT * FROM bookings WHERE customer_id = 'CUST0005';\n```"
        self.mock_client.chat.completions.create.return_value = mock_resp

        df, sql, err = run_self_healing_sql(
            client=self.mock_client,
            model_name=self.deployment,
            query="Show bookings for CUST0005",
            role="customer",
            customer_id="CUST0001"
        )
        self.assertIsNone(df)
        self.assertIsNotNone(err)
        self.assertIn("Guardrail Alert", err)
        self.assertIn("CUST0005", err)

    def test_support_agent_cross_customer_access_allowed(self):
        """Verify support agent role can query across all customer records."""
        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock()]
        mock_resp.choices[0].message.content = "```sql\nSELECT COUNT(*) FROM customers;\n```"
        self.mock_client.chat.completions.create.return_value = mock_resp

        df, sql, err = run_self_healing_sql(
            client=self.mock_client,
            model_name=self.deployment,
            query="Show total customer count",
            role="support_agent",
            customer_id=None
        )
        self.assertIsNotNone(df)
        self.assertIsNone(err)

if __name__ == "__main__":
    unittest.main()
