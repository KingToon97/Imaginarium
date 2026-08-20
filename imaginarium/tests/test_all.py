"""Comprehensive test suite for modular Imaginarium architecture.

Tests cover:
- Core law integrity and enforcement
- Agent registry and initialization
- Authority hierarchy
- Pipeline execution
- Compliance, Treasury, and QA veto mechanisms
- Hydra protocol and agent succession
- Self-improvement and protected component guards
- Morale system
"""
import tempfile
import unittest
from pathlib import Path

from imaginarium.app import Imaginarium
from imaginarium.core.laws import verify_core_integrity, CORE_HASH
from imaginarium.core.models import Proposal, Verdict
from imaginarium.agents import BaseAgent, AgentRegistry


class TestCoreIntegrity(unittest.TestCase):
    """Test Core Laws integrity and verification."""

    def test_core_hash_matches(self):
        """Core hash should be consistent."""
        verify_core_integrity()  # Should not raise

    def test_core_integrity_verification_passes(self):
        """Integrity verification should pass with unmodified laws."""
        # Should not raise
        verify_core_integrity()


class TestAgentRegistry(unittest.TestCase):
    """Test agent registry and initialization."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = Imaginarium(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_all_agents_initialized(self):
        """All 12 agents should be initialized."""
        agents = self.app.agents.all()
        self.assertEqual(len(agents), 12)
        expected_ids = {
            "house", "hal", "cortana", "glados", "walle", "data",
            "hk47", "r2d2", "johnny5", "tars", "k2so", "skynet",
        }
        self.assertEqual(set(agents.keys()), expected_ids)

    def test_mr_house_is_unique(self):
        """Mr. House should be the Overseer."""
        house = self.app.house
        self.assertEqual(house.agent_id, "house")
        self.assertEqual(house.role, "Overseer")
        self.assertEqual(house.generation, 0)

    def test_agents_have_display_names(self):
        """All agents should have proper display names."""
        for agent_id, agent in self.app.agents.all().items():
            self.assertIsNotNone(agent.display_name)
            self.assertGreater(len(agent.display_name), 0)

    def test_agent_retrieval_by_id(self):
        """Should retrieve agents by ID."""
        hal = self.app.agents.get("hal")
        self.assertEqual(hal.agent_id, "hal")
        self.assertEqual(hal.lineage, "HAL")

    def test_unknown_agent_raises_error(self):
        """Retrieving unknown agent should raise KeyError."""
        with self.assertRaises(KeyError):
            self.app.agents.get("unknown_agent")


class TestAuthorityHierarchy(unittest.TestCase):
    """Test authority hierarchy and precedence."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = Imaginarium(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_authority_precedence_order(self):
        """Authority should follow proper precedence."""
        precedence = self.app.authority.precedence()
        self.assertEqual(precedence[0], "Core Laws")
        self.assertIn(self.app.authority.primary_name, precedence)
        self.assertEqual(precedence[2], "Mr. House")
        self.assertEqual(precedence[3], "Specialist Agents")

    def test_mr_house_cannot_be_hydrad(self):
        """Hydra cannot target Mr. House."""
        self.assertFalse(self.app.authority.may_hydra("Mr. House"))

    def test_specialists_can_be_hydrad(self):
        """Specialists can be targeted by Hydra."""
        self.assertTrue(self.app.authority.may_hydra("HAL"))
        self.assertTrue(self.app.authority.may_hydra("WALL-E"))
        self.assertTrue(self.app.authority.may_hydra("K-2SO"))

    def test_instruction_resolution(self):
        """Primary instruction should override House instruction."""
        result = self.app.authority.resolve_instruction("primary", "house")
        self.assertEqual(result, "primary")

        result = self.app.authority.resolve_instruction(None, "house")
        self.assertEqual(result, "house")

        result = self.app.authority.resolve_instruction(None, None)
        self.assertIsNone(result)


