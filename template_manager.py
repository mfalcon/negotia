import os
import re
from typing import Dict, Any, List, Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape

class TemplateManager:
    def __init__(self, templates_dir: str = "templates"):
        self.env = Environment(
            loader=FileSystemLoader(templates_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )
    
    def render_seller_prompt(self, 
                            current_terms: Dict[str, float], 
                            rounds_left: int, 
                            constraints: Dict[str, Any], 
                            current_price_gap: float,
                            conversation_history: str = "",
                            analysis_file: Optional[str] = None) -> str:
        """
        Render the seller prompt template with the given parameters.
        
        Args:
            current_terms: Current negotiation terms
            rounds_left: Number of rounds left
            constraints: Seller's constraints
            current_price_gap: Current price gap percentage
            conversation_history: Formatted conversation history
            analysis_file: Path to a seller analysis file to extract suggestions from
        """
        # Determine urgency level
        urgency_level = "medium" if rounds_left > 5 else "critical"
        
        # Urgency context based on level
        urgency_notes = {
            "low": "Use tactical empathy while anchoring high. Create scarcity and competition pressure.",
            "medium": "Leverage time pressure and competition. Focus on value and what they might lose.",
            "critical": "Use final call tactics to push for closure."
        }
        
        # Extract analysis suggestions if file provided
        analysis_suggestions = []
        if analysis_file and os.path.exists(analysis_file):
            analysis_suggestions = self._extract_analysis_suggestions(analysis_file)
        
        # Check if terms are within constraints
        terms_within_constraints = all(
            constraints[term][0] <= current_terms[term] <= constraints[term][1]
            for term in current_terms if term in constraints
        )
        
        # Render the tactics template first
        tactics_template = self.env.get_template("seller/tactics.jinja2")
        tactics_content = tactics_template.render(
            constraints=constraints,
            current_price_gap=current_price_gap,
            urgency_level=urgency_level,
            analysis_suggestions=analysis_suggestions
        )
        
        # Render the base template with the tactics content
        base_template = self.env.get_template("base.jinja2")
        return base_template.render(
            role="seller",
            current_terms=current_terms,
            rounds_left=rounds_left,
            constraints=constraints,
            urgency_level=urgency_level,
            urgency_note=urgency_notes[urgency_level],
            tactics=tactics_content,
            terms_within_constraints=terms_within_constraints,
            conversation_history=conversation_history
        )
    
    def render_buyer_prompt(self, 
                           current_terms: Dict[str, float], 
                           rounds_left: int, 
                           constraints: Dict[str, Any],
                           conversation_history: str = "") -> str:
        """
        Render the buyer prompt template with the given parameters.
        
        Args:
            current_terms: Current negotiation terms
            rounds_left: Number of rounds left
            constraints: Buyer's constraints
            conversation_history: Formatted conversation history
        """
        # Determine urgency level
        urgency_level = "low" if rounds_left > 5 else "medium" if rounds_left > 2 else "critical"
        
        # Urgency context based on level
        urgency_notes = {
            "low": "Negotiate towards an agreement while protecting your interests. Remember you need to close a deal soon.",
            "medium": "Time is short - focus on reaching a deal with acceptable terms. Your boss is expecting results.",
            "critical": f"FINAL ROUNDS! Accept any terms within your constraints or risk no deal at all! You cannot afford to walk away empty-handed."
        }
        
        # Check if terms are within constraints
        terms_within_constraints = all(
            constraints[term][0] <= current_terms[term] <= constraints[term][1]
            for term in current_terms if term in constraints
        )
        
        # Render the tactics template first
        tactics_template = self.env.get_template("buyer/tactics.jinja2")
        tactics_content = tactics_template.render(
            constraints=constraints
        )
        
        # Render the base template with the tactics content
        base_template = self.env.get_template("base.jinja2")
        return base_template.render(
            role="buyer",
            current_terms=current_terms,
            rounds_left=rounds_left,
            constraints=constraints,
            urgency_level=urgency_level,
            urgency_note=urgency_notes[urgency_level],
            tactics=tactics_content,
            terms_within_constraints=terms_within_constraints,
            conversation_history=conversation_history
        )
    
    def _extract_analysis_suggestions(self, analysis_file: str) -> List[str]:
        """Extract improvement suggestions from a seller analysis file."""
        with open(analysis_file, 'r') as f:
            content = f.read()
        
        # Extract improvement suggestions section
        suggestions_section = re.search(r"--- IMPROVEMENT SUGGESTIONS ---\n(.*?)(?=\n\n|\Z)", 
                                       content, re.DOTALL)
        if not suggestions_section:
            return []
        
        # Extract individual suggestions
        suggestions_text = suggestions_section.group(1)
        suggestions = re.findall(r"- (.*?)(?=\n-|\Z)", suggestions_text, re.DOTALL)
        return [s.strip() for s in suggestions if s.strip()] 