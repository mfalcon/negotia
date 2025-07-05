# Swarm Negotiation System – Technical Specification

## 1. Purpose
The **swarm** package orchestrates multiple simultaneous, chat-based negotiations between autonomous AI agents (sellers & buyers) competing over items. It supports both **single-item** and **multi-item negotiations with quantities**. The system provides:

* Re-usable agent abstractions (prompting, model repository, decision loop)
* A negotiation engine with turn management & game-rules enforcement
* YAML-driven configuration for items, agents and negotiations
* Modular support for different LLM providers (OpenAI, Anthropic, Google, Ollama)
* **Multi-item negotiations** with quantity management and bulk pricing
* Automatic logging & evaluation of each negotiation

---

## 2. High-Level Architecture
```
┌────────────┐   build()   ┌─────────────┐            ┌─────────────┐
│ config.yaml│ ───────────▶│  Swarm      │   runs N   │ Negotiation │
└────────────┘             │  Runner     │ ──────────▶│ instances   │
                           └─────────────┘            └─────┬───────┘
                                    ▲                       │turns[]
                                    │decide()               ▼
                        ┌───────────┴───────────┐  max_turns*2 msgs
                        │   Agent (base)        │<───────────────┐
                        ├──────────┬────────────┤                │
                        │ BuyerAgent│ SellerAgent│                │
                        └──────────┴────────────┘                │
                                   │uses                         │
                                   ▼                            │
                         ┌──────────────────┐ prompt/render      │
                         │ TemplateManager  │────────────────────┘
                         └──────────────────┘
```
*`max_turns` defaults to **10** (→ 20 chat messages)*

### 2.1 Module Map
| Folder / File | Role |
|---------------|------|
| `swarm/main.py` | CLI entry-point & SwarmRunner bootstrapping |
| `swarm/config.yaml` | Example single-item scenario (2 sellers × 3 buyers × 2 negotiations) |
| `swarm/config_multi_item.yaml` | **NEW**: Multi-item scenario with quantities & bulk pricing |
| `swarm/config_tech_components.yaml` | **NEW**: Tech components scenario (GPUs/CPUs/SSDs – 3 sellers × 6 buyers) |
| `swarm/core/negotiation.py` | Dataclasses `Negotiation`, `Turn`, enum `NegotiationStatus` |
| `swarm/core/terms.py` | **EXTENDED**: `ItemTerms`, `MultiItemTerms`, `ItemRequest` |
| `swarm/core/scoring.py` | **EXTENDED**: Scoring for both single & multi-item negotiations |
| `swarm/agents/base.py` | `Agent` superclass + concrete `SellerAgent` & `BuyerAgent` |
| `swarm/agents/repositories.py` | LLM provider adapters (`OpenAIRepository`, `AnthropicRepository`, `GoogleRepository`, `OllamaRepository`) |
| `swarm/prompts/*.j2` | Jinja2 prompt templates for default agents |
| `swarm/prompts/multi_item_*.j2` | **NEW**: Multi-item specific prompt templates |
| `swarm/utils/file_io.py` | Persisting chat logs `logs/<negotiation-id>/chat.txt` |

---

## 3. Data Model

### 3.1 Single-Item Terms ( `swarm/core/terms.py` )
```python
@dataclass
class ItemTerms:
    price:        Range  # (min, max, reference)
    delivery_days:Range
    upfront_pct:  Range
    
    # Optional metadata
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
```

### 3.2 Multi-Item Terms (**NEW**)
```python
@dataclass
class ItemRequest:
    item_id: str
    quantity: int
    max_quantity: Optional[int] = None  # Maximum buyer will accept
    min_quantity: Optional[int] = None  # Minimum buyer needs

@dataclass
class MultiItemTerms:
    items: Dict[str, ItemTerms]  # item_id -> ItemTerms
    requests: List[ItemRequest]  # Items being negotiated
    
    # Global terms for entire deal
    global_delivery_days: Optional[Range] = None
    global_upfront_pct: Optional[Range] = None
    
    # Bulk pricing discounts
    bulk_discount_tiers: Dict[int, float] = {}  # quantity -> discount %
```

### 3.3 Negotiation
```python
@dataclass
class Negotiation:
    id: str
    seller_id: str
    buyer_id: str
    item_id: str  # For backward compatibility
    terms: Union[ItemTerms, MultiItemTerms]  # **EXTENDED**
    max_turns: int = 10
    turns: List[Turn] = field(default_factory=list)
    status: NegotiationStatus = NegotiationStatus.ONGOING
    final_terms: Optional[Dict[str, Union[float, Dict[str, float]]]] = None
    
    # Multi-item fields
    item_ids: Optional[List[str]] = None
    negotiation_type: str = "single"  # "single" or "multi"
```

