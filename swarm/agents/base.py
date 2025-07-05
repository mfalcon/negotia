from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from ..utils.template_manager import TemplateManager
from ..core.negotiation import Negotiation
from ..core.terms import MultiItemTerms

class Agent(ABC):
    """
    Clase base para BuyerAgent y SellerAgent.
    """
    def __init__(self,
                 agent_id: str,
                 prompt_path: str,
                 repo,
                 urgency: float,
                 term_weights: Dict[str, float],
                 custom_prompt: Optional[str] = None,
                 multi_item_prompt_path: Optional[str] = None):
        self.id           = agent_id
        self.repo         = repo
        self.urgency      = urgency
        self.term_weights = term_weights
        self.prompt_path  = prompt_path
        self.multi_item_prompt_path = multi_item_prompt_path
        self.custom_prompt = custom_prompt
        self.tmpl         = TemplateManager()
        self.negotiations: Dict[str, Negotiation] = {}

    @abstractmethod
    def decide(self, negotiation: Negotiation) -> str:
        """Returns the next message for a given negotiation."""
    
    def _get_prompt_path(self, negotiation: Negotiation) -> str:
        """Get the appropriate prompt path based on negotiation type"""
        if negotiation.is_multi_item() and self.multi_item_prompt_path:
            return self.multi_item_prompt_path
        return self.prompt_path

class SellerAgent(Agent):
    def __init__(self, *args, **kwargs):
        # Set default multi-item prompt if not provided
        if 'multi_item_prompt_path' not in kwargs:
            kwargs['multi_item_prompt_path'] = 'multi_item_seller_prompt.j2'
        super().__init__(*args, **kwargs)

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
        
        # Use custom prompt if available, otherwise use appropriate template
        if self.custom_prompt:
            prompt = self.tmpl.render_custom(
                self.custom_prompt,
                current_terms = negotiation.final_terms or negotiation.terms,
                rounds_left   = negotiation.max_turns - len(negotiation.turns)//2,
                constraints   = negotiation.terms,
                conversation_history = conversation_history,
                urgency       = self.urgency,
                weights       = self.term_weights,
                other_negotiations = other_status,
                agent_name    = self.id,
            )
        else:
            prompt_path = self._get_prompt_path(negotiation)
            prompt = self.tmpl.render(
                prompt_path,
                current_terms = negotiation.final_terms or negotiation.terms,
                rounds_left   = negotiation.max_turns - len(negotiation.turns)//2,
                constraints   = negotiation.terms,
                conversation_history = conversation_history,
                urgency       = self.urgency,
                weights       = self.term_weights,
                other_negotiations = other_status,
                agent_name    = self.id,
            )
        return self.repo.run(prompt)

class BuyerAgent(Agent):
    def __init__(self, *args, **kwargs):
        # Set default multi-item prompt if not provided
        if 'multi_item_prompt_path' not in kwargs:
            kwargs['multi_item_prompt_path'] = 'multi_item_buyer_prompt.j2'
        super().__init__(*args, **kwargs)

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
        
        # Use custom prompt if available, otherwise use appropriate template
        if self.custom_prompt:
            prompt = self.tmpl.render_custom(
                self.custom_prompt,
                current_terms = negotiation.final_terms or negotiation.terms,
                rounds_left   = negotiation.max_turns - len(negotiation.turns)//2,
                constraints   = negotiation.terms,
                conversation_history = conversation_history,
                urgency       = self.urgency,
                weights       = self.term_weights,
                other_negotiations = other_status,
                agent_name    = self.id,
            )
        else:
            prompt_path = self._get_prompt_path(negotiation)
            prompt = self.tmpl.render(
                prompt_path,
                current_terms = negotiation.final_terms or negotiation.terms,
                rounds_left   = negotiation.max_turns - len(negotiation.turns)//2,
                constraints   = negotiation.terms,
                conversation_history = conversation_history,
                urgency       = self.urgency,
                weights       = self.term_weights,
                other_negotiations = other_status,
                agent_name    = self.id,
            )
        return self.repo.run(prompt) 