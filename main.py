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
        urgency_level = "low" if rounds_left > 5 else "medium" if rounds_left > 2 else "critical"
        
        urgency_context = {
            "low": "Negotiate towards an agreement while protecting your interests.",
            "medium": "Time is short - focus on reaching a deal with acceptable terms.",
            "critical": f"FINAL ROUNDS! Accept any terms within your constraints or risk no deal at all!"
        }

        # Check if terms are within constraints
        terms_within_constraints = all(
            self.constraints[term][0] <= current_terms[term] <= self.constraints[term][1]
            for term in current_terms
        )

        terms_analysis = f"Current terms are {'within' if terms_within_constraints else 'outside'} your acceptable range.\n"
        if self.is_seller:
            price_gap = (self.constraints['price'][1] - current_terms['price']) / self.constraints['price'][1] * 100
            terms_analysis += f"Price is {price_gap:.0f}% below your maximum."
        else:
            price_gap = (current_terms['price'] - self.constraints['price'][0]) / self.constraints['price'][0] * 100
            terms_analysis += f"Price is {price_gap:.0f}% above your minimum."

        prompt = f"""You are negotiating as the {role}. Keep your response under 150 words.

Current situation:
- Price: ${current_terms['price']}
- Delivery time: {current_terms['delivery_time']} days
- Upfront payment: {current_terms['payment_terms']}%

Status:
- Rounds left: {rounds_left} out of {self.max_rounds}
- Urgency: {urgency_level}
- Note: {urgency_context[urgency_level]}
- Analysis: {terms_analysis}

Your constraints:
- Price: ${self.constraints['price'][0]} to ${self.constraints['price'][1]}
- Delivery: {self.constraints['delivery_time'][0]} to {self.constraints['delivery_time'][1]} days
- Payment: {self.constraints['payment_terms'][0]}% to {self.constraints['payment_terms'][1]}%

Instructions:
{'ACCEPT THE DEAL if terms are within your constraints! Start response with "I accept these terms"' if rounds_left <= 2 and terms_within_constraints else 'Make a final counter-offer that you would accept' if rounds_left <= 2 else 'Make a counter-proposal with significant concessions'}

Remember: A failed negotiation is worse than a less-than-perfect deal within your constraints.
"""
        return prompt

    def negotiate(self, current_terms: Dict[str, float]) -> Tuple[Dict[str, float], bool]:
        """Negotiate a single round based on current terms."""
        rounds_left = self.max_rounds - len(self.conversation_history)
        
        # Auto-accept if in final rounds and terms are within constraints
        if rounds_left <= 1:  # Force acceptance in the final round if terms are acceptable
            terms_within_constraints = all(
                self.constraints[term][0] <= current_terms[term] <= self.constraints[term][1]
                for term in current_terms
            )
            if terms_within_constraints:
                self.conversation_history.append(
                    f"{'Seller' if self.is_seller else 'Buyer'}: I accept these terms as they are within my constraints."
                )
                return current_terms, True
        
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
        constraints=seller_constraints,
        repository_type="open",
        model_name="phi4",
        max_rounds=10
    )

    buyer = AINegotiator(
        name="Buyer AI",
        is_seller=False,
        constraints=buyer_constraints,
        repository_type="ollama",
        model_name="phi4",
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