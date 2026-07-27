import unittest
from plexai_verify.core.domain.models import LibraryStats

class LibraryStatsTests(unittest.TestCase):
    def test_health_is_100_without_problem(self):
        self.assertEqual(LibraryStats(total=100).health_score, 100.0)
    def test_errors_are_weighted(self):
        stats=LibraryStats(total=100, errors=2, mismatches=1, quality_alerts=2)
        self.assertAlmostEqual(stats.health_score, 90.0)
    def test_empty_library_is_safe(self):
        self.assertEqual(LibraryStats().health_score, 100.0)

if __name__=='__main__': unittest.main()