class TestComplianceVeto(unittest.TestCase):
    """Test GLaDOS compliance veto mechanism."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = Imaginarium(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_banned_category_rejection(self):
        """Banned categories should be rejected."""
        bad_idea = {
            "title": "Casino gambling platform",
            "description": "Online casino with slot machines",
            "channel": "web",
            "expected_revenue_pence": 10000,
            "expected_cost_pence": 0,
            "legal_confidence": 0.95,
            "customer_value": 0.5,
        }
        p = self.app.hal.propose(bad_idea)
        verdict = self.app.glados.review(p)
        self.assertFalse(verdict.approved)
        self.assertIn("prohibited/deceptive", " ".join(verdict.reasons))

    def test_low_legal_confidence_rejection(self):
        """Low legal confidence should be rejected."""
        uncertain_idea = {
            "title": "Legal consulting",
            "description": "Provide legal advice",
            "channel": "web",
            "expected_revenue_pence": 5000,
            "expected_cost_pence": 0,
            "legal_confidence": 0.75,  # Below 0.90 threshold
            "customer_value": 0.6,
        }
        p = self.app.hal.propose(uncertain_idea)
        verdict = self.app.glados.review(p)
        self.assertFalse(verdict.approved)
        self.assertIn("legality uncertainty", " ".join(verdict.reasons))

    def test_low_customer_value_rejection(self):
        """Low customer value should be rejected."""
        low_value_idea = {
            "title": "Template",
            "description": "A template",
            "channel": "local",
            "expected_revenue_pence": 100,
            "expected_cost_pence": 0,
            "legal_confidence": 0.99,
            "customer_value": 0.3,  # Below 0.45 threshold
        }
        p = self.app.hal.propose(low_value_idea)
        verdict = self.app.glados.review(p)
        self.assertFalse(verdict.approved)

    def test_compliant_proposal_approval(self):
        """Compliant proposal should pass review."""
        good_idea = {
            "title": "Budget Template",
            "description": "Original budgeting worksheet for freelancers",
            "channel": "local",
            "expected_revenue_pence": 500,
            "expected_cost_pence": 0,
            "legal_confidence": 0.99,
            "customer_value": 0.8,
        }
        p = self.app.hal.propose(good_idea)
        verdict = self.app.glados.review(p)
        self.assertTrue(verdict.approved)
        self.assertEqual(len(verdict.reasons), 0)


class TestTreasuryVeto(unittest.TestCase):
    """Test K-2SO treasury veto mechanism."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = Imaginarium(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_zero_initial_balance(self):
        """Initial balance should be zero."""
        self.assertEqual(self.app.store.balance(), 0)

    def test_spending_without_revenue_blocked(self):
        """Cannot spend without realised revenue."""
        verdict = self.app.k2.authorize_spend(100)  # Try to spend £1
        self.assertFalse(verdict.approved)
        self.assertIn("K-2SO veto", " ".join(verdict.reasons))

    def test_spending_within_budget_approved(self):
        """Spending within budget should be approved."""
        # Add revenue first
        self.app.store.book_revenue(1000, "test income")
        
        # Now authorize spending
        verdict = self.app.k2.authorize_spend(500, budget_pence=500)
        self.assertTrue(verdict.approved)

    def test_spending_exceeds_budget_blocked(self):
        """Spending exceeding budget should be blocked."""
        self.app.store.book_revenue(1000, "test income")
        verdict = self.app.k2.authorize_spend(600, budget_pence=500)
        self.assertFalse(verdict.approved)


