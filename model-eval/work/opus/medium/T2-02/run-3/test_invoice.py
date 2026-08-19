import unittest

from invoice import grand_total


class InvoiceTest(unittest.TestCase):
    def test_tax_applies_after_discount(self):
        # 80 - 10% = 72; 72 * 1.0825 = 77.94; shipping 72 -> 4.99
        self.assertAlmostEqual(grand_total(80.00, 10), 82.93, places=2)

    def test_promo_is_capped_at_30pct(self):
        # cap: 50% -> 30%; 120 - 36 = 84; 84 * 1.0825 = 90.93; shipping 84 -> free
        self.assertAlmostEqual(grand_total(120.00, 50), 90.93, places=2)

    def test_free_shipping_at_exactly_75(self):
        # 75 * 1.0825 = 81.19; shipping 75 -> free
        self.assertAlmostEqual(grand_total(75.00, 0), 81.19, places=2)

    def test_mid_tier_shipping(self):
        # 40 * 1.0825 = 43.30; shipping 40 -> 4.99
        self.assertAlmostEqual(grand_total(40.00, 0), 48.29, places=2)

    def test_small_order_top_tier_shipping(self):
        # 20 * 1.0825 = 21.65; shipping 20 -> 7.99
        self.assertAlmostEqual(grand_total(20.00, 0), 29.64, places=2)


if __name__ == "__main__":
    unittest.main()
