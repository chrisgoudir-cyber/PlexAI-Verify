import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKERS = (ROOT / "src" / "plexai_verify" / "app" / "workers.py").read_text(encoding="utf-8")
MODERN = (ROOT / "src" / "plexai_verify" / "app" / "modern_window.py").read_text(encoding="utf-8")


class AllInOneSafetyTests(unittest.TestCase):
    def test_minimum_confidence_is_95_percent(self):
        self.assertIn("MINIMUM_CONFIDENCE = 0.95", WORKERS)

    def test_worker_exists(self):
        self.assertIn("class AllInOneWorker(BaseWorker):", WORKERS)

    def test_automatic_rename_requires_mismatch(self):
        self.assertIn(
            'result.get("status") == "mismatch"',
            WORKERS,
        )

    def test_no_delete_operation_in_worker(self):
        worker_source = WORKERS.split(
            "class AllInOneWorker(BaseWorker):", 1
        )[1]
        self.assertNotIn(".unlink(", worker_source)
        self.assertNotIn(".rmdir(", worker_source)

    def test_button_is_visible(self):
        self.assertIn("TOUT VÉRIFIER ET CORRIGER", MODERN)


if __name__ == "__main__":
    unittest.main()
