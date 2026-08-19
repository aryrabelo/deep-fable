import unittest

from cart import add_item, total


class CartTest(unittest.TestCase):
    def test_discount_threshold_is_inclusive(self):
        cart = add_item([], "dock", 60.00, 1)
        # $60 exactly qualifies: 20% off -> pays 48 -> below free-shipping -> +5.99
        self.assertAlmostEqual(total(cart), 53.99, places=2)

    def test_shipping_uses_discounted_amount(self):
        cart = add_item([], "stand", 61.00, 1)
        # 20% off 61 -> pays 48.80 -> below 50 -> +5.99
        self.assertAlmostEqual(total(cart), 54.79, places=2)

    def test_large_order_free_shipping(self):
        cart = add_item([], "keyboard", 100.00, 1)
        # 20% off -> pays 80 -> free shipping
        self.assertAlmostEqual(total(cart), 80.00, places=2)

    def test_small_order_pays_shipping(self):
        cart = add_item([], "sticker", 3.50, 2)
        self.assertAlmostEqual(total(cart), 7.00 + 5.99, places=2)


if __name__ == "__main__":
    unittest.main()
