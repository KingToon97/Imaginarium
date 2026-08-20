"""Test individual agent implementations."""
import tempfile
import unittest
from pathlib import Path

from imaginarium.app import Imaginarium
from imaginarium.core.models import Proposal


class TestHALAgent(unittest.TestCase):
    """Test HAL opportunity discovery agent."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = Imaginarium(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_hal_proposes_idea(self):
        """HAL should be able to propose an idea."""
        idea = {
            "title": "Test Product",
            "description": "A test product",
            "channel": "local",
            "expected_revenue_pence": 100,
            "expected_cost_pence": 0,
        }
        proposal = self.app.hal.propose(idea)
        self.assertEqual(proposal.title, "Test Product")
        self.assertIsNotNone(proposal.id)


class TestCortanaAgent(unittest.TestCase):
    """Test Cortana market analyst agent."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = Imaginarium(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_cortana_scores_proposal(self):
        """Cortana should score market potential."""
        proposal = Proposal(
            id="test",
            title="Product",
            description="Description",
            channel="local",
            expected_revenue_pence=1000,
            expected_cost_pence=0,
            customer_value=0.8,
            probability_of_sale=0.5,
            hours_to_launch=2.0,
        )
        score = self.app.cortana.score(proposal)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)


class TestGLaDOSAgent(unittest.TestCase):
    """Test GLaDOS compliance agent."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = Imaginarium(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_glados_approves_compliant(self):
        """GLaDOS should approve compliant proposals."""
        proposal = Proposal(
            id="test",
            title="Budget Template",
            description="A budgeting tool",
            channel="local",
            expected_revenue_pence=500,
            expected_cost_pence=0,
            legal_confidence=0.99,
            customer_value=0.8,
        )
        verdict = self.app.glados.review(proposal)
        self.assertTrue(verdict.approved)

    def test_glados_rejects_banned_category(self):
        """GLaDOS should reject banned categories."""
        proposal = Proposal(
            id="test",
            title="Casino Platform",
            description="An online gambling site",
            channel="web",
            expected_revenue_pence=10000,
            expected_cost_pence=0,
            legal_confidence=0.95,
            customer_value=0.7,
        )
        verdict = self.app.glados.review(proposal)
        self.assertFalse(verdict.approved)


class TestWALL_EAgent(unittest.TestCase):
    """Test WALL-E builder agent."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = Imaginarium(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_walle_builds_artifact(self):
        """WALL-E should build a product artifact."""
        proposal = Proposal(
            id="test",
            title="Budget Template",
            description="A budgeting tool for freelancers",
            channel="local",
            expected_revenue_pence=500,
            expected_cost_pence=0,
        )
        artifact = self.app.walle.build(proposal)
        self.assertTrue(artifact.exists())
        content = artifact.read_text()
        self.assertGreater(len(content), 0)


class TestMrDataAgent(unittest.TestCase):
    """Test Mr. Data QA agent."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = Imaginarium(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_data_qa_checks_size(self):
        """Mr. Data should reject artifacts that are too small."""
        proposal = Proposal(
            id="test",
            title="Product",
            description="Desc",
            channel="local",
            expected_revenue_pence=100,
            expected_cost_pence=0,
        )
        
        # Create a small artifact
        self.tmp_path = Path(self.tmp.name)
        artifact = self.tmp_path / "small.md"
        artifact.write_text("Too small")  # Only 9 bytes
        
        verdict = self.app.data.qa(proposal, artifact)
        self.assertFalse(verdict.approved)


class TestHK47Agent(unittest.TestCase):
    """Test HK-47 pricing agent."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = Imaginarium(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_hk47_prices_proposal(self):
        """HK-47 should set a fair price."""
        proposal = Proposal(
            id="test",
            title="Product",
            description="Description",
            channel="local",
            expected_revenue_pence=1000,
            expected_cost_pence=0,
            customer_value=0.8,
        )
        price = self.app.hk.price(proposal)
        self.assertGreater(price, 0)
        self.assertLessEqual(price, 10000)  # Max price


class TestK2SOAgent(unittest.TestCase):
    """Test K-2SO treasury agent."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = Imaginarium(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_k2so_blocks_overspending(self):
        """K-2SO should block spending without funds."""
        verdict = self.app.k2.authorize_spend(100)
        self.assertFalse(verdict.approved)

    def test_k2so_allows_spending_within_budget(self):
        """K-2SO should allow spending within budget."""
        self.app.store.book_revenue(500, "test")
        verdict = self.app.k2.authorize_spend(300, 400)
        self.assertTrue(verdict.approved)


if __name__ == "__main__":
    unittest.main()
