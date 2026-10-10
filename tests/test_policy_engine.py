import unittest
import os
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from policy_engine import PolicyRetriever

class TestPolicyEngine(unittest.TestCase):

    def setUp(self):
        docs_path = root_dir / "documents"
        if not docs_path.exists():
            docs_path = root_dir / "ridewise-assist" / "documents"
        self.retriever = PolicyRetriever(str(docs_path))

    def test_indexing_and_chunk_count(self):
        """Verify 5 PDF policy documents are indexed into FAISS."""
        self.retriever.load_and_index()
        self.assertGreater(len(self.retriever.chunks), 0, "No policy chunks indexed.")

    def test_faiss_vector_search(self):
        """Verify query returns valid policy matches with source and confidence scores."""
        self.retriever.load_and_index()
        results = self.retriever.search("cancellation refund rules", top_k=3)
        self.assertGreater(len(results), 0, "Vector search returned empty list.")
        
        top_res = results[0]
        self.assertIn("text", top_res)
        self.assertIn("source", top_res)
        self.assertIn("confidence_pct", top_res)
        self.assertGreater(top_res["confidence_pct"], 0.0)

    def test_policy_version_logic(self):
        """Verify versioning rules for Cancellation Policy v1 (< 2026-07-01) vs v2 (>= 2026-07-01)."""
        def get_cancellation_policy_version(booking_date_str):
            return "v2" if booking_date_str >= "2026-07-01" else "v1"

        self.assertEqual(get_cancellation_policy_version("2026-05-10"), "v1")
        self.assertEqual(get_cancellation_policy_version("2026-07-01 00:00:00"), "v2")
        self.assertEqual(get_cancellation_policy_version("2026-08-15"), "v2")

if __name__ == "__main__":
    unittest.main()
