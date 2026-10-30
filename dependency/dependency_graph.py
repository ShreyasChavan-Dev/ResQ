
class DependencyGraph:
    """
    Stores service dependencies and calculates
    the correct order for service recovery.
    """

    def __init__(self):
        self.graph = {}

    def add_service(self, service_name):
        """Register a service in the dependency graph."""

        if service_name not in self.graph:
            self.graph[service_name] = set()

    def add_dependency(self, service_name, depends_on):
        """
        Register a dependency.

        Example:
        Payment depends on Backend.
        """

        if service_name == depends_on:
            raise ValueError(
                "A service cannot depend on itself."
            )

        self.add_service(service_name)
        self.add_service(depends_on)

        self.graph[service_name].add(depends_on)

        # Check for circular dependencies.
        try:
            self.get_recovery_order()

        except ValueError:
            self.graph[service_name].remove(depends_on)
            raise

    def get_dependencies(self, service_name):
        """Return the direct dependencies of a service."""

        if service_name not in self.graph:
            return []

        return sorted(self.graph[service_name])

    def get_recovery_order(self):
        """
        Calculate recovery order using topological sorting.

        Dependencies are placed before the services
        that depend on them.
        """

        visited = set()
        visiting = set()
        recovery_order = []

        def visit(service_name):

            if service_name in visiting:
                raise ValueError(
                    "Circular dependency detected!"
                )

            if service_name in visited:
                return

            visiting.add(service_name)

            for dependency in sorted(
                self.graph.get(service_name, set())
            ):
                visit(dependency)

            visiting.remove(service_name)
            visited.add(service_name)

            recovery_order.append(service_name)

        for service_name in sorted(self.graph):
            visit(service_name)

        return recovery_order

    def show_graph(self):
        """Display all registered service dependencies."""

        print("\n===== RESQ DEPENDENCY GRAPH =====")

        for service_name in sorted(self.graph):

            dependencies = sorted(
                self.graph[service_name]
            )

            if dependencies:
                print(
                    service_name,
                    "depends on:",
                    ", ".join(dependencies)
                )

            else:
                print(
                    service_name,
                    "has no dependencies"
                )

        print("\n===== RECOVERY ORDER =====")

        for position, service in enumerate(
            self.get_recovery_order(),
            start=1
        ):
            print(position, "-", service)
