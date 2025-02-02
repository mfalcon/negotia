from .base_prompt import create_base_prompt

def get_buyer_prompt(current_terms, rounds_left, constraints):
    """Get the buyer's negotiation prompt."""
    urgency_level = "low" if rounds_left > 5 else "medium" if rounds_left > 2 else "critical"
    
    urgency_context = {
        "low": "Negotiate towards an agreement while protecting your interests.",
        "medium": "Time is short - focus on reaching a deal with acceptable terms.",
        "critical": f"FINAL ROUNDS! Accept any terms within your constraints or risk no deal at all!"
    }

    buyer_tactics = f"""
Key negotiation tactics for buyer:

1. Value Assessment:
   - Focus on total cost of ownership
   - Highlight market comparisons when favorable
   - Emphasize budget constraints and ROI requirements
   - Question any premium pricing

2. Relationship Building:
   - Show understanding of seller's position
   - Maintain professional and collaborative tone
   - Build long-term partnership potential
   - Express genuine interest in quality and service

3. Strategic Approaches:
   - Start with lower anchor points
   - Request justification for prices above market
   - Suggest volume commitments for better terms
   - Keep alternative options visible

Remember:
- Protect your interests while being reasonable
- Focus on value and quality assurance
- Maintain multiple options
- Be patient but show commitment to closing
"""

    return create_base_prompt("buyer", current_terms, rounds_left, constraints, urgency_level, urgency_context[urgency_level], buyer_tactics) 