"""
SwarmManager: ejecuta en round-robin todas las negociaciones activas.
"""
import itertools, time, os, re
from typing import List, Dict
from .negotiation import Negotiation, NegotiationStatus, Turn
from ..utils.file_io import save_log

def extract_terms_from_message(msg: str):
    # Example: "Done deal! price=1200, delivery=7, upfront=600"
    m = re.search(r"price\s*=\s*([\d.]+)[, ]+delivery\s*=\s*([\d.]+)[, ]+upfront\s*=\s*([\d.]+)", msg, re.I)
    if m:
        return {
            "price": float(m.group(1)),
            "delivery_days": float(m.group(2)),
            "upfront_pct": float(m.group(3)),
        }
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
        """Itera hasta que todas las negociaciones terminen."""
        sold_sellers = set()
        while any(n.status == NegotiationStatus.ONGOING
                  for n in self.negotiations):
            for n in self.negotiations:
                if n.status != NegotiationStatus.ONGOING:
                    continue

                # Si el vendedor ya vendió, cerrar la negociación
                if n.seller_id in sold_sellers:
                    n.status = NegotiationStatus.FAILED
                    save_log(n)
                    continue

                seller = self.sellers[n.seller_id]
                buyer  = self.buyers[n.buyer_id]

                # ---- turno vendedor -----------------------------------------
                s_msg = seller.decide(n)
                n.add_turn(Turn(seller.id, s_msg, time.time()))
                terms = extract_terms_from_message(s_msg)
                if terms:
                    n.register_agreement(terms)
                    save_log(n)
                    sold_sellers.add(n.seller_id)
                    # Cerrar todas las otras negociaciones activas de este vendedor
                    for other in self.negotiations:
                        if (other is not n and
                            other.seller_id == n.seller_id and
                            other.status == NegotiationStatus.ONGOING):
                            other.status = NegotiationStatus.FAILED
                            save_log(other)
                    continue

                # ---- turno comprador ----------------------------------------
                b_msg = buyer.decide(n)
                n.add_turn(Turn(buyer.id, b_msg, time.time()))
                terms = extract_terms_from_message(b_msg)
                if terms:
                    n.register_agreement(terms)
                    save_log(n)
                    sold_sellers.add(n.seller_id)
                    # Cerrar todas las otras negociaciones activas de este vendedor
                    for other in self.negotiations:
                        if (other is not n and
                            other.seller_id == n.seller_id and
                            other.status == NegotiationStatus.ONGOING):
                            other.status = NegotiationStatus.FAILED
                            save_log(other)
                    continue

                # ---- persistencia incremental -------------------------------
                save_log(n)

                # (opcional)  break si todas cerradas para evitar ciclo innecesario 