
import json
import time
from pathlib import Path

from monitoring.monitor import Service, MonitoringEngine


PROJECT_DIR = Path(__file__).resolve().parent

STATS_FILE = PROJECT_DIR / "resq_runtime_stats.json"
EVENTS_FILE = PROJECT_DIR / "resq_event_history.json"


resq = MonitoringEngine()


resq.add_service(
    Service(
        name="Backend",
        health_url="http://127.0.0.1:8001/health",
        app_module="backend_service",
        port=8001
    )
)


resq.add_service(
    Service(
        name="Payment",
        health_url="http://127.0.0.1:8002/health",
        app_module="payment_service",
        port=8002
    )
)


resq.add_dependency(
    service_name="Payment",
    depends_on="Backend"
)


def save_runtime_data():

    try:

        statistics = resq.get_statistics()

        with open(STATS_FILE, "w") as file:

            json.dump(
                statistics,
                file,
                indent=4
            )

        with open(EVENTS_FILE, "w") as file:

            json.dump(
                resq.get_event_history(),
                file,
                indent=4
            )

    except (OSError, ValueError) as error:

        print(
            "Could not save ResQ runtime data:",
            error
        )


resq.show_dependencies()


print("\n====================================")
print("       ResQ Monitoring System")
print("====================================")

print("Backend Service: Port 8001")
print("Payment Service: Port 8002")
print("Dependency-Aware Recovery: Enabled")
print("Intelligent Recovery Protection: Enabled")
print("Maximum Attempts: 3")
print("Cooldown: 30 seconds")
print("Monitoring interval: 5 seconds")
print("Automatic recovery: Enabled")
print("Event History: Enabled")
print("Press Ctrl + C to stop.\n")


try:

    while True:

        resq.monitor_all()

        save_runtime_data()

        time.sleep(5)


except KeyboardInterrupt:

    print("\nResQ monitoring stopped.")

    save_runtime_data()

    resq.show_recovery_statistics()
