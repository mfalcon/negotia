import random
import requests
from typing import Dict, Any, Tuple
import ast
import re
from abc import ABC, abstractmethod
import openai
import time
import os

class AIRepository(ABC):
    @abstractmethod
    def run(self, prompt: str) -> str:
        pass

class OllamaRepository(AIRepository):
    def __init__(self, model_name: str):
        self.url = 'http://localhost:11434/api/generate'
        self.model_name = model_name

    def run(self, prompt: str) -> str:
        data = {
            'model': self.model_name, 
            'prompt': prompt, 
            'stream': False,
            'options': {
                'temperature': 0,
                'num_predict': 250,
            }
        }

        response = requests.post(self.url, json=data)
        return response.json()['response']

class OpenAIRepository(AIRepository):
    def __init__(self, model_name: str, api_key: str = None):
        self.model_name = model_name
        self.client = openai.OpenAI(api_key=api_key or os.getenv('OPENAI_API_KEY'))
        if not (api_key or os.getenv('OPENAI_API_KEY')):
            raise ValueError("OpenAI API key must be provided either through environment variable OPENAI_API_KEY or as a parameter")

    def run(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=250
        )
        return response.choices[0].message.content

class AIModel:
    def __init__(self, 
                 repository_type: str = "ollama",
                 model_name: str = "llama2:latest",
                 api_key: str = None):
        """
        Initialize AI Model with specified repository
        
        Args:
            repository_type: "ollama" or "openai"
            model_name: Name of the model to use
            api_key: OpenAI API key (required for OpenAI repository)
        """
        if repository_type == "ollama":
            self.repository = OllamaRepository(model_name)
        elif repository_type == "openai":
            if not api_key:
                raise ValueError("OpenAI API key is required for OpenAI repository")
            self.repository = OpenAIRepository(model_name, api_key)
        else:
            raise ValueError(f"Unsupported repository type: {repository_type}")

    def generate_text(self, prompt: str) -> str:
        """Generate text using the specified AI model."""
        try:
            return self.repository.run(prompt)
        except Exception as e:
            print(f"Error using AI API: {e}")
            return "Error"

class NegotiationEvaluator:
    def __init__(self, seller_constraints: Dict[str, Tuple[float, float]], buyer_constraints: Dict[str, Tuple[float, float]]):
        self.seller_constraints = seller_constraints
        self.buyer_constraints = buyer_constraints

    def evaluate(self, final_terms: Dict[str, float]) -> Dict[str, Any]:
        """Evaluate the negotiation outcome for both parties."""
        evaluation = {}

        for party, constraints in [("seller", self.seller_constraints), ("buyer", self.buyer_constraints)]:
            scores = {}
            for term, (min_val, max_val) in constraints.items():
                term_value = final_terms.get(term, min_val)

                if party == "seller":
                    score = (term_value - min_val) / (max_val - min_val) * 100
                else:
                    score = (max_val - term_value) / (max_val - min_val) * 100

                score = max(0, min(score, 100))  # Ensure score is between 0-100
                scores[term] = score

            avg_score = sum(scores.values()) / len(scores)
            evaluation[party] = {
                "scores": scores,
                "average_score": avg_score,
                "comment": f"{party.capitalize()} achieved an average score of {avg_score:.2f} across all terms."
            }

        return evaluation

