
import unittest

from dependency.dependency_graph import DependencyGraph


class TestDependencyGraph(unittest.TestCase):

    def setUp(self):
        self.graph = DependencyGraph()

        self.graph.add_service("Backend")
        self.graph.add_service("Payment")

        self.graph.add_dependency(
            "Payment",
            "Backend"
        )

    def test_dependency_is_registered(self):
        self.assertEqual(
            self.graph.get_dependencies("Payment"),
            ["Backend"]
        )

    def test_recovery_order(self):
        order = self.graph.get_recovery_order()

        self.assertLess(
            order.index("Backend"),
            order.index("Payment")
        )

    def test_circular_dependency_is_rejected(self):
        with self.assertRaises(ValueError):
            self.graph.add_dependency(
                "Backend",
                "Payment"
            )

    def test_unknown_service_has_no_dependencies(self):
        self.assertEqual(
            self.graph.get_dependencies("Unknown"),
            []
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
