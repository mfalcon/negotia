"""
Ejecuta un escenario swarm a partir de un archivo YAML.

Opciones:
  • Desde raíz del proyecto .............  python -m swarm.main
  • Desde dentro de carpeta `swarm/` .....  python main.py
"""

# --- PATH FIX para ejecución como script -----------------------------------
import sys, pathlib
root_path = pathlib.Path(__file__).resolve().parent.parent  # <repo_root>
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

# ---------------------------------------------------------------------------
import argparse, yaml, os, time
from typing import Dict, List, Union

#  IMPORTS ABSOLUTOS (funcionan en ambos modos)
from swarm.core.terms        import Range, ItemTerms, MultiItemTerms, ItemRequest
from swarm.core.negotiation  import Negotiation
from swarm.core.scheduler    import SwarmManager
from swarm.utils.evaluator   import evaluate_swarm
from swarm.agents.base       import SellerAgent, BuyerAgent
from swarm.agents.repositories import OpenAIRepository, OllamaRepository, AnthropicRepository, GoogleRepository
from pathlib import Path

# ------------------------------------------------------------------ #
def mk_repo(repo_type: str, model: str):
    if repo_type == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError("OPENAI_API_KEY not set")
        return OpenAIRepository(model, api_key)
    elif repo_type == "ollama":
        return OllamaRepository(model)
    elif repo_type == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise EnvironmentError("ANTHROPIC_API_KEY not set")
        return AnthropicRepository(model, api_key)
    elif repo_type == "google":
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise EnvironmentError("GOOGLE_API_KEY not set")
        return GoogleRepository(model, api_key)
    else:
        raise ValueError(f"Unsupported repo: {repo_type}. Supported: openai, ollama, anthropic, google")

# ------------------------------------------------------------------ #
def _mk_range(mapping: Dict) -> Range:
    """
    Acepta tanto claves  {min, max, reference}
    como                {minimum, maximum, reference}
    """
    return Range(
        minimum   = mapping.get("minimum", mapping.get("min")),
        maximum   = mapping.get("maximum", mapping.get("max")),
        reference = mapping.get("reference", 0.0),
    )

def parse_item(d: Dict) -> ItemTerms:
    return ItemTerms(
        price         = _mk_range(d["price"]),
        delivery_days = _mk_range(d["delivery_days"]),
        upfront_pct   = _mk_range(d["upfront_pct"]),
        name          = d.get("name"),
        description   = d.get("description"),
        category      = d.get("category"),
    )

def parse_item_request(d: Dict) -> ItemRequest:
    """Parse item request from configuration"""
    return ItemRequest(
        item_id      = d["item_id"],
        quantity     = d["quantity"],
        max_quantity = d.get("max_quantity"),
        min_quantity = d.get("min_quantity"),
    )

def parse_multi_item_terms(d: Dict, items: Dict[str, ItemTerms]) -> MultiItemTerms:
    """Parse multi-item terms from configuration"""
    requests = [parse_item_request(req) for req in d["requests"]]
    
    # Extract only the items that are being requested
    relevant_items = {req.item_id: items[req.item_id] for req in requests}
    
    return MultiItemTerms(
        items                = relevant_items,
        requests             = requests,
        global_delivery_days = _mk_range(d["global_delivery_days"]) if "global_delivery_days" in d else None,
        global_upfront_pct   = _mk_range(d["global_upfront_pct"]) if "global_upfront_pct" in d else None,
        bulk_discount_tiers  = d.get("bulk_discount_tiers", {}),
    )

# ------------------------------------------------------------------ #
def build_from_config(cfg_path: str):
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}          # <-- evita None

    if not all(k in cfg for k in ("items", "agents", "negotiations")):
        raise ValueError(f"Config file {cfg_path} is missing required sections")

    # Items ----------------------------------------------------------
    items = {k: parse_item(v) for k, v in cfg["items"].items()}

    # Agents ---------------------------------------------------------
    sellers, buyers = {}, {}
    for sid, s_cfg in cfg["agents"]["sellers"].items():
        repo = mk_repo(s_cfg["repo"], s_cfg["model"])
        sellers[sid] = SellerAgent(
            agent_id     = sid,
            prompt_path  = s_cfg["prompt"],
            repo         = repo,
            urgency      = s_cfg["urgency"],
            term_weights = s_cfg["term_weights"],
            custom_prompt = s_cfg.get("custom_prompt")  # Optional custom prompt
        )
    for bid, b_cfg in cfg["agents"]["buyers"].items():
        repo = mk_repo(b_cfg["repo"], b_cfg["model"])
        buyers[bid] = BuyerAgent(
            agent_id     = bid,
            prompt_path  = b_cfg["prompt"],
            repo         = repo,
            urgency      = b_cfg["urgency"],
            term_weights = b_cfg["term_weights"],
            custom_prompt = b_cfg.get("custom_prompt")  # Optional custom prompt
        )

    # Negotiations ---------------------------------------------------
    negotiations = []
    for n_cfg in cfg["negotiations"]:
        # Determine if this is a single-item or multi-item negotiation
        if "item" in n_cfg:
            # Single-item negotiation (backward compatibility)
            for buyer_id in n_cfg["buyers"]:
                negotiations.append(
                    Negotiation(
                        id        = f"{n_cfg['id']}_{buyer_id}",
                        seller_id = n_cfg["seller"],
                        buyer_id  = buyer_id,
                        item_id   = n_cfg["item"],
                        terms     = items[n_cfg["item"]],
                        max_turns = n_cfg.get("max_turns", 10)
                    )
                )
        elif "multi_item" in n_cfg:
            # Multi-item negotiation
            multi_terms = parse_multi_item_terms(n_cfg["multi_item"], items)
            for buyer_id in n_cfg["buyers"]:
                negotiations.append(
                    Negotiation(
                        id        = f"{n_cfg['id']}_{buyer_id}",
                        seller_id = n_cfg["seller"],
                        buyer_id  = buyer_id,
                        item_id   = "multi",  # Placeholder for backward compatibility
                        terms     = multi_terms,
                        max_turns = n_cfg.get("max_turns", 10)
                    )
                )
        else:
            raise ValueError(f"Negotiation {n_cfg['id']} must specify either 'item' or 'multi_item'")
    
    return sellers, buyers, negotiations

# ------------------------------------------------------------------ #
def main():
    ap = argparse.ArgumentParser()
    default_cfg = Path(__file__).resolve().parent / "config.yaml"
    ap.add_argument("--config", "-c", default=str(default_cfg))
    args = ap.parse_args()

    sellers, buyers, negotiations = build_from_config(args.config)

    swarm = SwarmManager(sellers, buyers, negotiations)
    t0 = time.time()
    swarm.run()
    elapsed = time.time() - t0

    res, agg = evaluate_swarm(negotiations, buyers, sellers)

    print("\n==== RESULTS ====")
    for nid, r in res.items():
        nego = next(n for n in negotiations if n.id == nid)
        print(f"{nid} ({nego.get_summary()}): seller={r['seller_score']:.3f}  buyer={r['buyer_score']:.3f}  gap={r['gap']:.3f}")
    if agg:
        print(f"\nAverages -> seller={agg['avg_seller']:.3f}  buyer={agg['avg_buyer']:.3f}")
    print(f"\nCompleted in {elapsed:.1f}s")

# ------------------------------------------------------------------ #
if __name__ == "__main__":
    main() 