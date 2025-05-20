from dataclasses import dataclass
from typing import Tuple

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