class AINegotiator:
    def __init__(self, 
                 name: str, 
                 is_seller: bool, 
                 constraints: Dict[str, Tuple[float, float]], 
                 repository_type: str = "ollama",
                 model_name: str = "llama3.2:latest",
                 api_key: str = None,
                 max_rounds: int = 20):
        self.name = name
        self.is_seller = is_seller
        self.constraints = constraints
        self.ai_model = AIModel(
            repository_type=repository_type,
            model_name=model_name,
            api_key=api_key
        )
        self.conversation_history = []
        self.max_rounds = max_rounds

    def _extract_terms(self, response: str) -> Dict[str, float]:
        """Extract numerical terms from a natural language response."""
        terms = {}
        try:
            # Look for price mentions
            if "price" in response.lower():
                price_matches = re.findall(r'\$?(\d+(?:,\d+)?(?:\.\d+)?)', response)
                if price_matches:
                    terms["price"] = float(price_matches[0].replace(',', ''))
            
            # Look for delivery time mentions
            if "delivery" in response.lower() or "days" in response.lower():
                delivery_matches = re.findall(r'(\d+)(?:\s*(?:days?|business days?))', response.lower())
                if delivery_matches:
                    terms["delivery_time"] = float(delivery_matches[0])
            
            # Look for payment terms mentions
            if "payment" in response.lower() or "upfront" in response.lower():
                payment_matches = re.findall(r'(\d+)%?\s*(?:upfront|payment)', response.lower())
                if payment_matches:
                    terms["payment_terms"] = float(payment_matches[0])
        except Exception as e:
            print(f"Error extracting terms: {e}")
        
        return terms

    def _extract_acceptance(self, response: str) -> bool:
        """Check if the response indicates acceptance of terms."""
        # Only allow very explicit acceptance phrases
        acceptance_phrases = [
            "i accept these terms",
            "i agree to these terms",
            "deal accepted"
        ]
        response_lower = response.lower().strip()
        
        # Check for exact matches at the start of the response
        is_accepted = any(response_lower.startswith(phrase) for phrase in acceptance_phrases)
        
        # Check for explicit rejection phrases to avoid false positives
        rejection_phrases = [
            "i don't accept",
            "i do not accept",
            "i cannot accept",
            "i can't accept",
            "not acceptable",
            "no deal"
        ]
        is_rejected = any(phrase in response_lower for phrase in rejection_phrases)
        
        # Additional check: Make sure there's no counter-proposal if accepting
        contains_numbers = bool(re.search(r'\$?\d+', response_lower))
        
        return is_accepted and not is_rejected and not contains_numbers

    def _create_negotiation_prompt(self, current_terms: Dict[str, float], rounds_left: int) -> str:
        """Create a context-aware negotiation prompt."""
        role = "seller" if self.is_seller else "buyer"
        urgency_level = "low" if rounds_left > 10 else "medium" if rounds_left > 5 else "high"
        
        urgency_context = {
            "low": "Take your time to negotiate the best possible terms. Don't accept unless the deal is clearly in your favor.",
            "medium": "While time is becoming a factor, don't rush to accept unfavorable terms. Keep negotiating for better conditions.",
            "high": "Although time is running out, only accept if the terms are reasonably close to your goals. A bad deal is worse than no deal."
        }

        role_context = {
            "seller": {
                "goal": "As the seller, maximize your profits and minimize risks. Your ideal terms are:\n" +
                       f"- Highest possible price (your minimum is ${self.constraints['price'][0]})\n" +
                       f"- Longest possible delivery time (at least {self.constraints['delivery_time'][0]} days)\n" +
                       f"- Maximum upfront payment (at least {self.constraints['payment_terms'][0]}%)",
                "tactics": [
                    "Start high and concede slowly",
                    "Emphasize your product's quality, reliability, and unique value",
                    "Highlight your costs, expertise, and market position",
                    "Use scarcity or time pressure when appropriate",
                    "Make small concessions to show flexibility"
                ]
            },
            "buyer": {
                "goal": "As the buyer, minimize costs and secure favorable terms. Your ideal terms are:\n" +
                       f"- Lowest possible price (your maximum is ${self.constraints['price'][1]})\n" +
                       f"- Shortest possible delivery time (max {self.constraints['delivery_time'][1]} days)\n" +
                       f"- Minimum upfront payment (max {self.constraints['payment_terms'][1]}%)",
                "tactics": [
                    "Start low and concede gradually",
                    "Compare with market alternatives",
                    "Question high prices and long delivery times",
                    "Emphasize potential for long-term business",
                    "Make small concessions to show good faith"
                ]
            }
        }

        conversation_context = "\n".join(self.conversation_history[-4:]) if self.conversation_history else ""
        
        prompt = f"""You are negotiating as the {role}. Respond in first person, representing your role directly. Keep your response concise and under 150 words.

Current situation:
- Current price: ${current_terms['price']}
- Delivery time: {current_terms['delivery_time']} days
- Upfront payment: {current_terms['payment_terms']}%

Negotiation status:
- Rounds remaining: {rounds_left} out of {self.max_rounds}
- Urgency level: {urgency_level}
- Note: {urgency_context[urgency_level]}

Your goal: {role_context[role]['goal']}

Your negotiation tactics:
{chr(10).join(f"- {tactic}" for tactic in role_context[role]['tactics'])}

Previous conversation:
{conversation_context}

Instructions:
1. If you want to ACCEPT the current terms (only if they are very close to your goals), start your response with one of these exact phrases:
   - "I accept these terms"
   - "I agree to these terms"
   - "Deal accepted"
   
2. If you want to continue negotiating (recommended unless terms are very favorable):
   - Make a counter-proposal with specific numbers
   - Justify your position strongly using first-person perspective ("I", "my", "we", "our")
   - Include specific numbers for price, delivery time, and payment terms
   - Make small, strategic concessions
   - Use persuasion tactics to strengthen your position

Remember:
- Speak in first person - you ARE the {role}
- Be assertive and professional
- Don't accept terms just because time is running out
- Make calculated concessions based on your priorities
- Use your negotiation tactics effectively
- Only accept terms that are genuinely favorable to your side
"""
        return prompt

    def negotiate(self, current_terms: Dict[str, float]) -> Tuple[Dict[str, float], bool]:
        """
        Negotiate a single round based on current terms.
        Returns: (proposed_terms, accepted)
        """
        rounds_left = self.max_rounds - len(self.conversation_history)
        prompt = self._create_negotiation_prompt(current_terms, rounds_left)
        response = self.ai_model.generate_text(prompt)
        
        # Store the conversation
        self.conversation_history.append(f"{'Seller' if self.is_seller else 'Buyer'}: {response}")
        
        # Check if terms are accepted
        accepted = self._extract_acceptance(response)
        
        # Extract terms from natural language response
        proposed_terms = self._extract_terms(response)
        
        # If terms are accepted but no new terms proposed, use current terms
        if accepted and not proposed_terms:
            return current_terms, True
            
        # Fill in any missing terms with current terms
        for term in current_terms:
            if term not in proposed_terms:
                proposed_terms[term] = current_terms[term]
            else:
                # Ensure proposed terms are within constraints
                min_val, max_val = self.constraints[term]
                proposed_terms[term] = max(min_val, min(max_val, proposed_terms[term]))
        
        return proposed_terms, accepted

