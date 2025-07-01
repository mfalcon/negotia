from swarm.core.scoring import score_agent
from swarm.core.terms import Range, ItemTerms

terms = ItemTerms(
    price=Range(800, 1500),
    delivery_days=Range(5, 14),
    upfront_pct=Range(0, 100)
)
weights = {"price": 0.6, "delivery_days": 0.2, "upfront_pct": 0.2}

def test_seller_max_score():
    agreed = {"price": 1500, "delivery_days": 14, "upfront_pct": 100}
    assert score_agent("seller", agreed, terms, weights) == 1.0

def test_buyer_min_score():
    agreed = {"price": 1500, "delivery_days": 14, "upfront_pct": 100}
    assert score_agent("buyer", agreed, terms, weights) == 0.0 