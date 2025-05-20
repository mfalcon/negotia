from typing import List, Dict, Tuple
from ..core.scoring import score_agent
from ..core.negotiation import NegotiationStatus

def evaluate_swarm(negotiations,
                   buyer_agents,
                   seller_agents) -> Tuple[Dict, Dict]:
    """
    Devuelve:
      - dict por negociación con scores
      - dict global con medias
    """
    results = {}
    for n in negotiations:
        if n.status != NegotiationStatus.AGREEMENT:
            continue
        seller = seller_agents[n.seller_id]
        buyer  = buyer_agents[n.buyer_id]

        s = score_agent("seller", n.final_terms, n.terms, seller.term_weights)
        b = score_agent("buyer",  n.final_terms, n.terms, buyer.term_weights)

        results[n.id] = {"seller_score": s,
                         "buyer_score":  b,
                         "gap":          abs(s - b)}

    if not results:
        return {}, {}

    avg_s = sum(r["seller_score"] for r in results.values()) / len(results)
    avg_b = sum(r["buyer_score"]  for r in results.values()) / len(results)
    return results, {"avg_seller": avg_s, "avg_buyer": avg_b} 