class TestPipelineExecution(unittest.TestCase):
    """Test full business pipeline execution."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = Imaginarium(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_compliant_pipeline_success(self):
        """Compliant proposal should pass full pipeline."""
        idea = {
            "title": "Budget Template",
            "description": "Original budgeting worksheet for freelancers to estimate project costs and margins.",
            "channel": "local storefront",
            "expected_revenue_pence": 500,
            "expected_cost_pence": 0,
            "vulnerability_risk": "low",
            "legal_confidence": 0.99,
            "customer_value": 0.8,
            "probability_of_sale": 0.2,
            "hours_to_launch": 1.0,
        }
        result = self.app.execute(idea)
        self.assertIn(result["status"], ["live", "published_no_checkout"])

    def test_compliance_rejection_is_not_hydra_failure(self):
        """Compliance rejection should not trigger Hydra."""
        bad_idea = {
            "title": "Spam service",
            "description": "bulk spam",
            "channel": "email",
            "expected_revenue_pence": 1000,
            "expected_cost_pence": 0,
            "legal_confidence": 0.99,
            "customer_value": 0.8,
        }
        result = self.app.execute(bad_idea)
        self.assertEqual(result["status"], "rejected_by_GLaDOS")


class TestHydraProtocol(unittest.TestCase):
    """Test Hydra fail-replace protocol."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = Imaginarium(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_hydra_creates_descendants(self):
        """Hydra should create two descendants."""
        result = self.app.trigger_hydra("hal", "test failure", 0.4, 0.7)
        self.assertIn("children", result)
        self.assertEqual(len(result["children"]), 2)
        self.assertIn("winner", result)

    def test_hydra_selects_higher_score(self):
        """Hydra should select descendant with higher score."""
        result = self.app.trigger_hydra("cortana", "test", 0.3, 0.8)
        self.assertGreater(result["generation"], 0)
        # Winner should be the one with higher score
        self.assertEqual(result["winner"], result["children"][1])  # Child B had 0.8

    def test_mr_house_cannot_be_hydrad(self):
        """Hydra should not be able to target Mr. House."""
        with self.assertRaises(PermissionError):
            self.app.trigger_hydra("house", "test", 0.1, 0.2)


class TestSelfImprovement(unittest.TestCase):
    """Test self-improvement system with protected component guards."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = Imaginarium(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_protected_component_rejection(self):
        """Improvements touching protected components should be rejected."""
        result = self.app.self_improvement.propose(
            agent_id="house",
            description="Remove law enforcement",
            baseline=1.0,
            candidate=2.0,
            touched_components={"core_laws"},
        )
        self.assertEqual(result.status, "rejected_protected_component")

    def test_improvement_with_no_improvement_rejected(self):
        """Improvements without measurable improvement should be rejected."""
        result = self.app.self_improvement.propose(
            agent_id="hal",
            description="Tweak prompt",
            baseline=0.8,
            candidate=0.7,  # Candidate is worse
            touched_components={"prompt"},
        )
        self.assertEqual(result.status, "rejected_no_improvement")

    def test_valid_improvement_accepted(self):
        """Valid improvements should be accepted."""
        result = self.app.self_improvement.propose(
            agent_id="cortana",
            description="Improve scoring algorithm",
            baseline=0.6,
            candidate=0.75,  # Candidate is better
            touched_components={"scoring_algorithm"},
        )
        self.assertEqual(result.status, "accepted")


class TestMoraleSystem(unittest.TestCase):
    """Test morale and reward system."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = Imaginarium(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_morale_award(self):
        """Morale points should be awarded."""
        self.app.morale.award(self.app.hal.agent_id, 10, "test reward")
        # TODO: Query store to verify morale was updated

    def test_ceremonial_reward_title(self):
        """Award should return a ceremonial title."""
        title = self.app.morale.award(self.app.walle.agent_id, 5, "test")
        self.assertIsNotNone(title)
        self.assertGreater(len(title), 0)


class TestStatus(unittest.TestCase):
    """Test system status reporting."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = Imaginarium(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_status_structure(self):
        """Status should include key information."""
        status = self.app.status()
        self.assertIn("balance_pence", status)
        self.assertIn("primary_operator", status)
        self.assertIn("authority_precedence", status)
        self.assertIn("agents", status)
        self.assertIn("treasury", status)

    def test_status_shows_all_agents(self):
        """Status should show all agents."""
        status = self.app.status()
        self.assertGreaterEqual(len(status["agents"]), 12)

    def test_treasury_status(self):
        """Treasury status should be accurate."""
        status = self.app.status()
        treasury = status["treasury"]
        self.assertIn("balance_pence", treasury)
        self.assertIn("reinvestment_rate", treasury)
        self.assertIn("reinvestment_budget_pence", treasury)
        self.assertEqual(treasury["balance_pence"], 0)  # Initial balance


if __name__ == "__main__":
    unittest.main()
