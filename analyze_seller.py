import sys
import os
import re
import json
import openai
from typing import Dict, List, Any
from datetime import datetime

def analyze_seller_negotiation(filename: str, api_key: str = None):
    """
    Analyze the seller's negotiation techniques from a negotiation log file using an LLM.
    
    Args:
        filename: Path to the negotiation log file
        api_key: OpenAI API key (optional, will use environment variable if not provided)
    """
    if not os.path.exists(filename):
        print(f"Error: File {filename} not found.")
        return
    
    # Set up OpenAI client
    if api_key:
        client = openai.OpenAI(api_key=api_key)
    else:
        client = openai.OpenAI()  # Uses OPENAI_API_KEY environment variable
    
    with open(filename, 'r') as f:
        content = f.read()
    
    # Extract seller messages
    seller_messages = re.findall(r'Seller: (.*?)(?=\n\n|\n\[|\Z)', content, re.DOTALL)
    
    # Check if deal was reached
    deal_reached = "Deal reached" in content
    deal_acceptor = re.search(r'\[Deal reached: (.*?) accepted', content)
    deal_acceptor = deal_acceptor.group(1) if deal_acceptor else "None"
    
    # Extract final terms
    final_terms = extract_final_terms(content)
    
    # Prepare the prompt for the LLM
    system_prompt = """
    You are an expert negotiation analyst specializing in evaluating seller negotiation techniques.
    Analyze the provided negotiation messages from a seller and evaluate their negotiation skills.
    Focus on identifying negotiation techniques such as:
    
    1. Anchoring
    2. Creating scarcity
    3. Leveraging competition
    4. Creating urgency
    5. Value framing
    6. Emotional labeling
    7. Using calibrated questions
    8. Concession management
    9. Constraint handling (without revealing actual constraints)
    10. Showing empathy
    11. Using loss aversion
    12. Reciprocity
    
    Also identify any weaknesses such as:
    1. Revealing actual constraints
    2. Showing desperation
    3. Making concessions without getting anything in return
    4. Focusing on price rather than value
    5. Lacking empathy
    
    Provide your analysis in JSON format with the following structure:
    {
        "techniques_used": [{"technique": "name", "count": number, "example": "example text"}],
        "strengths": ["description"],
        "weaknesses": ["description"],
        "effectiveness_score": number (0-100),
        "overall_assessment": "text",
        "improvement_suggestions": ["suggestion"]
    }
    """
    
    user_prompt = f"""
    Here are the messages from a seller in a negotiation:
    
    {json.dumps(seller_messages)}
    
    Analyze these messages and evaluate the seller's negotiation techniques.
    """
    
    # Call the LLM for analysis
    response = client.chat.completions.create(
        model="gpt-4o",  # Use an appropriate model
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format={"type": "json_object"}
    )
    
    # Parse the response
    try:
        analysis = json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        print("Error: Could not parse LLM response as JSON.")
        print(response.choices[0].message.content)
        return
    
    # Generate report text
    report = []
    report.append("===== SELLER NEGOTIATION ANALYSIS =====")
    report.append(f"File analyzed: {filename}")
    report.append(f"Number of messages: {len(seller_messages)}")
    report.append(f"Deal reached: {deal_reached}")
    if deal_reached:
        report.append(f"Deal accepted by: {deal_acceptor}")
        report.append(f"Final terms: {final_terms}")
    
    report.append("\n--- NEGOTIATION TECHNIQUES USED ---")
    for technique in analysis.get("techniques_used", []):
        report.append(f"- {technique['technique']}: {technique['count']} instances")
        report.append(f"  Example: \"{technique['example']}\"")
    
    report.append("\n--- STRENGTHS ---")
    for strength in analysis.get("strengths", []):
        report.append(f"✓ {strength}")
    
    report.append("\n--- WEAKNESSES ---")
    for weakness in analysis.get("weaknesses", []):
        report.append(f"✗ {weakness}")
    
    report.append("\n--- OVERALL ASSESSMENT ---")
    report.append(f"Effectiveness score: {analysis.get('effectiveness_score', 0)}/100")
    report.append(analysis.get("overall_assessment", "No assessment provided."))
    
    report.append("\n--- IMPROVEMENT SUGGESTIONS ---")
    for suggestion in analysis.get("improvement_suggestions", []):
        report.append(f"- {suggestion}")
    
    # Print the report to console
    print("\n".join(report))
    
    # Save the report to a file in the data directory
    os.makedirs("data", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_filename = os.path.basename(filename)
    base_name = os.path.splitext(base_filename)[0]
    output_filename = f"data/seller_analysis_{base_name}_{timestamp}.txt"
    
    with open(output_filename, 'w') as f:
        f.write("\n".join(report))
    
    print(f"\nAnalysis saved to: {output_filename}")

def extract_final_terms(content: str) -> Dict[str, float]:
    """Extract the final terms from the negotiation log."""
    # Look for the Final Terms section in a more robust way
    final_terms_match = re.search(r"Final Terms: \{([^}]+)\}", content)
    
    if final_terms_match:
        # Extract the dictionary-like string
        terms_str = final_terms_match.group(1)
        
        # Parse the terms
        terms_dict = {}
        
        # Extract price
        price_match = re.search(r"'price': ([0-9.]+)", terms_str)
        if price_match:
            terms_dict['price'] = float(price_match.group(1))
        
        # Extract delivery time
        delivery_match = re.search(r"'delivery_time': ([0-9.]+)", terms_str)
        if delivery_match:
            terms_dict['delivery_time'] = float(delivery_match.group(1))
        
        # Extract payment terms
        payment_match = re.search(r"'payment_terms': ([0-9.]+)", terms_str)
        if payment_match:
            terms_dict['payment_terms'] = float(payment_match.group(1))
        
        return terms_dict
    
    # Try alternative format
    alt_match = re.search(r"\[Deal reached:.*?\]\s*\n\s*Final Terms:\s*Price=\$([0-9.]+),\s*Delivery=([0-9.]+)\s*days,\s*Payment=([0-9.]+)%", content, re.DOTALL)
    if alt_match:
        return {
            'price': float(alt_match.group(1)),
            'delivery_time': float(alt_match.group(2)),
            'payment_terms': float(alt_match.group(3))
        }
    
    # If no final terms found, return empty dict
    return {}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_seller.py <negotiation_log_file> [openai_api_key]")
        sys.exit(1)
    
    api_key = sys.argv[2] if len(sys.argv) > 2 else None
    analyze_seller_negotiation(sys.argv[1], api_key) 