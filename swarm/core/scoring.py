"""
Conversión de términos acordados → puntuaciones 0-1 para vendedor y comprador.
"""
from typing import Dict
from .terms import ItemTerms

def _normalize(value: float, lo: float, hi: float, maximize: bool) -> float:
    if hi == lo:
        return 0.0
    pct = (value - lo) / (hi - lo)
    return pct if maximize else 1 - pct

def score_agent(role: str,
                agreed: Dict[str, float],
                terms: ItemTerms,
                weights: Dict[str, float]) -> float:
    """
    role : 'seller' | 'buyer'
    agreed: {'price': .., 'delivery_days': .., 'upfront_pct': ..}
    """
    assert role in ("seller", "buyer")
    maximize = (role == "seller")

    score  = weights["price"] * _normalize(
                agreed["price"],
                terms.price.minimum, terms.price.maximum, maximize)
    score += weights["delivery_days"] * _normalize(
                agreed["delivery_days"],
                terms.delivery_days.minimum, terms.delivery_days.maximum, maximize)
    score += weights["upfront_pct"] * _normalize(
                agreed["upfront_pct"],
                terms.upfront_pct.minimum, terms.upfront_pct.maximum, maximize)
    return round(score, 3) 