"""
SwarmManager: ejecuta en round-robin todas las negociaciones activas.
"""
import itertools, time, os, re, json
from typing import List, Dict, Union
from .negotiation import Negotiation, NegotiationStatus, Turn
from .terms import MultiItemTerms
from .scoring import calculate_multi_item_totals
from ..utils.file_io import save_log

def extract_terms_from_message(msg: str, negotiation: Negotiation = None):
    """Extract terms from message, handling both single-item and multi-item negotiations"""
    
    # First try the standard single-item format
    # Example: "Done deal! price=1200, delivery=7, upfront=50"
    m = re.search(r"price\s*=\s*([\d.]+)[, ]+delivery\s*=\s*([\d.]+)[, ]+upfront\s*=\s*([\d.]+)", msg, re.I)
    if m:
        return {
            "price": float(m.group(1)),
            "delivery_days": float(m.group(2)),
            "upfront_pct": float(m.group(3)),
        }
    
    # If negotiation is multi-item, try to extract multi-item format
    if negotiation and negotiation.is_multi_item():
        return extract_multi_item_terms(msg, negotiation)
    
    return None

def extract_multi_item_terms(msg: str, negotiation: Negotiation):
    """Extract terms from multi-item negotiation message"""
    # Try to find JSON-like structure in message
    # Example: "Done deal! {item1: {price: 100, qty: 5}, item2: {price: 200, qty: 3}, delivery: 7, upfront: 50}"
    
    # Look for various patterns
    patterns = [
        # JSON-like format
        r'\{[^}]+\}',
        # Simple multi-item format: "item1=5x100, item2=3x200, delivery=7, upfront=50"
        r'(\w+)=(\d+)x([\d.]+)',
        # Total format: "total=1500, delivery=7, upfront=50"
        r'total\s*=\s*([\d.]+)[, ]+delivery\s*=\s*([\d.]+)[, ]+upfront\s*=\s*([\d.]+)',
    ]
    
    # Try total format first (most common for multi-item)
    total_match = re.search(r'total\s*=\s*([\d.]+)[, ]+delivery\s*=\s*([\d.]+)[, ]+upfront\s*=\s*([\d.]+)', msg, re.I)
    if total_match:
        return {
            "total_price": float(total_match.group(1)),
            "delivery_days": float(total_match.group(2)),
            "upfront_pct": float(total_match.group(3)),
        }
    
    # Try to extract individual items
    item_matches = re.findall(r'(\w+)[:=]\s*(\d+)x([\d.]+)', msg, re.I)
    if item_matches:
        items = {}
        total_price = 0.0
        
        for item_id, qty_str, price_str in item_matches:
            quantity = int(qty_str)
            price = float(price_str)
            items[item_id] = {"quantity": quantity, "price": price}
            total_price += quantity * price
        
        # Extract global terms
        delivery_match = re.search(r'delivery\s*[:=]\s*([\d.]+)', msg, re.I)
        upfront_match = re.search(r'upfront\s*[:=]\s*([\d.]+)', msg, re.I)
        
        result = {
            "items": items,
            "total_price": total_price,
        }
        
        if delivery_match:
            result["delivery_days"] = float(delivery_match.group(1))
        if upfront_match:
            result["upfront_pct"] = float(upfront_match.group(1))
        
        return result
    
    return None

class SwarmManager:
    def __init__(self,
                 sellers: Dict[str, 'SellerAgent'],
                 buyers: Dict[str, 'BuyerAgent'],
                 negotiations: List[Negotiation]):
        self.sellers = sellers
        self.buyers = buyers
        self.negotiations = negotiations

    def run(self) -> None:
        """Round-robin: en cada ciclo, cada negociación activa recibe un turno (buyer, luego seller)."""
        sold_sellers = set()
        bought_buyers = set()
        while any(n.status == NegotiationStatus.ONGOING for n in self.negotiations):
            for n in self.negotiations:
                if n.status != NegotiationStatus.ONGOING:
                    continue

                # Si el vendedor ya vendió, cerrar la negociación
                if n.seller_id in sold_sellers:
                    n.status = NegotiationStatus.FAILED
                    save_log(n)
                    continue

                # Si el comprador ya compró, cerrar la negociación
                if n.buyer_id in bought_buyers:
                    n.status = NegotiationStatus.FAILED
                    save_log(n)
                    continue

                buyer = self.buyers[n.buyer_id]
                seller = self.sellers[n.seller_id]

                # --- Turno del comprador ---
                b_msg = buyer.decide(n)
                n.add_turn(Turn(buyer.id, b_msg, time.time()))
                terms = extract_terms_from_message(b_msg, n)
                if terms:
                    # Process multi-item terms if necessary
                    if n.is_multi_item() and isinstance(n.terms, MultiItemTerms):
                        terms = self._process_multi_item_agreement(terms, n.terms)
                    
                    n.register_agreement(terms)
                    save_log(n)
                    sold_sellers.add(n.seller_id)
                    bought_buyers.add(n.buyer_id)
                    # Cerrar otras negociaciones activas de este vendedor y comprador
                    for other in self.negotiations:
                        if other is not n and other.status == NegotiationStatus.ONGOING:
                            if other.seller_id == n.seller_id or other.buyer_id == n.buyer_id:
                                other.status = NegotiationStatus.FAILED
                                save_log(other)
                    # Si el comprador acepta, el vendedor NO responde en esta ronda
                    continue

                # --- Turno del vendedor ---
                s_msg = seller.decide(n)
                n.add_turn(Turn(seller.id, s_msg, time.time()))
                terms = extract_terms_from_message(s_msg, n)
                if terms:
                    # Process multi-item terms if necessary
                    if n.is_multi_item() and isinstance(n.terms, MultiItemTerms):
                        terms = self._process_multi_item_agreement(terms, n.terms)
                    
                    n.register_agreement(terms)
                    save_log(n)
                    sold_sellers.add(n.seller_id)
                    bought_buyers.add(n.buyer_id)
                    # Cerrar otras negociaciones activas de este vendedor y comprador
                    for other in self.negotiations:
                        if other is not n and other.status == NegotiationStatus.ONGOING:
                            if other.seller_id == n.seller_id or other.buyer_id == n.buyer_id:
                                other.status = NegotiationStatus.FAILED
                                save_log(other)
                    continue

                save_log(n)

                # (opcional)  break si todas cerradas para evitar ciclo innecesario
    
    def _process_multi_item_agreement(self, terms: Dict, multi_terms: MultiItemTerms) -> Dict:
        """Process multi-item agreement terms and calculate totals"""
        if "items" in terms:
            # Calculate totals from individual items
            totals = calculate_multi_item_totals(terms["items"], multi_terms)
            terms.update(totals)
        
        return terms 