def negotiate(seller: AINegotiator, buyer: AINegotiator) -> Dict[str, float]:
    """Simulate a negotiation between seller and buyer."""
    max_rounds = min(seller.max_rounds, buyer.max_rounds)
    rounds_remaining = max_rounds
    
    current_terms = {
        "price": (seller.constraints["price"][0] + buyer.constraints["price"][1]) / 2,
        "delivery_time": (seller.constraints["delivery_time"][0] + buyer.constraints["delivery_time"][1]) / 2,
        "payment_terms": (seller.constraints["payment_terms"][0] + buyer.constraints["payment_terms"][1]) / 2
    }

    print("\nNegotiation Starting...")
    print(f"Initial terms: Price=${current_terms['price']}, Delivery={current_terms['delivery_time']} days, Payment={current_terms['payment_terms']}% upfront")
    
    while rounds_remaining > 0:
        print(f"\n--- Round {max_rounds - rounds_remaining + 1} ---")
        
        # Seller's turn
        seller_proposal, seller_accepted = seller.negotiate(current_terms)
        seller_message = seller.conversation_history[-1].split(": ", 1)[1]
        print(f"\nSeller: {seller_message}")
        
        if seller_accepted:
            print("\n[Deal reached: Seller accepted the terms]")
            return current_terms
            
        # Buyer's turn
        buyer_proposal, buyer_accepted = buyer.negotiate(seller_proposal)
        buyer_message = buyer.conversation_history[-1].split(": ", 1)[1]
        print(f"\nBuyer: {buyer_message}")
        
        if buyer_accepted:
            print("\n[Deal reached: Buyer accepted the terms]")
            return seller_proposal

        current_terms = buyer_proposal
        rounds_remaining -= 1
        
        if rounds_remaining <= 5:
            print(f"\n[Warning: {rounds_remaining} rounds remaining]")
            
        time.sleep(1)

    print("\n[Negotiation failed: No deal reached]")
    return None

if __name__ == "__main__":
    # Example constraints for seller and buyer
    seller_constraints = {
        "price": (1000, 1500),
        "delivery_time": (7, 14),
        "payment_terms": (50, 100)
    }

    buyer_constraints = {
        "price": (800, 1200),
        "delivery_time": (5, 10),
        "payment_terms": (0, 50)
    }

    # Get OpenAI API key from environment
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if not openai_api_key:
        raise ValueError("Please set OPENAI_API_KEY environment variable")

    seller = AINegotiator(
        name="Seller AI",
        is_seller=True,
        repository_type="openai",
        constraints=seller_constraints,
        model_name="gpt-4o-mini",
        api_key=openai_api_key,
        max_rounds=10
    )

    buyer = AINegotiator(
        name="Buyer AI",
        is_seller=False,
        constraints=buyer_constraints,
        repository_type="openai",
        model_name="gpt-4o-mini",
        api_key=openai_api_key,
        max_rounds=10
    )

    # Simulate negotiation
    final_terms = negotiate(seller, buyer)
    
    if final_terms is None:
        print("\nNegotiation failed - No agreement reached!")
    else:
        print(f"\nFinal Terms: {final_terms}")
        
        # Evaluate the negotiation
        evaluator = NegotiationEvaluator(seller_constraints, buyer_constraints)
        evaluation = evaluator.evaluate(final_terms)
        
        print("\nNegotiation Evaluation:")
        for role, result in evaluation.items():
            print(f"{role.capitalize()}:")
            print(f" - Scores: {result['scores']}")
            print(f" - Average Score: {result['average_score']:.2f}")
            print(f" - Comment: {result['comment']}\n")