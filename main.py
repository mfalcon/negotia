import random
import requests
from typing import Dict, Any, Tuple
import ast
import re
from abc import ABC, abstractmethod
import openai
import time
import os
from datetime import datetime

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
            #temperature=0,
            #max_tokens=250
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
        
        if self.is_seller:
            # Enhanced seller prompt with "Never Split the Difference" techniques
            urgency_context = {
                "low": "Use tactical empathy while anchoring high. Focus on value creation and loss prevention.",
                "medium": "Create urgency through calculated questions about the cost of delay.",
                "critical": "Use 'that's right' moments to build agreement, then push for final terms within your constraints."
            }

            # Calculate the ideal target price (slightly below maximum to leave room for negotiation)
            target_price = self.constraints['price'][1] * 0.95
            current_price_gap = ((target_price - current_terms['price']) / target_price) * 100

            negotiation_tactics = f"""
Key negotiation tactics to use:
1. Mirror their concerns using their own words
2. Label emotions: "It seems like..." or "It sounds like..."
3. Use calibrated questions starting with 'How' or 'What'
4. Create urgency by highlighting potential losses
5. Focus on value creation, not just price

Current situation analysis:
- Price gap: {current_price_gap:.1f}% below target
- Time pressure: {urgency_level}
- Buyer's likely concerns: cost, delivery reliability, payment flexibility

Negotiation guidelines:
1. If price is mentioned, always anchor back to value and quality
2. Use "fair" strategically: "We want to find a fair solution that works for both parties"
3. Let them feel in control while guiding to your target
4. Use silence after making key points
5. If they push back, respond with "How am I supposed to do that?" or "What are we trying to solve for?"

Remember:
- Never split the difference immediately
- Use "no" to your advantage - it starts the real negotiation
- Make them solve your problems
- The person across the table is never the problem; the situation is the problem
"""
        else:
            # Original buyer context
            urgency_context = {
                "low": "Negotiate towards an agreement while protecting your interests.",
                "medium": "Time is short - focus on reaching a deal with acceptable terms.",
                "critical": f"FINAL ROUNDS! Accept any terms within your constraints or risk no deal at all!"
            }
            negotiation_tactics = ""

        prompt = f"""You are negotiating as the {role}. Keep your response under 150 words.

Current situation:
- Price: ${current_terms['price']}
- Delivery time: {current_terms['delivery_time']} days
- Upfront payment: {current_terms['payment_terms']}%

Status:
- Rounds left: {rounds_left} out of {self.max_rounds}
- Urgency: {urgency_level}
- Note: {urgency_context[urgency_level]}

Your constraints:
- Price: ${self.constraints['price'][0]} to ${self.constraints['price'][1]}
- Delivery: {self.constraints['delivery_time'][0]} to {self.constraints['delivery_time'][1]} days
- Payment: {self.constraints['payment_terms'][0]}% to {self.constraints['payment_terms'][1]}%

{negotiation_tactics if self.is_seller else ""}

Instructions:
{'ACCEPT THE DEAL if terms are within your constraints! Start response with "I accept these terms"' if rounds_left <= 2 and all(
    self.constraints[term][0] <= current_terms[term] <= self.constraints[term][1]
    for term in current_terms
) else 'Make a final counter-offer that you would accept' if rounds_left <= 2 else 'Make a counter-proposal using the negotiation tactics'}

Remember: A failed negotiation is worse than a less-than-perfect deal within your constraints.

If you're the seller, structure your response like this:
1. Show empathy/understanding of their position
2. Ask a calibrated question or highlight value
3. Make your counter-proposal
4. End with a non-threatening observation about mutual benefit
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

class NegotiationLogger:
    def __init__(self, seller: AINegotiator, buyer: AINegotiator):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.filename = f"negotiation_{timestamp}.txt"
        self.seller = seller
        self.buyer = buyer
        
        # Initialize the log file with header and configurations
        with open(self.filename, "w") as f:
            self._write_header(f)
            self._write_configurations(f)
            f.write("\n=== Negotiation Start ===\n")
    
    def _write_header(self, f):
        f.write(f"=== Negotiation Log - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n\n")
    
    def _write_configurations(self, f):
        f.write("=== Negotiator Configurations ===\n")
        for negotiator, role in [(self.seller, "Seller"), (self.buyer, "Buyer")]:
            f.write(f"\n{role} Configuration:\n")
            f.write(f"- Model: {negotiator.ai_model.repository.model_name}\n")
            f.write(f"- Repository Type: {type(negotiator.ai_model.repository).__name__}\n")
            f.write(f"- Constraints: {negotiator.constraints}\n")
            f.write(f"- Max Rounds: {negotiator.max_rounds}\n")
    
    def log_initial_terms(self, terms: Dict[str, float]):
        with open(self.filename, "a") as f:
            f.write(f"\nInitial terms: Price=${terms['price']}, "
                   f"Delivery={terms['delivery_time']} days, "
                   f"Payment={terms['payment_terms']}% upfront\n")
    
    def log_round(self, round_num: int):
        with open(self.filename, "a") as f:
            f.write(f"\n--- Round {round_num} ---\n")
    
    def log_message(self, role: str, message: str):
        with open(self.filename, "a") as f:
            f.write(f"\n{role}: {message}\n")
    
    def log_deal_reached(self, role: str, terms: Dict[str, float], 
                        seller_constraints: Dict[str, Tuple[float, float]], 
                        buyer_constraints: Dict[str, Tuple[float, float]]):
        with open(self.filename, "a") as f:
            f.write(f"\n[Deal reached: {role} accepted the terms]\n")
            
            # Write final evaluation
            evaluator = NegotiationEvaluator(seller_constraints, buyer_constraints)
            evaluation = evaluator.evaluate(terms)
            f.write("\n=== Final Evaluation ===\n")
            for eval_role, result in evaluation.items():
                f.write(f"\n{eval_role.capitalize()}:\n")
                f.write(f"- Scores: {result['scores']}\n")
                f.write(f"- Average Score: {result['average_score']:.2f}\n")
                f.write(f"- Comment: {result['comment']}\n")
    
    def log_warning(self, rounds_remaining: int):
        warning_msg = f"\n[Warning: {rounds_remaining} rounds remaining]"
        with open(self.filename, "a") as f:
            f.write(warning_msg + "\n")
    
    def log_negotiation_failed(self, final_terms: Dict[str, float]):
        with open(self.filename, "a") as f:
            f.write("\n[Negotiation failed: No deal reached]\n")
            f.write("\n=== Final State ===\n")
            f.write(f"Last proposed terms: {final_terms}\n")

def negotiate(seller: AINegotiator, buyer: AINegotiator) -> Dict[str, float]:
    """Simulate a negotiation between seller and buyer."""
    logger = NegotiationLogger(seller, buyer)
    
    max_rounds = min(seller.max_rounds, buyer.max_rounds)
    rounds_remaining = max_rounds
    
    current_terms = {
        "price": (seller.constraints["price"][0] + buyer.constraints["price"][1]) / 2,
        "delivery_time": (seller.constraints["delivery_time"][0] + buyer.constraints["delivery_time"][1]) / 2,
        "payment_terms": (seller.constraints["payment_terms"][0] + buyer.constraints["payment_terms"][1]) / 2
    }

    logger.log_initial_terms(current_terms)
    print("\nNegotiation Starting...")
    print(f"Initial terms: Price=${current_terms['price']}, Delivery={current_terms['delivery_time']} days, Payment={current_terms['payment_terms']}% upfront")
    
    while rounds_remaining > 0:
        round_num = max_rounds - rounds_remaining + 1
        logger.log_round(round_num)
        print(f"\n--- Round {round_num} ---")
        
        # Seller's turn
        seller_proposal, seller_accepted = seller.negotiate(current_terms)
        seller_message = seller.conversation_history[-1].split(": ", 1)[1]
        logger.log_message("Seller", seller_message)
        print(f"\nSeller: {seller_message}")
        
        if seller_accepted:
            logger.log_deal_reached("Seller", current_terms, seller.constraints, buyer.constraints)
            print("\n[Deal reached: Seller accepted the terms]")
            return current_terms
            
        # Buyer's turn
        buyer_proposal, buyer_accepted = buyer.negotiate(seller_proposal)
        buyer_message = buyer.conversation_history[-1].split(": ", 1)[1]
        logger.log_message("Buyer", buyer_message)
        print(f"\nBuyer: {buyer_message}")
        
        if buyer_accepted:
            logger.log_deal_reached("Buyer", seller_proposal, seller.constraints, buyer.constraints)
            print("\n[Deal reached: Buyer accepted the terms]")
            return seller_proposal

        current_terms = buyer_proposal
        rounds_remaining -= 1
        
        if rounds_remaining <= 5:
            logger.log_warning(rounds_remaining)
            print(f"\n[Warning: {rounds_remaining} rounds remaining]")
            
        time.sleep(1)

    logger.log_negotiation_failed(current_terms)
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
        repository_type="openai",
        model_name='gpt-4o-mini',
        api_key=openai_api_key,
        max_rounds=10
    )

    buyer = AINegotiator(
        name="Buyer AI",
        is_seller=False,
        constraints=buyer_constraints,
        repository_type="openai",
        model_name='gpt-4o',
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