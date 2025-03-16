import random
import requests
from typing import Dict, Any, Tuple, List, Optional, Union
import ast
import re
from abc import ABC, abstractmethod
import openai
import time
import os
from datetime import datetime
import json
from template_manager import TemplateManager

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
        # Check for API key before initializing client
        if not (api_key or os.getenv('OPENAI_API_KEY')):
            raise ValueError("OpenAI API key must be provided either through environment variable OPENAI_API_KEY or as a parameter")
        self.client = openai.OpenAI(api_key=api_key or os.getenv('OPENAI_API_KEY'))

    def run(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "user", "content": prompt}
            ],
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

class NegotiationMessage:
    """Class to represent a single message in the negotiation."""
    def __init__(self, role: str, content: str, round_num: int, terms: Optional[Dict[str, float]] = None):
        self.role = role
        self.content = content
        self.round_num = round_num
        self.terms = terms or {}
        self.accepted = False
    
    def __str__(self):
        return f"{self.role}: {self.content}"
    
    def to_dict(self):
        return {
            "role": self.role,
            "content": self.content,
            "round_num": self.round_num,
            "terms": self.terms,
            "accepted": self.accepted
        }

class NegotiationState:
    """Class to manage the state of the negotiation."""
    def __init__(self, initial_terms: Dict[str, float], max_rounds: int):
        self.current_terms = initial_terms.copy()
        self.max_rounds = max_rounds
        self.current_round = 1
        self.messages: List[NegotiationMessage] = []
        self.deal_reached = False
        self.deal_acceptor = None
    
    def add_message(self, role: str, content: str, terms: Optional[Dict[str, float]] = None, accepted: bool = False):
        """Add a message to the negotiation history."""
        message = NegotiationMessage(role, content, self.current_round, terms)
        message.accepted = accepted
        self.messages.append(message)
        
        # Update current terms if new terms were proposed
        if terms:
            self.current_terms.update(terms)
        
        # Update state if deal was accepted
        if accepted:
            self.deal_reached = True
            self.deal_acceptor = role
        
        # Increment round counter after both parties have spoken
        if role == "buyer":
            self.current_round += 1
    
    def get_rounds_left(self) -> int:
        """Get the number of rounds left in the negotiation."""
        return max(0, self.max_rounds - self.current_round + 1)
    
    def get_conversation_history(self) -> str:
        """Get formatted conversation history for prompts."""
        if not self.messages:
            return ""
        
        history = "\n\nPrevious messages:\n"
        
        # Group messages by round
        rounds = {}
        for msg in self.messages:
            if msg.round_num not in rounds:
                rounds[msg.round_num] = {"seller": "", "buyer": ""}
            rounds[msg.round_num][msg.role.lower()] = msg.content
        
        # Format the conversation by rounds
        for round_num in sorted(rounds.keys()):
            history += f"\n--- Round {round_num} ---\n"
            if rounds[round_num]["seller"]:
                history += f"Seller: {rounds[round_num]['seller']}\n"
            if rounds[round_num]["buyer"]:
                history += f"Buyer: {rounds[round_num]['buyer']}\n"
        
        return history
    
    def should_auto_accept(self, role: str, constraints: Dict[str, Tuple[float, float]]) -> bool:
        """Check if the negotiator should automatically accept the current terms."""
        # Auto-accept in final round if terms are acceptable
        if self.get_rounds_left() <= 1:
            return all(
                constraints[term][0] <= self.current_terms[term] <= constraints[term][1]
                for term in self.current_terms
            )
        return False

