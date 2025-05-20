from abc import ABC, abstractmethod
from typing import Dict, Any, List
from ..utils.template_manager import TemplateManager
from ..core.negotiation import Negotiation

class Agent(ABC):
    """
    Clase base para BuyerAgent y SellerAgent.
    """
    def __init__(self,
                 agent_id: str,
                 prompt_path: str,
                 repo,
                 urgency: float,
                 term_weights: Dict[str, float]):
        self.id           = agent_id
        self.repo         = repo
        self.urgency      = urgency
        self.term_weights = term_weights
        self.prompt_path  = prompt_path
        self.tmpl         = TemplateManager()
        self.negotiations: Dict[str, Negotiation] = {}

    @abstractmethod
    def decide(self, negotiation: Negotiation) -> str:
        """Returns the next message for a given negotiation.""" 

class SellerAgent(Agent):
    def decide(self, negotiation: Negotiation) -> str:
        # Todas las negociaciones de este vendedor
        all_negos = [
            n for n in self.negotiations.values()
            if n.seller_id == self.id
        ]
        other_status = [
            {
                "buyer": n.buyer_id,
                "status": n.status.name,
                "last_msg": n.turns[-1].message if n.turns else "",
            }
            for n in all_negos
        ]
        conversation_history = "\n".join(f"{t.sender_id}: {t.message}" for t in negotiation.turns)
        prompt = self.tmpl.render(
            self.prompt_path,
            current_terms = negotiation.final_terms or negotiation.terms,
            rounds_left   = negotiation.max_turns - len(negotiation.turns)//2,
            constraints   = negotiation.terms.__dict__,
            conversation_history = conversation_history,
            urgency       = self.urgency,
            weights       = self.term_weights,
            other_negotiations = other_status,
        )
        return self.repo.run(prompt)

class BuyerAgent(Agent):
    def decide(self, negotiation: Negotiation) -> str:
        # Todas las negociaciones de este vendedor
        all_negos = [
            n for n in self.negotiations.values()
            if n.seller_id == negotiation.seller_id
        ]
        other_status = [
            {
                "buyer": n.buyer_id,
                "status": n.status.name,
                "last_msg": n.turns[-1].message if n.turns else "",
            }
            for n in all_negos
        ]
        conversation_history = "\n".join(f"{t.sender_id}: {t.message}" for t in negotiation.turns)
        prompt = self.tmpl.render(
            self.prompt_path,
            current_terms = negotiation.final_terms or negotiation.terms,
            rounds_left   = negotiation.max_turns - len(negotiation.turns)//2,
            constraints   = negotiation.terms.__dict__,
            conversation_history = conversation_history,
            urgency       = self.urgency,
            weights       = self.term_weights,
            other_negotiations = other_status,
        )
        return self.repo.run(prompt) 