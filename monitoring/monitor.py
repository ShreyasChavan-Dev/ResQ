
import time
import requests

from datetime import datetime
from collections import deque

from recovery.recovery_manager import RecoveryManager
from dependency.dependency_graph import DependencyGraph


class Service:
    """Represents a service monitored by ResQ."""

    def __init__(
        self,
        name,
        health_url,
        app_module,
        port
    ):
        self.name = name
        self.health_url = health_url
        self.app_module = app_module
        self.port = port

        self.status = "UNKNOWN"
        self.response_time = 0
        self.last_checked = None

        self.total_failures = 0


class MonitoringEngine:
    """Monitors services and manages automatic recovery."""

    def __init__(self):

        self.services = {}

        self.dependency_graph = DependencyGraph()

        self.recovery_manager = RecoveryManager(
            max_attempts=3,
            cooldown_seconds=30
        )

        self.total_failures = 0
        self.successful_recoveries = 0
        self.failed_recoveries = 0

        # Store the latest 100 monitoring and recovery events.
        self.event_history = deque(maxlen=100)

    def record_event(
        self,
        service_name,
        event_type,
        message
    ):
        """Save a timestamped event."""

        event = {
            "timestamp": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "service": service_name,
            "event": event_type,
            "message": message
        }

        self.event_history.append(event)

        print(
            f"[RESQ EVENT] {event['timestamp']} | "
            f"{service_name} | {event_type} | {message}"
        )

    def get_event_history(self):
        """Return the latest events, newest first."""

        return list(reversed(self.event_history))

    def add_service(self, service):

        self.services[service.name] = service

        self.dependency_graph.add_service(
            service.name
        )

        self.record_event(
            service.name,
            "SERVICE_REGISTERED",
            "Service added to monitoring."
        )

    def add_dependency(
        self,
        service_name,
        depends_on
    ):

        self.dependency_graph.add_dependency(
            service_name,
            depends_on
        )

        self.record_event(
            service_name,
            "DEPENDENCY_ADDED",
            f"Depends on {depends_on}."
        )

    def check_health(self, service):

        try:

            start_time = time.time()

            response = requests.get(
                service.health_url,
                timeout=3
            )

            response_time = (
                time.time() - start_time
            ) * 1000

            if response.status_code == 200:

                service.status = "HEALTHY"
                service.response_time = round(
                    response_time,
                    2
                )

                service.last_checked = (
                    datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                )

                return True

            service.status = "FAILED"

        except requests.RequestException:

            service.status = "FAILED"
            service.response_time = 0

        service.last_checked = (
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )

        return False

    def monitor_all(self):
        """Check the health of every registered service."""

        for service in self.services.values():

            healthy = self.check_health(service)

            if healthy:

                print(
                    f"{service.name} - HEALTHY "
                    f"({service.response_time} ms)"
                )

            else:

                print(
                    f"{service.name} - FAILED"
                )

                self.total_failures += 1
                service.total_failures += 1

                self.record_event(
                    service.name,
                    "FAILURE_DETECTED",
                    "Health check failed."
                )

                self.recover_with_dependencies(
                    service.name
                )

    def recover_service(self, service_name):
        """Restart a service using its Python module."""

        import importlib
        import subprocess
        import sys

        service = self.services.get(service_name)

        if service is None:
            return False

        try:

            print(
                f"Attempting recovery for "
                f"{service_name}..."
            )

            # Find and stop the existing service process
            # using its registered port.
            if sys.platform == "win32":

                result = subprocess.run(
                    [
                        "powershell",
                        "-NoProfile",
                        "-Command",
                        (
                            f"$connections = Get-NetTCPConnection "
                            f"-LocalPort {service.port} "
                            f"-State Listen "
                            f"-ErrorAction SilentlyContinue; "
                            f"$connections | ForEach-Object "
                            f"{{ Stop-Process -Id "
                            f"$_.OwningProcess -Force "
                            f"-ErrorAction SilentlyContinue }}"
                        )
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

            time.sleep(2)

            # Start the service again.
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    f"{service.app_module}:app",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(service.port)
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            # Allow the service to initialize.
            time.sleep(3)

            if self.check_health(service):

                print(
                    f"{service_name} recovered successfully!"
                )

                return True

            return False

        except Exception as error:

            print(
                f"Recovery error for {service_name}: "
                f"{error}"
            )

            return False

    def recover_with_dependencies(self, service_name):
        """Recover dependencies before the failed service."""

        print(
            f"Calculating recovery order for "
            f"{service_name}..."
        )

        try:

            recovery_order = (
                self.dependency_graph.get_recovery_order()
            )

        except ValueError as error:

            print("Dependency error:", error)

            self.record_event(
                service_name,
                "DEPENDENCY_ERROR",
                str(error)
            )

            return

        if service_name not in recovery_order:
            return

        target_index = recovery_order.index(
            service_name
        )

        required_services = recovery_order[
            :target_index + 1
        ]

        for current_service in required_services:

            service = self.services.get(
                current_service
            )

            if service is None:
                continue

            if self.check_health(service):

                print(
                    f"{current_service} is already healthy."
                )

                continue

            if not self.recovery_manager.can_recover(
                current_service
            ):

                self.record_event(
                    current_service,
                    "RECOVERY_BLOCKED",
                    "Recovery protection prevented another attempt."
                )

                continue

            self.recovery_manager.record_attempt(
                current_service
            )

            self.record_event(
                current_service,
                "RECOVERY_STARTED",
                "Automatic recovery started."
            )

            recovered = self.recover_service(
                current_service
            )

            if recovered:

                self.recovery_manager.record_success(
                    current_service
                )

                self.successful_recoveries += 1

                self.record_event(
                    current_service,
                    "RECOVERY_SUCCESS",
                    "Service recovered successfully."
                )

            else:

                self.recovery_manager.record_failure(
                    current_service
                )

                self.failed_recoveries += 1

                self.record_event(
                    current_service,
                    "RECOVERY_FAILED",
                    "Automatic recovery failed."
                )

                # Do not recover dependent services
                # if their dependency could not recover.
                break

    def get_statistics(self):

        successful = (
            self.successful_recoveries
        )

        failed = self.failed_recoveries

        total_recoveries = successful + failed

        if total_recoveries > 0:

            success_rate = round(
                (successful / total_recoveries) * 100,
                2
            )

        else:

            success_rate = 0

        recovery_stats = (
            self.recovery_manager.get_statistics()
        )

        return {
            "total_failures": self.total_failures,
            "successful_recoveries": successful,
            "failed_recoveries": failed,
            "blocked_recoveries":
                recovery_stats["blocked_recoveries"],
            "success_rate": success_rate
        }

    def get_dashboard_data(self):

        healthy_services = 0
        failed_services = 0

        service_data = []

        for service in self.services.values():

            if service.status == "HEALTHY":
                healthy_services += 1

            elif service.status == "FAILED":
                failed_services += 1

            service_data.append({
                "name": service.name,
                "port": service.port,
                "health_url": service.health_url,
                "status": service.status,
                "response_time": service.response_time,
                "total_failures": service.total_failures
            })

        statistics = self.get_statistics()

        return {
            "total_services": len(self.services),
            "healthy_services": healthy_services,
            "failed_services": failed_services,
            "services": service_data,
            "total_failures":
                statistics["total_failures"],
            "successful_recoveries":
                statistics["successful_recoveries"],
            "failed_recoveries":
                statistics["failed_recoveries"],
            "blocked_recoveries":
                statistics["blocked_recoveries"],
            "success_rate":
                statistics["success_rate"],
            "event_history":
                self.get_event_history()
        }

    def show_dependencies(self):

        self.dependency_graph.show_graph()

    def show_recovery_statistics(self):

        print("\n===== RESQ RECOVERY STATISTICS =====")

        statistics = self.get_statistics()

        for key, value in statistics.items():

            print(
                key.replace("_", " ").title(),
                ":",
                value
            )

    def get_dependency_graph(self):

        graph = []

        for service_name in sorted(
            self.dependency_graph.graph
        ):

            dependencies = (
                self.dependency_graph.get_dependencies(
                    service_name
                )
            )

            graph.append({
                "service": service_name,
                "dependencies": dependencies
            })

        return graph