class AINegotiator:
    def __init__(self, 
                 name: str, 
                 is_seller: bool, 
                 constraints: Dict[str, Tuple[float, float]], 
                 repository_type: str = "ollama",
                 model_name: str = "llama2:latest",
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
        self.max_rounds = max_rounds
        self.role = "seller" if is_seller else "buyer"
        self.last_message = None
        self.template_manager = TemplateManager()
        
        # Find the most recent analysis file for this negotiator type
        self.analysis_file = self._find_latest_analysis_file()
    
    def _find_latest_analysis_file(self) -> Optional[str]:
        """Find the most recent analysis file for this negotiator type."""
        import glob
        import os
        
        # Get all analysis files for this negotiator type
        pattern = f"data/{'seller' if self.is_seller else 'buyer'}_analysis_*.txt"
        files = glob.glob(pattern)
        
        # Return the most recent file if any exist
        if files:
            return max(files, key=os.path.getmtime)
        return None
    
    def extract_terms_with_llm(self, response: str) -> Dict[str, float]:
        """Extract terms from a message using an LLM."""
        try:
            # Create a specific prompt for term extraction
            prompt = f"""
            Extract the negotiation terms (price, delivery time, and payment terms) from this message.
            
            Rules:
            1. Only extract terms that are EXPLICITLY mentioned in the message
            2. Ignore any terms from previous messages that are being referenced
            3. For price, look for dollar amounts (e.g., $1000, 950 dollars)
            4. For delivery time, look for day references (e.g., 10 days, 7.5-day delivery)
            5. For payment terms, look for percentage references (e.g., 50% upfront, 40 percent payment)
            6. Be precise and only extract numbers that are clearly intended as offers
            
            Return ONLY a valid JSON object with this exact structure:
            {{
                "price": [number or null],
                "delivery_time": [number or null],
                "payment_terms": [number or null]
            }}
            
            If a term is not mentioned in the message, use null for that term.
            
            Message: {response}
            
            JSON:
            """
            
            extraction_response = self.ai_model.generate_text(prompt)
            
            # Parse the JSON response
            json_match = re.search(r'\{.*\}', extraction_response, re.DOTALL)
            if not json_match:
                return {}
                
            extracted_json = json_match.group(0)
            extracted_terms = json.loads(extracted_json)
            
            # Convert to proper format
            terms = {}
            if extracted_terms.get("price") is not None:
                terms["price"] = float(extracted_terms["price"])
            if extracted_terms.get("delivery_time") is not None:
                terms["delivery_time"] = float(extracted_terms["delivery_time"])
            if extracted_terms.get("payment_terms") is not None:
                terms["payment_terms"] = float(extracted_terms["payment_terms"])
            
            print(f"LLM extracted terms: {terms}")
            return terms
            
        except Exception as e:
            print(f"Error extracting terms with LLM: {e}")
            return {}
    
    def extract_terms(self, response: str) -> Dict[str, float]:
        """Extract numerical terms from a natural language response."""
        terms = {}
        
        try:
            # First try to extract terms using LLM
            llm_terms = self.extract_terms_with_llm(response)
            if llm_terms:
                return llm_terms
        except Exception as e:
            print(f"Error extracting terms with LLM: {e}")
        
        # Fall back to regex extraction if LLM extraction fails
        try:
            # Price extraction
            price_matches = re.findall(r'\$\s*(\d+(?:,\d+)?(?:\.\d+)?)|(\d+(?:,\d+)?(?:\.\d+)?)\s*dollars', response.lower())
            if price_matches:
                flat_matches = [match for tup in price_matches for match in tup if match]
                if flat_matches:
                    terms["price"] = float(flat_matches[0].replace(',', ''))
            
            # Delivery time extraction
            delivery_matches = re.findall(r'(\d+(?:\.\d+)?)\s*(?:-|\s)?days?|(\d+(?:\.\d+)?)\s*(?:-|\s)?day delivery', response.lower())
            if delivery_matches:
                flat_matches = [match for tup in delivery_matches for match in tup if match]
                if flat_matches:
                    terms["delivery_time"] = float(flat_matches[0])
            
            # Payment terms extraction
            payment_matches = re.findall(r'(\d+(?:\.\d+)?)\s*(?:%|percent|percentage)(?:\s*upfront|\s*payment|\s*deposit)?', response.lower())
            if payment_matches:
                terms["payment_terms"] = float(payment_matches[0])
            
            print(f"Regex extracted terms: {terms}")
        except Exception as e:
            print(f"Error in regex term extraction: {e}")
        
        return terms

    def extract_acceptance(self, response: str) -> bool:
        """
        Extract acceptance from a response.
        Only returns True if the message contains the exact phrase "Done deal!"
        """
        return "Done deal!" in response
    
    def create_negotiation_prompt(self, negotiation_state: NegotiationState) -> str:
        """Create a negotiation prompt using the template manager."""
        # Get conversation history
        conversation_history = negotiation_state.get_conversation_history()
        
        if self.is_seller:
            # Calculate price gap for seller
            target_price = self.constraints['price'][1] * 0.95
            current_price_gap = ((target_price - negotiation_state.current_terms['price']) / target_price) * 100
            
            return self.template_manager.render_seller_prompt(
                current_terms=negotiation_state.current_terms,
                rounds_left=negotiation_state.get_rounds_left(),
                constraints={**self.constraints, 'max_rounds': self.max_rounds},
                current_price_gap=current_price_gap,
                conversation_history=conversation_history,
                analysis_file=self.analysis_file
            )
        else:
            return self.template_manager.render_buyer_prompt(
                current_terms=negotiation_state.current_terms,
                rounds_left=negotiation_state.get_rounds_left(),
                constraints={**self.constraints, 'max_rounds': self.max_rounds},
                conversation_history=conversation_history
            )
    
    def negotiate(self, negotiation_state: NegotiationState) -> Tuple[Dict[str, float], bool]:
        """Generate a negotiation response based on the current state."""
        # Check if we should auto-accept
        if negotiation_state.should_auto_accept(self.role, self.constraints):
            acceptance_message = "Done deal! I accept these terms as they are within my constraints."
            self.last_message = acceptance_message
            return {}, True
        
        # Generate response
        prompt = self.create_negotiation_prompt(negotiation_state)
        response = self.ai_model.generate_text(prompt)
        self.last_message = response
        
        # Check if terms are accepted (explicit "Done deal!" phrase)
        accepted = self.extract_acceptance(response)
        
        # Extract terms from response
        proposed_terms = self.extract_terms(response)
        
        # If accepting, return empty terms dict to use current terms
        if accepted:
            return {}, True
        
        # Ensure proposed terms are within constraints
        for term in negotiation_state.current_terms:
            if term in proposed_terms:
                min_val, max_val = self.constraints[term]
                proposed_terms[term] = max(min_val, min(max_val, proposed_terms[term]))
        
        print(f"Final proposed terms: {proposed_terms}")
        return proposed_terms, accepted

class NegotiationLogger:
    def __init__(self, seller: AINegotiator, buyer: AINegotiator):
        # Create data directory if it doesn't exist
        os.makedirs("data", exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.filename = f"data/negotiation_{timestamp}.txt"
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
            f.write(f"\n=== Round {round_num} ===\n")
    
    def log_message(self, role: str, message: str):
        with open(self.filename, "a") as f:
            f.write(f"\n{role}: {message}\n")
    
    def log_deal_reached(self, acceptor: str, terms: Dict[str, float], seller_constraints: Dict, buyer_constraints: Dict):
        with open(self.filename, "a") as f:
            f.write(f"\n[Deal reached: {acceptor} accepted the terms]\n")
            f.write(f"\nFinal Terms: {terms}\n\n")
            
            # Add evaluation
            evaluator = NegotiationEvaluator(seller_constraints, buyer_constraints)
            evaluation = evaluator.evaluate(terms)
            
            f.write("Negotiation Evaluation:\n")
            for role, result in evaluation.items():
                f.write(f"{role.capitalize()}:\n")
                f.write(f" - Scores: {result['scores']}\n")
                f.write(f" - Average Score: {result['average_score']:.2f}\n")
                f.write(f" - Comment: {result['comment']}\n")
    
    def log_warning(self, rounds_remaining: int):
        warning_msg = f"\n[Warning: {rounds_remaining} rounds remaining]"
        with open(self.filename, "a") as f:
            f.write(warning_msg + "\n")
    
    def log_negotiation_failed(self, final_terms: Dict[str, float]):
        with open(self.filename, "a") as f:
            f.write("\n[Negotiation failed: No deal reached]\n")
            f.write("\n=== Final State ===\n")
            f.write(f"Last proposed terms: {final_terms}\n")

def negotiate(seller: AINegotiator, buyer: AINegotiator, max_rounds: int = 10) -> Dict[str, float]:
    """Simulate a negotiation between seller and buyer with improved state management."""
    logger = NegotiationLogger(seller, buyer)
    
    # Initialize negotiation state
    initial_terms = {
        "price": (seller.constraints["price"][0] + buyer.constraints["price"][1]) / 2,
        "delivery_time": (seller.constraints["delivery_time"][0] + buyer.constraints["delivery_time"][1]) / 2,
        "payment_terms": (seller.constraints["payment_terms"][0] + buyer.constraints["payment_terms"][1]) / 2
    }

    state = NegotiationState(initial_terms, max_rounds)
    
    logger.log_initial_terms(initial_terms)
    print("\nNegotiation Starting...")
    print(f"Initial terms: Price=${initial_terms['price']}, Delivery={initial_terms['delivery_time']} days, Payment={initial_terms['payment_terms']}% upfront")
    
    while state.get_rounds_left() > 0 and not state.deal_reached:
        logger.log_round(state.current_round)
        print(f"\n--- Round {state.current_round} ---")
        
        # Seller's turn
        seller_terms, seller_accepted = seller.negotiate(state)
        logger.log_message("Seller", seller.last_message)
        print(f"\nSeller: {seller.last_message}")
        
        # Update negotiation state with seller's message
        state.add_message("seller", seller.last_message, seller_terms, seller_accepted)
        
        if seller_accepted:
            logger.log_deal_reached("Seller", state.current_terms, seller.constraints, buyer.constraints)
            print("\n[Deal reached: Seller accepted the terms]")
            return state.current_terms
            
        # Buyer's turn
        buyer_terms, buyer_accepted = buyer.negotiate(state)
        logger.log_message("Buyer", buyer.last_message)
        print(f"\nBuyer: {buyer.last_message}")
        
        # Update negotiation state with buyer's message
        state.add_message("buyer", buyer.last_message, buyer_terms, buyer_accepted)
        
        if buyer_accepted:
            logger.log_deal_reached("Buyer", state.current_terms, seller.constraints, buyer.constraints)
            print("\n[Deal reached: Buyer accepted the terms]")
            return state.current_terms
        
        # Warning for low rounds
        if state.get_rounds_left() <= 5:
            logger.log_warning(state.get_rounds_left())
            print(f"\n[Warning: {state.get_rounds_left()} rounds remaining]")
            
        time.sleep(1)

    logger.log_negotiation_failed(state.current_terms)
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
        model_name='gpt-4o',
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
    final_terms = negotiate(seller, buyer, max_rounds=10)
    
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