#!/usr/bin/env python3
"""
Script to analyze the latest negotiation and update the seller template
to improve performance in future negotiations.
"""

import os
import re
import glob
import json
import openai
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import shutil
import time
import sys

def get_latest_negotiation_file() -> Optional[str]:
    """Get the path to the most recent negotiation log file."""
    negotiation_files = glob.glob("data/negotiation_*.txt")
    if not negotiation_files:
        print("No negotiation files found in data directory.")
        return None
    
    return max(negotiation_files, key=os.path.getmtime)

def extract_negotiation_data(file_path: str) -> Dict[str, Any]:
    """Extract key data from a negotiation log file using LLM."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Extract seller and buyer messages using simple regex
    seller_messages = re.findall(r'Seller: (.*?)(?=\n\n|\nBuyer:|\n\[|\Z)', content, re.DOTALL)
    buyer_messages = re.findall(r'Buyer: (.*?)(?=\n\n|\nSeller:|\n\[|\Z)', content, re.DOTALL)
    
    # Use LLM to extract structured data from the negotiation log
    client = openai.OpenAI()
    
    system_prompt = """
    You are an AI assistant specialized in extracting structured data from negotiation logs.
    Extract the requested information accurately and return it in JSON format.
    """
    
    user_prompt = f"""
    Extract the following information from this negotiation log:
    1. Final terms (price, delivery_time, payment_terms)
    2. Seller constraints (min and max for price, delivery_time, payment_terms)
    3. Buyer constraints (min and max for price, delivery_time, payment_terms)
    4. Whether a deal was reached
    5. Who accepted the deal (seller or buyer)
    6. Evaluation scores for seller and buyer

    Here's the negotiation log:
    ```
    {content}
    ```

    Return the data in this JSON format:
    {{
        "final_terms": {{
            "price": float,
            "delivery_time": float,
            "payment_terms": float
        }},
        "seller_constraints": {{
            "price": [min_float, max_float],
            "delivery_time": [min_float, max_float],
            "payment_terms": [min_float, max_float]
        }},
        "buyer_constraints": {{
            "price": [min_float, max_float],
            "delivery_time": [min_float, max_float],
            "payment_terms": [min_float, max_float]
        }},
        "deal_reached": boolean,
        "deal_acceptor": "Seller" or "Buyer" or null,
        "seller_score": float,
        "buyer_score": float
    }}
    """
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format={"type": "json_object"}
    )
    
    try:
        extracted_data = json.loads(response.choices[0].message.content)
        
        # Convert seller and buyer constraints to tuples
        for party in ["seller_constraints", "buyer_constraints"]:
            if party in extracted_data:
                for term in ["price", "delivery_time", "payment_terms"]:
                    if term in extracted_data[party]:
                        min_val, max_val = extracted_data[party][term]
                        extracted_data[party][term] = (float(min_val), float(max_val))
        
        # Add the messages and file path to the extracted data
        extracted_data["seller_messages"] = seller_messages
        extracted_data["buyer_messages"] = buyer_messages
        extracted_data["file_path"] = file_path
        
        return extracted_data
    
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error extracting data with LLM: {e}")
        print("Falling back to basic extraction...")
        
        # Fallback to basic extraction
        basic_data = {
            "seller_messages": seller_messages,
            "buyer_messages": buyer_messages,
            "final_terms": {},
            "seller_constraints": {},
            "buyer_constraints": {},
            "deal_reached": "Deal reached" in content,
            "deal_acceptor": None,
            "seller_score": 0,
            "buyer_score": 0,
            "file_path": file_path
        }
        
        # Try to extract deal acceptor
        if basic_data["deal_reached"]:
            acceptor_match = re.search(r'\[Deal reached: (.*?) accepted', content)
            if acceptor_match:
                basic_data["deal_acceptor"] = acceptor_match.group(1)
        
        return basic_data

def analyze_negotiation(negotiation_file):
    """Analyze a negotiation log file using AI to generate improvement suggestions based on Chris Voss's techniques."""
    print(f"Analyzing negotiation with AI...")
    
    # Read the negotiation file
    with open(negotiation_file, 'r') as f:
        negotiation_content = f.read()
    
    # Create a prompt for the AI that incorporates Chris Voss's negotiation principles
    prompt = f"""
    You are an expert negotiation coach trained in the methods of Chris Voss (author of "Never Split the Difference"). 
    Analyze this negotiation transcript and provide SPECIFIC, TACTICAL advice to help the seller WIN future negotiations.
    
    Focus on these Chris Voss techniques:
    1. Tactical Empathy - Understanding the buyer's perspective to gain advantage
    2. Calibrated Questions - Using "how" and "what" questions to guide the buyer
    3. Labeling - Naming emotions to defuse or reinforce them
    4. Mirroring - Repeating the last few words to encourage elaboration
    5. Creating the illusion of control - Making the buyer feel they're in charge
    
    Provide:
    1. 2-3 specific tactical empathy phrases the seller should use
    2. 2-3 calibrated questions to shift leverage to the seller
    3. 2-3 effective labels to manage emotions
    4. 2-3 mirroring techniques for this specific negotiation context
    5. 1-2 "no"-oriented questions that actually lead to "yes"
    
    Format your response as SPECIFIC, ACTIONABLE tactics the seller can immediately implement.
    Each tactic should be a precise phrase or question the seller can use verbatim.
    
    NEGOTIATION TRANSCRIPT:
    {negotiation_content}
    """
    
    # Get OpenAI API key from environment
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if not openai_api_key:
        raise ValueError("Please set OPENAI_API_KEY environment variable")
    
    # Initialize OpenAI client
    client = openai.OpenAI(api_key=openai_api_key)
    
    # Generate analysis
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an expert in Chris Voss's negotiation techniques from 'Never Split the Difference'. Provide specific, tactical advice that will help the seller win negotiations."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=800
    )
    
    analysis = response.choices[0].message.content
    
    # Save the analysis
    os.makedirs('data/analysis', exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    negotiation_id = os.path.basename(negotiation_file).replace('.txt', '')
    analysis_file = f"data/analysis/improvement_{negotiation_id}_{timestamp}.txt"
    
    with open(analysis_file, 'w') as f:
        f.write(analysis)
    
    print(f"Analysis report saved to {analysis_file}")
    return analysis_file, analysis

def update_seller_template(analysis):
    """Update the seller tactics template with Chris Voss-inspired negotiation techniques."""
    print("Updating seller template...")
    
    # Ensure the directory exists
    os.makedirs('templates/seller', exist_ok=True)
    
    # Path to the tactics template
    tactics_file = 'templates/seller/tactics.j2'
    
    try:
        # Create a structured tactics file based on Chris Voss's methods
        with open(tactics_file, 'w') as f:
            f.write("# Seller Tactics: Chris Voss's 'Never Split the Difference' Approach\n\n")
            
            # Tactical Empathy section
            f.write("## Tactical Empathy\n")
            for line in analysis.split("\n"):
                if "empathy" in line.lower() and line.strip().startswith("-") and "\"" in line:
                    f.write(f"{line}\n")
            
            # Calibrated Questions section
            f.write("\n## Calibrated Questions\n")
            for line in analysis.split("\n"):
                if any(term in line.lower() for term in ["question", "how", "what"]) and line.strip().startswith("-") and "?" in line:
                    f.write(f"{line}\n")
            
            # Labeling section
            f.write("\n## Emotional Labeling\n")
            for line in analysis.split("\n"):
                if any(term in line.lower() for term in ["label", "emotion", "feel", "seems"]) and line.strip().startswith("-"):
                    f.write(f"{line}\n")
            
            # Mirroring section
            f.write("\n## Mirroring Techniques\n")
            for line in analysis.split("\n"):
                if any(term in line.lower() for term in ["mirror", "repeat", "echo"]) and line.strip().startswith("-"):
                    f.write(f"{line}\n")
            
            # No-oriented questions
            f.write("\n## Strategic 'No' Questions\n")
            for line in analysis.split("\n"):
                if "no" in line.lower() and line.strip().startswith("-") and "?" in line:
                    f.write(f"{line}\n")
            
            # Add default tactics if sections are empty
            sections = ["Tactical Empathy", "Calibrated Questions", "Emotional Labeling", "Mirroring Techniques", "Strategic 'No' Questions"]
            content = f.tell()
            
            if content < 500:  # If not much content was written, add defaults
                f.seek(0)
                f.write("# Seller Tactics: Chris Voss's 'Never Split the Difference' Approach\n\n")
                
                f.write("## Tactical Empathy\n")
                f.write("- \"It sounds like you're looking for the best value, not just the lowest price.\"\n")
                f.write("- \"I understand that budget constraints are a real challenge you're facing.\"\n")
                
                f.write("\n## Calibrated Questions\n")
                f.write("- \"How would a faster delivery time impact your operations?\"\n")
                f.write("- \"What would need to happen for you to consider a higher upfront payment?\"\n")
                
                f.write("\n## Emotional Labeling\n")
                f.write("- \"It seems like the price point is causing you some frustration.\"\n")
                f.write("- \"It looks like you're concerned about committing to a higher upfront payment.\"\n")
                
                f.write("\n## Mirroring Techniques\n")
                f.write("- When buyer mentions price: \"The price is too high?\"\n")
                f.write("- When buyer pushes on delivery: \"Faster delivery?\"\n")
                
                f.write("\n## Strategic 'No' Questions\n")
                f.write("- \"Would it be a ridiculous idea to consider a slightly longer delivery time in exchange for a better price?\"\n")
                f.write("- \"Is it unreasonable to expect some flexibility on payment terms given the quality we're offering?\"\n")
            
            # Always add the closing tactics
            f.write("\n## Black Swan Tactics\n")
            f.write("- When deadlocked: \"What's the biggest challenge you're facing in this negotiation?\"\n")
            f.write("- For final rounds: \"How can we reach an agreement that you'd be comfortable presenting to your team?\"\n")
            f.write("- Use \"Done deal!\" only when terms meet your minimum requirements\n")
        
        print(f"✅ Seller tactics template updated with Chris Voss techniques: {tactics_file}")
        return True
    except Exception as e:
        print(f"Error updating seller template: {e}")
        return False

def find_latest_negotiation():
    """Find the most recent negotiation log file."""
    negotiation_files = [f for f in os.listdir('data') if f.startswith('negotiation_') and f.endswith('.txt')]
    
    if not negotiation_files:
        print("No negotiation logs found in the data directory.")
        return None
    
    # Sort by creation time (newest first)
    latest_file = max(negotiation_files, key=lambda f: os.path.getctime(os.path.join('data', f)))
    return os.path.join('data', latest_file)

def main():
    print("=== Negotiation Performance Analyzer and Prompt Updater ===")
    
    # Find the latest negotiation log
    latest_negotiation = find_latest_negotiation()
    if not latest_negotiation:
        print("❌ No negotiation logs found to analyze.")
        return
    
    print(f"Analyzing latest negotiation: {latest_negotiation}")
    
    # Analyze the negotiation
    analysis_file, analysis = analyze_negotiation(latest_negotiation)
    
    # Update the seller template
    success = update_seller_template(analysis)
    
    if not success:
        print("\n❌ Failed to update seller template")
    else:
        print("\n✅ Seller template updated successfully!")
        print(f"The next negotiation will use the improved tactics.")

if __name__ == "__main__":
    main() 