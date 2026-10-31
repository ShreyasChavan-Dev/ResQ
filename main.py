import json
import time
from pathlib import Path

from monitoring.monitor import Service, MonitoringEngine


# Shared folder used by the dashboard and monitor containers.
DATA_DIR = Path("/app/runtime")
DATA_DIR.mkdir(parents=True, exist_ok=True)

STATS_FILE = DATA_DIR / "resq_runtime_stats.json"
EVENTS_FILE = DATA_DIR / "resq_event_history.json"


# Create the monitoring engine.
resq = MonitoringEngine()

# Docker Compose service names are used as hostnames.
resq.add_service(
    Service(
        name="Backend",
        health_url="http://backend:8001/health",
        app_module="backend_service",
        port=8001
    )
)

resq.add_service(
    Service(
        name="Payment",
        health_url="http://payment:8002/health",
        app_module="payment_service",
        port=8002
    )
)

# Payment depends on Backend.
resq.add_dependency(
    service_name="Payment",
    depends_on="Backend"
)


def save_runtime_data():
    """Save monitoring statistics and event history."""

    stats = resq.get_dashboard_data()

    with open(STATS_FILE, "w", encoding="utf-8") as file:
        json.dump(stats, file, indent=4)

    with open(EVENTS_FILE, "w", encoding="utf-8") as file:
        json.dump(
            resq.get_event_history(),
            file,
            indent=4
        )


def main():
    print("===================================")
    print("       RESQ MONITOR STARTED")
    print("===================================")

    while True:
        try:
            print("\n[RESQ] Checking all services...")

            resq.monitor_all()
            save_runtime_data()

            print("[RESQ] Monitoring cycle completed.")

        except Exception as error:
            print(f"[RESQ ERROR] Monitoring error: {error}")

        time.sleep(5)


if __name__ == "__main__":
    main()