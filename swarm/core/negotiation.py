from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union
from .terms import ItemTerms, MultiItemTerms

class NegotiationStatus(Enum):
    ONGOING = auto()
    AGREEMENT = auto()
    FAILED = auto()

@dataclass
class Turn:
    sender_id: str
    message: str
    timestamp: float

@dataclass
class Negotiation:
    id: str
    seller_id: str
    buyer_id: str
    item_id: str  # For backward compatibility with single-item negotiations
    terms: Union[ItemTerms, MultiItemTerms]  # Support both single and multi-item
    max_turns: int = 10
    turns: List[Turn] = field(default_factory=list)
    status: NegotiationStatus = NegotiationStatus.ONGOING
    final_terms: Optional[Dict[str, Union[float, Dict[str, float]]]] = None
    
    # Multi-item specific fields
    item_ids: Optional[List[str]] = None  # List of item IDs for multi-item negotiations
    negotiation_type: str = "single"  # "single" or "multi"

    def __post_init__(self):
        """Set negotiation type based on terms"""
        if isinstance(self.terms, MultiItemTerms):
            self.negotiation_type = "multi"
            self.item_ids = list(self.terms.items.keys())
        else:
            self.negotiation_type = "single"
            self.item_ids = [self.item_id]

    def add_turn(self, turn: Turn) -> None:
        if self.status != NegotiationStatus.ONGOING:
            return
        self.turns.append(turn)
        if len(self.turns) >= self.max_turns * 2:          # vendedor+comprador = 2 mensajes por turno
            self.status = NegotiationStatus.FAILED

    def register_agreement(self, terms: Dict[str, Union[float, Dict[str, float]]]) -> None:
        """Marca la negociación como cerrada y guarda los términos finales."""
        if self.status == NegotiationStatus.ONGOING:
            self.final_terms = terms
            self.status = NegotiationStatus.AGREEMENT

    def is_finished(self) -> bool:
        return self.status != NegotiationStatus.ONGOING
    
    def is_multi_item(self) -> bool:
        """Check if this is a multi-item negotiation"""
        return self.negotiation_type == "multi"
    
    def get_item_count(self) -> int:
        """Get the number of items in this negotiation"""
        if self.is_multi_item():
            return len(self.terms.requests)
        return 1
    
    def get_summary(self) -> str:
        """Get a summary of the negotiation"""
        if self.is_multi_item():
            item_list = [f"{req.quantity}x {req.item_id}" for req in self.terms.requests]
            return f"Multi-item: {', '.join(item_list)}"
        else:
            return f"Single item: {self.item_id}" 