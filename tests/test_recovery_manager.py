
import unittest
from unittest.mock import patch

from recovery.recovery_manager import RecoveryManager


class TestRecoveryManager(unittest.TestCase):

    def setUp(self):
        self.manager = RecoveryManager(
            max_attempts=3,
            cooldown_seconds=30
        )

    @patch("recovery.recovery_manager.time.time")
    def test_recovery_allowed_initially(self, mock_time):
        mock_time.return_value = 1000

        self.assertTrue(
            self.manager.can_recover("Backend")
        )

    @patch("recovery.recovery_manager.time.time")
    def test_cooldown_blocks_recovery(self, mock_time):
        mock_time.return_value = 1000
        self.manager.record_attempt("Backend")

        mock_time.return_value = 1010

        self.assertFalse(
            self.manager.can_recover("Backend")
        )

    @patch("recovery.recovery_manager.time.time")
    def test_recovery_allowed_after_cooldown(self, mock_time):
        mock_time.return_value = 1000
        self.manager.record_attempt("Backend")

        mock_time.return_value = 1031

        self.assertTrue(
            self.manager.can_recover("Backend")
        )

    @patch("recovery.recovery_manager.time.time")
    def test_maximum_attempts_are_enforced(self, mock_time):
        mock_time.return_value = 1000

        for _ in range(3):
            self.manager.record_attempt("Backend")

        # Check while all three attempts are still recent.
        mock_time.return_value = 1001

        self.assertFalse(
            self.manager.can_recover("Backend")
        )

        self.assertEqual(
            self.manager.blocked_recoveries,
            1
        )

    def test_recovery_statistics(self):
        self.manager.record_success("Backend")
        self.manager.record_failure("Payment")

        statistics = self.manager.get_statistics()

        self.assertEqual(
            statistics["successful_recoveries"],
            1
        )

        self.assertEqual(
            statistics["failed_recoveries"],
            1
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
