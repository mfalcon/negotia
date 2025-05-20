from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from .terms import ItemTerms

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
    item_id: str
    terms: ItemTerms
    max_turns: int = 10
    turns: List[Turn] = field(default_factory=list)
    status: NegotiationStatus = NegotiationStatus.ONGOING
    final_terms: Optional[Dict[str, float]] = None

    def add_turn(self, turn: Turn) -> None:
        if self.status != NegotiationStatus.ONGOING:
            return
        self.turns.append(turn)
        if len(self.turns) >= self.max_turns * 2:          # vendedor+comprador = 2 mensajes por turno
            self.status = NegotiationStatus.FAILED

    def register_agreement(self, terms: Dict[str, float]) -> None:
        """Marca la negociación como cerrada y guarda los términos finales."""
        if self.status == NegotiationStatus.ONGOING:
            self.final_terms = terms
            self.status = NegotiationStatus.AGREEMENT

    def is_finished(self) -> bool:
        return self.status != NegotiationStatus.ONGOING 