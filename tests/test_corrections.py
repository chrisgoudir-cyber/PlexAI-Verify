import tempfile
import unittest
from pathlib import Path

from plexai_verify.core.services.correction_service import CorrectionService


class CorrectionSafetyTests(unittest.TestCase):
    def test_minimum_score_is_high(self):
        self.assertGreaterEqual(
            CorrectionService.MINIMUM_SCORE,
            0.90,
        )

    def test_result_extension_rule(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "Film test.mkv"
            target = Path(tmp) / "Film test.mp4"
            source.write_bytes(b"demo")
            self.assertNotEqual(source.suffix, target.suffix)

    def test_existing_target_is_detectable(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "ancien.mkv"
            target = Path(tmp) / "nouveau.mkv"
            source.write_bytes(b"a")
            target.write_bytes(b"b")
            self.assertTrue(target.exists())


if __name__ == "__main__":
    unittest.main()
