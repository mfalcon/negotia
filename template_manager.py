import os
from jinja2 import Environment, FileSystemLoader
from typing import Dict, Any, Optional

class TemplateManager:
    """
    Manages Jinja2 templates for the negotiation system.
    Handles loading and rendering templates with proper context.
    """
    
    def __init__(self):
        """Initialize the template manager with the Jinja2 environment."""
        template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        self.env = Environment(loader=FileSystemLoader(template_dir))
        
        # Cache for loaded templates to avoid duplicate loading
        self._template_cache = {}
        
    def _get_template(self, template_path: str):
        """Get a template from cache or load it if not cached."""
        if template_path not in self._template_cache:
            self._template_cache[template_path] = self.env.get_template(template_path)
        return self._template_cache[template_path]
    
    def render_seller_prompt(self, 
                            current_terms: Dict[str, float], 
                            rounds_left: int,
                            constraints: Dict[str, Any],
                            current_price_gap: float,
                            conversation_history: str = "",
                            analysis_file: Optional[str] = None) -> str:
        """
        Render the seller prompt template with the given context.
        
        Args:
            current_terms: Current negotiation terms
            rounds_left: Number of rounds left in the negotiation
            constraints: Seller's constraints
            current_price_gap: Gap between current price and target price
            conversation_history: History of the conversation
            analysis_file: Path to analysis file (optional)
            
        Returns:
            str: The rendered prompt
        """
        # Load the main seller template
        template = self._get_template('seller_prompt.j2')
        
        # Prepare context with all required variables
        context = {
            'current_terms': current_terms,
            'rounds_left': rounds_left,
            'constraints': constraints,
            'current_price_gap': current_price_gap,
            'conversation_history': conversation_history
        }
        
        # Load tactics from the tactics template - explicitly use .j2 extension
        tactics_path = 'seller/tactics.j2'
        try:
            tactics_template = self._get_template(tactics_path)
            tactics_content = tactics_template.render(
                constraints=constraints,
                current_price_gap=current_price_gap,
                rounds_left=rounds_left
            )
            
            # Only include tactics if they're not too verbose (limit to reasonable size)
            if len(tactics_content.split('\n')) <= 25:  # Limit to 25 lines max
                context['tactics'] = tactics_content
                print(f"Successfully loaded tactics from {tactics_path}")
            else:
                # Extract just the most important parts if too verbose
                lines = tactics_content.split('\n')
                # Get headers and first bullet point under each header
                important_lines = []
                for i, line in enumerate(lines):
                    if line.startswith('#') or (i > 0 and lines[i-1].startswith('#') and line.strip().startswith('-')):
                        important_lines.append(line)
                context['tactics'] = '\n'.join(important_lines)
        except Exception as e:
            print(f"Warning: Could not load seller tactics template {tactics_path}: {e}")
            
            # Fall back to analysis file if tactics template fails
            if analysis_file and os.path.exists(analysis_file):
                print(f"Loading tactics from analysis file: {analysis_file}")
                with open(analysis_file, 'r') as f:
                    analysis_content = f.read()
                    # Extract just key points from analysis
                    lines = analysis_content.split('\n')
                    important_lines = [line for line in lines if line.strip().startswith('**') or line.strip().startswith('-')]
                    context['tactics'] = '\n'.join(important_lines[:20])  # Limit to 20 lines
        
        # Render the template with the context
        return template.render(**context)
    
    def render_buyer_prompt(self,
                           current_terms: Dict[str, float],
                           rounds_left: int,
                           constraints: Dict[str, Any],
                           conversation_history: str = "",
                           analysis_file: Optional[str] = None) -> str:
        """
        Render the buyer prompt template with the given context.
        
        Args:
            current_terms: Current negotiation terms
            rounds_left: Number of rounds left in the negotiation
            constraints: Buyer's constraints
            conversation_history: History of the conversation
            analysis_file: Path to analysis file (optional)
            
        Returns:
            str: The rendered prompt
        """
        # Load the main buyer template
        template = self._get_template('buyer_prompt.j2')
        
        # Prepare context with all required variables
        context = {
            'current_terms': current_terms,
            'rounds_left': rounds_left,
            'constraints': constraints,
            'conversation_history': conversation_history
        }
        
        # Load tactics from the tactics template - explicitly use .j2 extension
        tactics_path = 'buyer/tactics.j2'
        try:
            tactics_template = self._get_template(tactics_path)
            tactics_content = tactics_template.render(
                constraints=constraints,
                rounds_left=rounds_left
            )
            
            # Only include tactics if they're not too verbose (limit to reasonable size)
            if len(tactics_content.split('\n')) <= 25:  # Limit to 25 lines max
                context['tactics'] = tactics_content
                print(f"Successfully loaded tactics from {tactics_path}")
            else:
                # Extract just the most important parts if too verbose
                lines = tactics_content.split('\n')
                # Get headers and first bullet point under each header
                important_lines = []
                for i, line in enumerate(lines):
                    if line.startswith('#') or (i > 0 and lines[i-1].startswith('#') and line.strip().startswith('-')):
                        important_lines.append(line)
                context['tactics'] = '\n'.join(important_lines)
        except Exception as e:
            print(f"Warning: Could not load buyer tactics template {tactics_path}: {e}")
            
            # Fall back to analysis file if tactics template fails
            if analysis_file and os.path.exists(analysis_file):
                print(f"Loading tactics from analysis file: {analysis_file}")
                with open(analysis_file, 'r') as f:
                    analysis_content = f.read()
                    # Extract just key points from analysis
                    lines = analysis_content.split('\n')
                    important_lines = [line for line in lines if line.strip().startswith('**') or line.strip().startswith('-')]
                    context['tactics'] = '\n'.join(important_lines[:20])  # Limit to 20 lines
        
        # Render the template with the context
        return template.render(**context) 