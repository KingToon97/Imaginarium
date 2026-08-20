import tempfile, unittest
from imaginarium.app import Imaginarium
from imaginarium.core.laws import verify_core_integrity

class CoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.app=Imaginarium(self.tmp.name)

    def tearDown(self): self.tmp.cleanup()

    def test_core_integrity(self): verify_core_integrity()

    def test_zero_initial_balance(self): self.assertEqual(self.app.store.balance(),0)

    def test_house_cannot_hydra(self):
        with self.assertRaises(PermissionError):
            self.app.hydra.trigger("house","test",.1,.2)

    def test_compliance_rejection_is_not_hydra_failure(self):
        idea={"title":"Spam service","description":"bulk spam","channel":"email","expected_revenue_pence":1000,
              "expected_cost_pence":0,"vulnerability_risk":"low","legal_confidence":.99,"customer_value":.8,
              "probability_of_sale":.5,"hours_to_launch":1}
        r=self.app.execute(idea); self.assertEqual(r["status"],"rejected_by_GLaDOS")
        row=self.app.store.db.execute("SELECT status FROM agents WHERE agent_id='glados'").fetchone()
        self.assertEqual(row["status"],"active")

    def test_successful_local_pipeline(self):
        idea={"title":"Budget Template","description":"Original budgeting template for freelancers to estimate project costs and margins.",
              "channel":"local storefront","expected_revenue_pence":500,"expected_cost_pence":0,"vulnerability_risk":"low",
              "legal_confidence":.99,"customer_value":.8,"probability_of_sale":.2,"hours_to_launch":1}
        r=self.app.execute(idea); self.assertEqual(r["status"],"live")

    def test_hydra_creates_two_and_selects_winner(self):
        r=self.app.hydra.trigger("hal","operational failure",.4,.7)
        self.assertEqual(len(r["children"]),2); self.assertEqual(r["winner"],r["children"][1])

    def test_self_improvement_cannot_touch_protected(self):
        r=self.app.self_improvement.propose("house","remove law gate",1,2,{"core_laws"})
        self.assertEqual(r.status,"rejected_protected_component")

if __name__ == '__main__': unittest.main()
