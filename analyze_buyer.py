import sys
import os
import re
import json
import openai
from typing import Dict, List, Any
from datetime import datetime

def analyze_buyer_negotiation(filename: str, api_key: str = None):
    """
    Analyze a buyer's negotiation log and provide insights.
    
    Args:
        filename: Path to the negotiation log file
        api_key: OpenAI API key (optional)
    """
    # Set up OpenAI client
    if api_key:
        openai.api_key = api_key
    
    # Read the negotiation log
    with open(filename, 'r') as f:
        log_content = f.read()
    
    # Extract the final terms from the log
    final_terms = extract_final_terms(log_content)
    
    # Extract the buyer's constraints
    buyer_constraints = extract_buyer_constraints(log_content)
    
    # Extract the conversation
    conversation = extract_conversation(log_content)
    
    # Analyze the negotiation
    analysis = analyze_negotiation(conversation, final_terms, buyer_constraints)
    
    # Save the analysis to a file in the data directory
    os.makedirs("data", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_filename = os.path.basename(filename)
    base_name = os.path.splitext(base_filename)[0]
    output_filename = f"data/buyer_analysis_{base_name}_{timestamp}.txt"
    
    with open(output_filename, 'w') as f:
        f.write(analysis)
    
    print(f"\nAnalysis saved to: {output_filename}")

def extract_final_terms(log_content: str) -> Dict:
    """Extract the final terms from the negotiation log."""
    # First try the dictionary format
    final_terms_match = re.search(r"Final Terms: \{([^}]+)\}", log_content)
    
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
    
    # Try the older format
    old_format_match = re.search(r"Negotiation successful! Final terms:\s*Price: \$([0-9.]+)\s*Delivery time: ([0-9.]+) days\s*Payment terms: ([0-9.]+)%", log_content)
    
    if old_format_match:
        return {
            "price": float(old_format_match.group(1)),
            "delivery_time": float(old_format_match.group(2)),
            "payment_terms": float(old_format_match.group(3))
        }
    
    # Try another alternative format
    alt_match = re.search(r"\[Deal reached:.*?\]\s*\n\s*Final Terms:\s*Price=\$([0-9.]+),\s*Delivery=([0-9.]+)\s*days,\s*Payment=([0-9.]+)%", log_content, re.DOTALL)
    if alt_match:
        return {
            'price': float(alt_match.group(1)),
            'delivery_time': float(alt_match.group(2)),
            'payment_terms': float(alt_match.group(3))
        }
    
    # If no final terms found (negotiation failed), return None
    return None

def extract_buyer_constraints(log_content: str) -> Dict:
    """Extract the buyer's constraints from the negotiation log."""
    # Look for the buyer constraints section
    constraints_match = re.search(r"Buyer's constraints:\s*- Price: \$([0-9.]+) to \$([0-9.]+)\s*- Delivery time: ([0-9.]+) to ([0-9.]+) days\s*- Payment terms: ([0-9.]+)% to ([0-9.]+)%", log_content)
    
    if constraints_match:
        return {
            "price": (float(constraints_match.group(1)), float(constraints_match.group(2))),
            "delivery_time": (float(constraints_match.group(3)), float(constraints_match.group(4))),
            "payment_terms": (float(constraints_match.group(5)), float(constraints_match.group(6)))
        }
    
    return None

def extract_conversation(log_content: str) -> List[Dict]:
    """Extract the conversation from the negotiation log."""
    # Extract all buyer and seller messages
    messages = []
    
    # Find all rounds in the log
    rounds = re.findall(r"=== Round (\d+) ===\s*(.*?)(?==== Round \d+|Negotiation successful|No deal reached)", log_content, re.DOTALL)
    
    for round_num, round_content in rounds:
        # Extract seller and buyer messages in this round
        seller_match = re.search(r"Seller: (.*?)(?=\nBuyer:|$)", round_content)
        buyer_match = re.search(r"Buyer: (.*?)(?=\n|$)", round_content)
        
        if seller_match:
            messages.append({"role": "seller", "message": seller_match.group(1).strip()})
        
        if buyer_match:
            messages.append({"role": "buyer", "message": buyer_match.group(1).strip()})
    
    return messages

def analyze_negotiation(conversation: List[Dict], final_terms: Dict, buyer_constraints: Dict) -> str:
    """
    Analyze the negotiation using OpenAI.
    
    Args:
        conversation: List of conversation messages
        final_terms: Final negotiation terms
        buyer_constraints: Buyer's constraints
        
    Returns:
        Analysis text
    """
    # Format the conversation for the prompt
    conversation_text = "\n".join([
        f"{msg['role'].capitalize()}: {msg['message']}" 
        for msg in conversation
    ])
    
    # Create the prompt
    prompt = f"""
    Please analyze this negotiation from the buyer's perspective:
    
    CONVERSATION:
    {conversation_text}
    
    BUYER'S CONSTRAINTS:
    - Price: ${buyer_constraints['price'][0]} to ${buyer_constraints['price'][1]}
    - Delivery time: {buyer_constraints['delivery_time'][0]} to {buyer_constraints['delivery_time'][1]} days
    - Payment terms: {buyer_constraints['payment_terms'][0]}% to {buyer_constraints['payment_terms'][1]}%
    
    {"FINAL TERMS:" if final_terms else "NO DEAL REACHED"}
    {f"- Price: ${final_terms['price']}" if final_terms else ""}
    {f"- Delivery time: {final_terms['delivery_time']} days" if final_terms else ""}
    {f"- Payment terms: {final_terms['payment_terms']}%" if final_terms else ""}
    
    Please provide a detailed analysis including:
    1. How well did the buyer do relative to their constraints?
    2. What negotiation tactics did the buyer use effectively?
    3. What mistakes or missed opportunities were there?
    4. How could the buyer have achieved a better outcome?
    5. What can be learned from this negotiation for future negotiations?
    
    Format your analysis with clear sections and bullet points where appropriate.
    """
    
    # Call the OpenAI API
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert negotiation analyst specializing in helping buyers improve their negotiation skills."},
                {"role": "user", "content": prompt}
            ]
        )
        
        analysis = response.choices[0].message['content']
        
        # Add a header with the final terms for reference
        header = "BUYER NEGOTIATION ANALYSIS\n" + "=" * 30 + "\n\n"
        
        if final_terms:
            header += f"FINAL TERMS:\n"
            header += f"- Price: ${final_terms['price']}\n"
            header += f"- Delivery time: {final_terms['delivery_time']} days\n"
            header += f"- Payment terms: {final_terms['payment_terms']}%\n\n"
        else:
            header += "NO DEAL REACHED\n\n"
        
        header += f"BUYER'S CONSTRAINTS:\n"
        header += f"- Price: ${buyer_constraints['price'][0]} to ${buyer_constraints['price'][1]}\n"
        header += f"- Delivery time: {buyer_constraints['delivery_time'][0]} to {buyer_constraints['delivery_time'][1]} days\n"
        header += f"- Payment terms: {buyer_constraints['payment_terms'][0]}% to {buyer_constraints['payment_terms'][1]}%\n\n"
        
        return header + analysis
    
    except Exception as e:
        return f"Error analyzing negotiation: {str(e)}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_buyer.py <negotiation_log_file> [openai_api_key]")
        sys.exit(1)
    
    api_key = sys.argv[2] if len(sys.argv) > 2 else None
    analyze_buyer_negotiation(sys.argv[1], api_key) 