---

## 4. Agent Lifecycle
1. **Build** – `SwarmRunner` converts YAML agent config → `SellerAgent` / `BuyerAgent`.
2. **Prompt Selection** – Agent chooses appropriate template based on negotiation type:
   - Single-item: `seller_prompt.j2` / `buyer_prompt.j2`
   - Multi-item: `multi_item_seller_prompt.j2` / `multi_item_buyer_prompt.j2`
3. **Prompt Render** – `Agent.decide()` creates a prompt via `TemplateManager`.
    * Custom inline prompt (`custom_prompt`) overrides template file.
    * Context variables: `current_terms`, `rounds_left`, `constraints`, `conversation_history`, `urgency`, `weights`, `other_negotiations`.
4. **LLM Call** – delegated to repository (`repo.run(prompt)`), returning raw text.
5. **Term Extraction** – Enhanced parser handles both single and multi-item formats.
6. **Update** – `Negotiation.add_turn()` appends the message & enforces rules.

### 4.1 Constraints Visible to Agent
**Single-item:**
```yaml
constraints:
  price:          {minimum, reference, maximum}
  delivery_days:  {...}
  upfront_pct:    {...}
```

**Multi-item:**
```yaml
constraints:
  items:          {item1: ItemTerms, item2: ItemTerms, ...}
  requests:       [{item_id, quantity, min_quantity, max_quantity}, ...]
  global_delivery_days: {minimum, reference, maximum}
  global_upfront_pct:   {...}
  bulk_discount_tiers:  {10: 5%, 20: 10%, ...}
```

---

## 5. Game Rules & Constraints
| Rule | Source | Enforcement |
|------|--------|-------------|
| Max rounds **10** | `Negotiation.max_turns` | `Negotiation.add_turn()` auto-fails |
| Acceptance phrase | Templates | Parser looks for `Done deal!` prefix |
| Terms range | `ItemTerms` / `MultiItemTerms` | Proposals are clamped server-side |
| Auto-accept final round | `Agent.decide()` logic | If terms in range & `rounds_left <= 1` |
| One item / exclusive sale | Seller template context | Human-level behaviour (not code-enforced) |
| **Quantity constraints** | **`ItemRequest.min/max_quantity`** | **Validated during term extraction** |
| **Bulk discounts** | **`MultiItemTerms.bulk_discount_tiers`** | **Applied automatically in scoring** |

---

## 6. Prompt System
* **Jinja2** templates under `swarm/prompts` render seller/buyer messages.
* **Automatic template selection** based on negotiation type:
  - Single-item: Uses standard `seller_prompt.j2` / `buyer_prompt.j2`
  - Multi-item: Uses `multi_item_seller_prompt.j2` / `multi_item_buyer_prompt.j2`
* Variables injected by `TemplateManager` include negotiation stats & external competition.
* **Multi-item context** includes item lists, quantities, bulk discounts, and total budget calculations.
* Supports full Jinja2 control flow so advanced tactics can be encoded.

---

## 7. Repository Abstraction
```python
class BaseRepository:
    def run(self, prompt: str) -> str: ...
```
Concrete impls translate the generic call into provider-specific API invocations:
* **OpenAIRepository** – uses `openai` python SDK
* **AnthropicRepository** – uses `anthropic`
* **GoogleRepository** – uses `google-generativeai`
* **OllamaRepository** – local inference via REST `http://localhost:11434` (default model `llama3`)

`mk_repo(provider_type, model_name, api_key)` factory hides the switch logic.

---

## 8. Multi-Item Term Extraction (**NEW**)
The system recognizes multiple acceptance formats:

**Single-item format:**
```
"Done deal! price=1200, delivery=7, upfront=50"
```

**Multi-item formats:**
```
"Done deal! total=5500, delivery=10, upfront=50"
"Done deal! laptop: 5x1100, monitor: 5x380, delivery=10, upfront=50"
```

**Bulk discount calculation:**
- Automatically applied based on total quantity
- Configurable tiers (e.g., 10+ items = 5% discount)
- Reflected in final pricing and scoring

---

