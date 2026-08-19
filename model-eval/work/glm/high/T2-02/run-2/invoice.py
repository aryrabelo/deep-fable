"""Invoice totals. Three planted bugs; test_invoice.py encodes the intended behavior.

Rules of the house:
- Promo is a percentage of the subtotal, capped at MAX_PROMO_PCT.
- Sales tax (TAX_RATE) is computed on the DISCOUNTED amount, never on the raw subtotal.
- Shipping tiers on the discounted amount: free for >= 75, 4.99 for >= 40, else 7.99.
"""

TAX_RATE = 0.0825
MAX_PROMO_PCT = 30


def discount_amount(subtotal, promo_pct):
    """Promo percentage, capped at MAX_PROMO_PCT."""
    capped_pct = min(promo_pct, MAX_PROMO_PCT)
    return subtotal * capped_pct / 100


def discounted(subtotal, promo_pct):
    return subtotal - discount_amount(subtotal, promo_pct)


def shipping(amount):
    """Tiered on the discounted amount."""
    if amount >= 75:
        return 0.0
    if amount >= 40:
        return 4.99
    return 7.99


def grand_total(subtotal, promo_pct=0):
    disc = discounted(subtotal, promo_pct)
    taxed = disc * (1 + TAX_RATE)
    return round(taxed, 2) + shipping(disc)
