"""
Conversión de términos acordados → puntuaciones 0-1 para vendedor y comprador.
"""
from typing import Dict, Union
from .terms import ItemTerms, MultiItemTerms

def _normalize(value: float, lo: float, hi: float, maximize: bool) -> float:
    if hi == lo:
        return 0.0
    pct = (value - lo) / (hi - lo)
    return pct if maximize else 1 - pct

def score_agent(role: str,
                agreed: Dict[str, Union[float, Dict[str, float]]],
                terms: Union[ItemTerms, MultiItemTerms],
                weights: Dict[str, float]) -> float:
    """
    role : 'seller' | 'buyer'
    agreed: For single-item: {'price': .., 'delivery_days': .., 'upfront_pct': ..}
            For multi-item: {'total_price': .., 'delivery_days': .., 'upfront_pct': .., 
                           'items': {'item1': {'price': .., 'quantity': ..}, ...}}
    """
    assert role in ("seller", "buyer")
    maximize = (role == "seller")

    if isinstance(terms, MultiItemTerms):
        return _score_multi_item(role, agreed, terms, weights, maximize)
    else:
        return _score_single_item(role, agreed, terms, weights, maximize)

def _score_single_item(role: str, agreed: Dict[str, float], terms: ItemTerms, 
                      weights: Dict[str, float], maximize: bool) -> float:
    """Score a single-item negotiation"""
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

def _score_multi_item(role: str, agreed: Dict[str, Union[float, Dict[str, float]]], 
                     terms: MultiItemTerms, weights: Dict[str, float], maximize: bool) -> float:
    """Score a multi-item negotiation"""
    # Calculate total price range for normalization
    total_price_range = terms.get_total_price_range()
    
    # Score based on total price
    total_price = agreed.get("total_price", 0.0)
    price_score = weights["price"] * _normalize(
        total_price,
        total_price_range.minimum, 
        total_price_range.maximum, 
        maximize
    )
    
    # Score delivery days (use global if available, otherwise use first item's range)
    delivery_days = agreed.get("delivery_days", 0.0)
    if terms.global_delivery_days:
        delivery_range = terms.global_delivery_days
    else:
        # Use the first item's delivery range as default
        first_item = next(iter(terms.items.values()))
        delivery_range = first_item.delivery_days
    
    delivery_score = weights["delivery_days"] * _normalize(
        delivery_days,
        delivery_range.minimum,
        delivery_range.maximum,
        maximize
    )
    
    # Score upfront percentage (use global if available, otherwise use first item's range)
    upfront_pct = agreed.get("upfront_pct", 0.0)
    if terms.global_upfront_pct:
        upfront_range = terms.global_upfront_pct
    else:
        # Use the first item's upfront range as default
        first_item = next(iter(terms.items.values()))
        upfront_range = first_item.upfront_pct
    
    upfront_score = weights["upfront_pct"] * _normalize(
        upfront_pct,
        upfront_range.minimum,
        upfront_range.maximum,
        maximize
    )
    
    total_score = price_score + delivery_score + upfront_score
    return round(total_score, 3)

def calculate_multi_item_totals(agreed_items: Dict[str, Dict[str, float]], 
                               terms: MultiItemTerms) -> Dict[str, float]:
    """Calculate totals for multi-item negotiation results"""
    total_price = 0.0
    total_quantity = 0
    
    for item_id, item_agreed in agreed_items.items():
        quantity = item_agreed.get("quantity", 1)
        price_per_unit = item_agreed.get("price", 0.0)
        total_price += price_per_unit * quantity
        total_quantity += quantity
    
    # Apply bulk discounts if configured
    discount_pct = 0.0
    for min_qty, discount in sorted(terms.bulk_discount_tiers.items()):
        if total_quantity >= min_qty:
            discount_pct = discount
    
    if discount_pct > 0:
        total_price *= (1 - discount_pct / 100)
    
    return {
        "total_price": total_price,
        "total_quantity": total_quantity,
        "bulk_discount_applied": discount_pct
    } 