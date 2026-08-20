"""Test package initialization and imports."""
import unittest

from imaginarium import Imaginarium, BaseAgent, AgentRegistry, Proposal, Verdict


class TestPackageImports(unittest.TestCase):
    """Test package-level imports."""

    def test_imaginarium_importable(self):
        """Imaginarium class should be importable from package."""
        self.assertIsNotNone(Imaginarium)

    def test_base_agent_importable(self):
        """BaseAgent should be importable from package."""
        self.assertIsNotNone(BaseAgent)

    def test_agent_registry_importable(self):
        """AgentRegistry should be importable from package."""
        self.assertIsNotNone(AgentRegistry)

    def test_proposal_importable(self):
        """Proposal model should be importable from package."""
        self.assertIsNotNone(Proposal)

    def test_verdict_importable(self):
        """Verdict model should be importable from package."""
        self.assertIsNotNone(Verdict)


if __name__ == "__main__":
    unittest.main()