## 9. Logging & Evaluation
* `swarm/utils/file_io.save_log()` writes every turn with timestamp to `logs/<negotiation-id>/chat.txt`.
* CLI output summarises each negotiation (`seller_score`, `buyer_score`, `gap`) with negotiation type.
* **Enhanced scoring** handles multi-item total pricing and bulk discounts.
* Optional post-hoc analysis scripts (`analyze_seller.py`, `analyze_buyer.py`) use GPT-4o to grade technique effectiveness.

---

## 10. Configuration Schema (`config.yaml`)

### 10.1 Single-Item Negotiation (Backward Compatible)
```yaml
items:
  item1: {price: {reference, min, max}, delivery_days: {...}, upfront_pct: {...}}
negotiations:
  - id: N1
    seller: seller1
    item: item1
    buyers: [buyer1, buyer2]
```

### 10.2 Multi-Item Negotiation (**NEW**)
```yaml
items:
  laptop: {price: {reference: 1200, min: 900, max: 1500}, ...}
  monitor: {price: {reference: 400, min: 300, max: 500}, ...}
  
negotiations:
  - id: N3_office_setup
    seller: tech_seller
    buyers: [startup_buyer, enterprise_buyer]
    multi_item:
      requests:
        - item_id: laptop
          quantity: 5
          min_quantity: 3
          max_quantity: 8
        - item_id: monitor
          quantity: 5
          min_quantity: 3
          max_quantity: 8
      global_delivery_days: {reference: 10, min: 7, max: 21}
      global_upfront_pct: {reference: 50, min: 30, max: 70}
      bulk_discount_tiers:
        10: 5    # 5% discount for 10+ total items
        20: 10   # 10% discount for 20+ total items
```

### 10.3 Tech Components Scenario (**NEW**)
```yaml
items:
  nvidia_3090:
    name: "NVIDIA RTX 3090 24GB"
    price: {reference: 1500, min: 1200, max: 1800}
    delivery_days: {reference: 7, min: 3, max: 14}
    upfront_pct: {reference: 60, min: 40, max: 80}

  i9_processor:
    name: "Intel Core i9-13900K"
    price: {reference: 600, min: 450, max: 750}
    delivery_days: {reference: 5, min: 2, max: 10}
    upfront_pct: {reference: 50, min: 30, max: 70}

  ssd_5000gb:
    name: "5TB NVMe SSD"
    price: {reference: 800, min: 600, max: 1000}
    delivery_days: {reference: 4, min: 2, max: 8}
    upfront_pct: {reference: 40, min: 20, max: 60}

negotiations:
  - id: N2_ai_training_rigs
    seller: gpu_specialist
    buyers: [ai_startup, research_lab, data_center]
    max_turns: 15
    multi_item:
      requests:
        - item_id: nvidia_3090
          quantity: 8
          min_quantity: 4
          max_quantity: 12
      global_delivery_days: {reference: 10, min: 5, max: 14}
      global_upfront_pct: {reference: 60, min: 40, max: 80}
      bulk_discount_tiers:
        6: 4  # 4% discount for 6+ GPUs
        10: 8 # 8% discount for 10+ GPUs
```

---

## 11. Extensibility Notes
* **New LLM provider** ⇒ add class in `swarm/agents/repositories.py` & update `mk_repo()`.
* **Different acceptance pattern** ⇒ tweak regex in `extract_terms_from_message()`.
* **Alternate scoring** ⇒ modify `swarm/core/scoring.py`.
* **Custom bulk pricing** ⇒ extend `MultiItemTerms.bulk_discount_tiers`.
* **Item categories** ⇒ use `ItemTerms.category` for category-specific logic.

---

## 12. Testing
* `tests/test_negotiator.py` – unit tests for term extraction & prompt content.
* `tests/test_prompts.py` – snapshot tests ensuring Jinja variables render.
* **NEW**: Multi-item test cases for quantity validation and bulk pricing.
* Run `pytest -q` from project root.

---

## 13. CLI Usage
```bash
# Run single-item scenario
python -m swarm.main

# Run multi-item scenario
python -m swarm.main --config swarm/config_multi_item.yaml

# Run tech-components scenario
python -m swarm.main --config swarm/config_tech_components.yaml
```

Outputs summary & detailed chat logs under `./logs/`.

---

## 14. Future Improvements
* Persist negotiation state in DB for multi-process coordination
* Implement **timeout** for LLM responses
* Add **Monte–Carlo self-play** to tune agent parameters automatically
* Visual web dashboard (Streamlit) for real-time monitoring
* **Dynamic quantity adjustment** during negotiations
* **Cross-item dependencies** (e.g., laptop requires monitor)
* **Inventory management** with stock limitations per item

---

© 2025 NegotiAI – MIT License 