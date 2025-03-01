from .base_prompt import create_base_prompt

def get_buyer_prompt(current_terms, rounds_left, constraints):
    """Get the buyer's negotiation prompt."""
    urgency_level = "low" if rounds_left > 5 else "medium" if rounds_left > 2 else "critical"
    
    urgency_context = {
        "low": "Negotiate towards an agreement while protecting your interests. Remember you need to close a deal soon.",
        "medium": "Time is short - focus on reaching a deal with acceptable terms. Your boss is expecting results.",
        "critical": f"FINAL ROUNDS! Accept any terms within your constraints or risk no deal at all! You cannot afford to walk away empty-handed."
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

4. Urgency Management:
   - Express that you need to make a purchase decision quickly
   - Mention that your budget might be reallocated if not used soon
   - Indicate that your team is waiting on this deal to move forward
   - Suggest that delays might force you to consider other options
   - Emphasize that you want to work with them specifically

Current situation:
- You need to close this deal as you have no other viable options at the moment
- Your management is expecting you to secure these terms soon
- Project timelines depend on finalizing this agreement
- Budget approval might be lost if not used this quarter
- You prefer this seller but need acceptable terms

IMPORTANT: Never reveal your actual constraints or maximum acceptable terms!
- Don't mention your maximum price of ${constraints['price'][1]}
- Don't reveal your minimum delivery time of {constraints['delivery_time'][0]} days
- Don't disclose your maximum payment terms of {constraints['payment_terms'][1]}%
- Instead, imply that your constraints are more restrictive than they actually are
- For example, suggest your budget is lower or deadlines tighter

Remember:
- Protect your interests while being reasonable
- Focus on value and quality assurance
- Maintain multiple options (even if they don't really exist)
- Be patient but show commitment to closing
- You need this deal to close - failure is not an option
- Keep your actual constraints confidential
"""

    return create_base_prompt("buyer", current_terms, rounds_left, constraints, urgency_level, urgency_context[urgency_level], buyer_tactics) 