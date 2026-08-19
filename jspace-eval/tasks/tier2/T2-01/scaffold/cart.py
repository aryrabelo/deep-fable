"""Shopping cart totals. Two planted bugs; test_cart.py encodes the intended behavior."""


def add_item(cart, name, price, qty):
    cart.append({"name": name, "price": price, "qty": qty})
    return cart


def subtotal(cart):
    return sum(item["price"] * item["qty"] for item in cart)


def discount(sub):
    """20% discount on orders of $60 or more (inclusive threshold)."""
    if sub > 60:
        return sub * 0.20
    return 0.0


def shipping(sub, disc):
    """Free shipping when the amount actually paid (sub - disc) is $50 or more."""
    if sub >= 50:
        return 0.0
    return 5.99


def total(cart):
    sub = subtotal(cart)
    disc = discount(sub)
    ship = shipping(sub, disc)
    return sub - disc + ship
