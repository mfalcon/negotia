from dataclasses import dataclass, field
from typing import Tuple, Dict, List, Optional

@dataclass
class Range:
    minimum: float
    maximum: float
    reference: float = 0.0        # valor objetivo opcional

@dataclass
class ItemTerms:
    price: Range
    delivery_days: Range
    upfront_pct: Range
    
    # Optional item metadata
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None

@dataclass
class ItemRequest:
    """Represents a request for a specific item with quantity"""
    item_id: str
    quantity: int
    max_quantity: Optional[int] = None  # Maximum quantity buyer is willing to accept
    min_quantity: Optional[int] = None  # Minimum quantity buyer needs

@dataclass
class MultiItemTerms:
    """Terms for negotiations involving multiple items"""
    items: Dict[str, ItemTerms]  # item_id -> ItemTerms
    requests: List[ItemRequest]  # List of items being negotiated
    
    # Global terms that apply to the entire deal
    global_delivery_days: Optional[Range] = None  # Overall delivery window
    global_upfront_pct: Optional[Range] = None    # Overall payment terms
    
    # Bulk pricing discounts
    bulk_discount_tiers: Dict[int, float] = field(default_factory=dict)  # quantity -> discount %
    
    def get_total_price_range(self) -> Range:
        """Calculate total price range for all requested items"""
        min_total = 0.0
        max_total = 0.0
        ref_total = 0.0
        
        for req in self.requests:
            item_terms = self.items[req.item_id]
            min_qty = req.min_quantity or req.quantity
            max_qty = req.max_quantity or req.quantity
            
            min_total += item_terms.price.minimum * min_qty
            max_total += item_terms.price.maximum * max_qty
            ref_total += item_terms.price.reference * req.quantity
        
        return Range(minimum=min_total, maximum=max_total, reference=ref_total)
    
    def get_item_terms(self, item_id: str) -> ItemTerms:
        """Get terms for a specific item"""
        return self.items[item_id]
    
    def get_request(self, item_id: str) -> Optional[ItemRequest]:
        """Get request details for a specific item"""
        for req in self.requests:
            if req.item_id == item_id:
                return req
        return None 