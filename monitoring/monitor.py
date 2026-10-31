
import time
from datetime import datetime
from collections import deque

import requests
import docker

from recovery.recovery_manager import RecoveryManager
from dependency.dependency_graph import DependencyGraph


class Service:
    """Stores information about a monitored service."""

    def __init__(
        self,
        name,
        health_url,
        app_module,
        port,
        container_name=None
    ):
        self.name = name
        self.health_url = health_url
        self.app_module = app_module
        self.port = port
        self.container_name = container_name or {
            "Backend": "resq-backend",
            "Payment": "resq-payment"
        }.get(name, name.lower())

        self.status = "Unknown"
        self.response_time = 0
        self.last_checked = None
        self.total_failures = 0


class MonitoringEngine:
    """
    Monitors services and automatically recovers failed
    Docker containers while respecting dependencies.
    """

    def __init__(self):
        self.services = {}

        self.dependency_graph = DependencyGraph()

        self.recovery_manager = RecoveryManager(
            max_attempts=3,
            cooldown_seconds=30
        )

        self.total_failures = 0
        self.event_history = deque(maxlen=100)

        self.docker_client = None

    def get_docker_client(self):
        """Connect to the Docker Engine when required."""

        if self.docker_client is None:
            self.docker_client = docker.from_env()

        return self.docker_client

    def record_event(self, message, event_type="INFO"):
        """Record an event with its timestamp."""

        event = {
            "timestamp": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "type": event_type,
            "message": message
        }

        self.event_history.append(event)

        print(f"[RESQ {event_type}] {message}")

    def get_event_history(self):
        """Return recorded events as a list."""

        return list(self.event_history)

    def add_service(self, service):
        """Register a service for monitoring."""

        self.services[service.name] = service
        self.dependency_graph.add_service(service.name)

        self.record_event(
            f"{service.name} service registered."
        )

    def add_dependency(self, service_name, depends_on):
        """Register a service dependency."""

        self.dependency_graph.add_dependency(
            service_name,
            depends_on
        )

        self.record_event(
            f"{service_name} depends on {depends_on}."
        )

    def check_health(self, service):
        """Check whether a service health endpoint responds."""

        start_time = time.time()

        try:
            response = requests.get(
                service.health_url,
                timeout=3
            )

            service.response_time = round(
                (time.time() - start_time) * 1000,
                2
            )

            service.last_checked = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            if response.status_code == 200:
                service.status = "Healthy"
                return True

            service.status = "Unhealthy"
            return False

        except requests.RequestException:
            service.response_time = round(
                (time.time() - start_time) * 1000,
                2
            )

            service.last_checked = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            service.status = "Unhealthy"
            return False

    def monitor_all(self):
        """Check every registered service and recover failures."""

        for service in self.services.values():

            if self.check_health(service):
                print(
                    f"[RESQ] {service.name} is healthy."
                )
                continue

            service.total_failures += 1
            self.total_failures += 1

            self.record_event(
                f"{service.name} service is unhealthy.",
                "WARNING"
            )

            self.recover_with_dependencies(service.name)

    def recover_service(self, service_name):
        """
        Restart a failed service's Docker container
        and wait for its health endpoint to respond.
        """

        service = self.services.get(service_name)

        if service is None:
            self.record_event(
                f"Unknown service: {service_name}",
                "ERROR"
            )
            return False

        try:
            client = self.get_docker_client()

            container = client.containers.get(
                service.container_name
            )

            self.record_event(
                f"Restarting Docker container "
                f"{service.container_name}."
            )

            container.restart(timeout=10)

            # Wait for the service to become healthy.
            for attempt in range(15):

                time.sleep(2)

                if self.check_health(service):
                    self.record_event(
                        f"{service_name} recovered successfully.",
                        "SUCCESS"
                    )
                    return True

                print(
                    f"[RESQ] Waiting for {service_name} "
                    f"to become healthy "
                    f"({attempt + 1}/15)..."
                )

            self.record_event(
                f"{service_name} did not become healthy "
                f"after restart.",
                "ERROR"
            )

            return False

        except docker.errors.DockerException as error:
            self.record_event(
                f"Docker recovery failed for "
                f"{service_name}: {error}",
                "ERROR"
            )
            return False

        except Exception as error:
            self.record_event(
                f"Unexpected recovery error for "
                f"{service_name}: {error}",
                "ERROR"
            )
            return False

    def recover_with_dependencies(self, failed_service):
        """
        Recover dependencies before recovering the
        failed service itself.
        """

        try:
            recovery_order = (
                self.dependency_graph.get_recovery_order()
            )

        except ValueError as error:
            self.record_event(
                f"Cannot calculate recovery order: {error}",
                "ERROR"
            )
            return

        if failed_service not in recovery_order:
            self.record_event(
                f"{failed_service} is not registered.",
                "ERROR"
            )
            return

        # Only consider dependencies and the failed service.
        required_services = set()

        def collect_dependencies(service_name):
            if service_name in required_services:
                return

            required_services.add(service_name)

            for dependency in (
                self.dependency_graph.get_dependencies(
                    service_name
                )
            ):
                collect_dependencies(dependency)

        collect_dependencies(failed_service)

        for service_name in recovery_order:

            if service_name not in required_services:
                continue

            service = self.services.get(service_name)

            if service is None:
                continue

            # Do not restart a service that is already healthy.
            if self.check_health(service):
                continue

            if not self.recovery_manager.can_recover(
                service_name
            ):
                self.record_event(
                    f"Recovery not allowed for {service_name}.",
                    "WARNING"
                )
                continue

            self.recovery_manager.record_attempt(
                service_name
            )

            success = self.recover_service(service_name)

            if success:
                self.recovery_manager.record_success(
                    service_name
                )
            else:
                self.recovery_manager.record_failure(
                    service_name
                )

                # A dependent service should not be restarted
                # if its required dependency remains unhealthy.
                if service_name != failed_service:
                    self.record_event(
                        f"Skipping recovery of {failed_service}: "
                        f"dependency {service_name} is unavailable.",
                        "WARNING"
                    )
                    return

    def get_statistics(self):
        """Return recovery statistics."""

        return self.recovery_manager.get_statistics()

    def get_dashboard_data(self):
        """Return monitoring data for the dashboard."""

        statistics = self.get_statistics()

        successful = statistics["successful_recoveries"]
        failed = statistics["failed_recoveries"]

        total_recoveries = successful + failed

        if total_recoveries > 0:
            success_rate = round(
                successful / total_recoveries * 100,
                2
            )
        else:
            success_rate = 0

        service_data = []

        for service in self.services.values():
            service_data.append({
                "name": service.name,
                "status": service.status,
                "response_time": service.response_time,
                "last_checked": service.last_checked,
                "total_failures": service.total_failures
            })

        return {
            "services": service_data,
            "total_services": len(self.services),
            "healthy_services": sum(
                1 for service in self.services.values()
                if service.status == "Healthy"
            ),
            "unhealthy_services": sum(
                1 for service in self.services.values()
                if service.status == "Unhealthy"
            ),
            "total_failures": self.total_failures,
            "successful_recoveries": successful,
            "failed_recoveries": failed,
            "blocked_recoveries": statistics[
                "blocked_recoveries"
            ],
            "success_rate": success_rate
        }

    def get_dependency_graph(self):
        """Return the registered dependency graph."""

        return self.dependency_graph.graph
