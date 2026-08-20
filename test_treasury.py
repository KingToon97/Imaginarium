import tempfile, unittest
from imaginarium.app import Imaginarium

class TreasuryTests(unittest.TestCase):
    def setUp(self): self.tmp=tempfile.TemporaryDirectory(); self.app=Imaginarium(self.tmp.name)
    def tearDown(self): self.tmp.cleanup()
    def test_no_spend_before_revenue(self): self.assertFalse(self.app.treasury.authorize(1).approved)
    def test_reinvestment_is_profit_funded(self):
        self.app.store.book_revenue(10000,"test sale")
        self.assertEqual(self.app.treasury.reinvestment_budget(),2500)
        self.assertTrue(self.app.treasury.authorize(2500).approved)
        self.assertFalse(self.app.treasury.authorize(2501).approved)
if __name__=='__main__': unittest.main()
