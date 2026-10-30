
import time
from datetime import datetime


class RecoveryManager:
    """
    Manages intelligent service recovery.

    Features:
    - Tracks recovery attempts.
    - Prevents excessive restart attempts.
    - Uses cooldown periods.
    - Tracks successful and failed recoveries.
    """

    def __init__(
        self,
        max_attempts=3,
        cooldown_seconds=30
    ):
        self.max_attempts = max_attempts
        self.cooldown_seconds = cooldown_seconds

        self.recovery_history = {}
        self.last_recovery_time = {}

        self.successful_recoveries = 0
        self.failed_recoveries = 0
        self.blocked_recoveries = 0

    def can_recover(self, service_name):
        """Check whether a service is allowed to recover."""

        current_time = time.time()

        history = self.recovery_history.get(
            service_name,
            []
        )

        # Keep only attempts from the last 60 seconds.
        recent_attempts = [
            attempt
            for attempt in history
            if current_time - attempt < 60
        ]

        self.recovery_history[service_name] = (
            recent_attempts
        )

        # Prevent too many recovery attempts.
        if len(recent_attempts) >= self.max_attempts:
            self.blocked_recoveries += 1

            print(
                f"[RESQ WARNING] Recovery blocked for "
                f"{service_name}: too many attempts."
            )

            return False

        # Apply cooldown after the previous recovery.
        last_time = self.last_recovery_time.get(
            service_name
        )

        if last_time is not None:

            elapsed = current_time - last_time

            if elapsed < self.cooldown_seconds:

                remaining = int(
                    self.cooldown_seconds - elapsed
                ) + 1

                print(
                    f"[RESQ INFO] {service_name} is in "
                    f"cooldown. Try again in "
                    f"{remaining} seconds."
                )

                return False

        return True

    def record_attempt(self, service_name):
        """Record a recovery attempt."""

        current_time = time.time()

        self.recovery_history.setdefault(
            service_name,
            []
        ).append(current_time)

        self.last_recovery_time[service_name] = (
            current_time
        )

        print(
            f"[RESQ] Recovery attempt recorded for "
            f"{service_name} at "
            f"{datetime.now().strftime('%H:%M:%S')}"
        )

    def record_success(self, service_name):
        """Record a successful recovery."""

        self.successful_recoveries += 1

        print(
            f"[RESQ SUCCESS] {service_name} recovered."
        )

    def record_failure(self, service_name):
        """Record a failed recovery."""

        self.failed_recoveries += 1

        print(
            f"[RESQ ERROR] Recovery failed for "
            f"{service_name}."
        )

    def get_statistics(self):
        """Return recovery statistics."""

        return {
            "successful_recoveries":
                self.successful_recoveries,

            "failed_recoveries":
                self.failed_recoveries,

            "blocked_recoveries":
                self.blocked_recoveries
        }
