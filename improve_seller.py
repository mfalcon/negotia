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

def analyze_negotiation_with_llm(negotiation_data: Dict[str, Any]) -> Dict[str, Any]:
    """Use LLM to analyze the negotiation and suggest improvements."""
    client = openai.OpenAI()
    
    # Prepare the prompt
    system_prompt = """
    You are an expert negotiation coach specializing in helping sellers improve their negotiation skills.
    Analyze the provided negotiation data and suggest specific improvements for the seller's template.
    
    Focus on:
    1. Identifying effective techniques that worked well
    2. Spotting missed opportunities or weaknesses
    3. Suggesting specific template improvements
    4. Providing new tactics or phrases that could be more effective
    
    Your analysis should be detailed, actionable, and focused on improving the seller's performance in future negotiations.
    """
    
    # Use double curly braces to escape them in f-strings
    user_prompt = f"""
    Here is the data from a recent negotiation:
    
    Seller Messages:
    {json.dumps(negotiation_data["seller_messages"], indent=2)}
    
    Buyer Messages:
    {json.dumps(negotiation_data["buyer_messages"], indent=2)}
    
    Final Terms: {negotiation_data["final_terms"]}
    Deal Reached: {negotiation_data["deal_reached"]}
    Deal Acceptor: {negotiation_data["deal_acceptor"]}
    
    Seller Score: {negotiation_data["seller_score"]}
    Buyer Score: {negotiation_data["buyer_score"]}
    
    Seller Constraints: {negotiation_data["seller_constraints"]}
    Buyer Constraints: {negotiation_data["buyer_constraints"]}
    
    Please analyze this negotiation and provide:
    1. A summary of what worked well for the seller
    2. Identification of missed opportunities or weaknesses
    3. 3-5 specific template improvements (exact phrases or tactics to add)
    4. 2-3 new effective phrases the seller could use
    5. Overall strategy recommendations
    
    Format your response as JSON with these keys:
    {{
        "strengths": ["list of what worked well"],
        "weaknesses": ["list of weaknesses"],
        "template_improvements": ["specific template changes"],
        "new_phrases": ["new effective phrases"],
        "strategy_recommendations": ["overall strategy recommendations"]
    }}
    """
    
    # Call the LLM
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format={"type": "json_object"}
    )
    
    # Parse the response
    try:
        analysis = json.loads(response.choices[0].message.content)
        return analysis
    except json.JSONDecodeError:
        print("Error: Could not parse LLM response as JSON.")
        print(response.choices[0].message.content)
        return {
            "strengths": [],
            "weaknesses": [],
            "template_improvements": [],
            "new_phrases": [],
            "strategy_recommendations": []
        }

def update_seller_template(analysis: Dict[str, Any]) -> bool:
    """Update the seller tactics template with the analysis insights."""
    template_path = "templates/seller/tactics.jinja2"
    
    # Create a backup of the current template
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"templates/seller/tactics_{timestamp}.jinja2.bak"
    
    try:
        shutil.copy2(template_path, backup_path)
        print(f"Created backup of seller template at {backup_path}")
        
        with open(template_path, 'r') as f:
            current_template = f.read()
        
        # Add new phrases to the Strategic Phrases section
        if analysis["new_phrases"]:
            strategic_phrases_section = re.search(r"4\. Strategic Phrases to Use:(.*?)5\.", current_template, re.DOTALL)
            if strategic_phrases_section:
                current_phrases = strategic_phrases_section.group(1)
                new_phrases_text = current_phrases
                
                for phrase in analysis["new_phrases"]:
                    if phrase not in current_phrases:
                        new_phrases_text += f"   - \"{phrase}\"\n"
                
                current_template = current_template.replace(current_phrases, new_phrases_text)
        
        # Add template improvements to the top of the template
        if analysis["template_improvements"]:
            improvements_text = "\n{% if analysis_suggestions %}\nBased on previous negotiation analysis:\n{% for suggestion in analysis_suggestions %}\n- {{ suggestion }}\n{% endfor %}\n{% endif %}\n\n"
            
            # Add a new section for the latest improvements
            improvements_text += "Latest negotiation insights:\n"
            for improvement in analysis["template_improvements"]:
                improvements_text += f"- {improvement}\n"
            
            # Find the right position to insert the improvements
            urgency_section_match = re.search(r"5\. Urgency Creation:(.*?)Current situation analysis:", current_template, re.DOTALL)
            if urgency_section_match:
                insert_position = urgency_section_match.end(1)
                current_template = current_template[:insert_position] + improvements_text + current_template[insert_position:]
        
        # Write the updated template
        with open(template_path, 'w') as f:
            f.write(current_template)
        
        print(f"Updated seller template with new insights")
        return True
    
    except Exception as e:
        print(f"Error updating seller template: {e}")
        return False

def save_analysis_report(negotiation_data: Dict[str, Any], analysis: Dict[str, Any]) -> str:
    """Save the analysis report to a file."""
    os.makedirs("data/analysis", exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_filename = os.path.basename(negotiation_data["file_path"])
    base_name = os.path.splitext(base_filename)[0]
    output_filename = f"data/analysis/improvement_{base_name}_{timestamp}.txt"
    
    report = []
    report.append("=== NEGOTIATION IMPROVEMENT ANALYSIS ===")
    report.append(f"File analyzed: {negotiation_data['file_path']}")
    report.append(f"Analysis date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"Deal reached: {negotiation_data['deal_reached']}")
    if negotiation_data['deal_reached']:
        report.append(f"Deal acceptor: {negotiation_data['deal_acceptor']}")
        report.append(f"Final terms: {negotiation_data['final_terms']}")
    
    report.append(f"Seller score: {negotiation_data['seller_score']}")
    report.append(f"Buyer score: {negotiation_data['buyer_score']}")
    
    report.append("\n=== STRENGTHS ===")
    for strength in analysis.get("strengths", []):
        report.append(f"✓ {strength}")
    
    report.append("\n=== WEAKNESSES ===")
    for weakness in analysis.get("weaknesses", []):
        report.append(f"✗ {weakness}")
    
    report.append("\n=== TEMPLATE IMPROVEMENTS ===")
    for improvement in analysis.get("template_improvements", []):
        report.append(f"• {improvement}")
    
    report.append("\n=== NEW EFFECTIVE PHRASES ===")
    for phrase in analysis.get("new_phrases", []):
        report.append(f"• \"{phrase}\"")
    
    report.append("\n=== STRATEGY RECOMMENDATIONS ===")
    for recommendation in analysis.get("strategy_recommendations", []):
        report.append(f"• {recommendation}")
    
    with open(output_filename, 'w') as f:
        f.write("\n".join(report))
    
    print(f"Analysis report saved to {output_filename}")
    return output_filename

def main():
    """Main function to analyze negotiation and update seller template."""
    print("=== Negotiation Performance Analyzer and Prompt Updater ===")
    
    # Get the latest negotiation file
    latest_file = get_latest_negotiation_file()
    if not latest_file:
        print("No negotiation files found. Exiting.")
        return
    
    print(f"Analyzing latest negotiation: {latest_file}")
    
    # Extract data from the negotiation file
    negotiation_data = extract_negotiation_data(latest_file)
    
    # Analyze the negotiation with LLM
    print("Analyzing negotiation with AI...")
    analysis = analyze_negotiation_with_llm(negotiation_data)
    
    # Save the analysis report
    report_file = save_analysis_report(negotiation_data, analysis)
    
    # Update the seller template
    print("Updating seller template...")
    success = update_seller_template(analysis)
    
    if success:
        print("\n=== Summary ===")
        print(f"✓ Analyzed negotiation: {latest_file}")
        print(f"✓ Generated analysis report: {report_file}")
        print(f"✓ Updated seller template with improvements")
        print("\nKey improvements:")
        for i, improvement in enumerate(analysis.get("template_improvements", [])[:3], 1):
            print(f"{i}. {improvement}")
    else:
        print("\n❌ Failed to update seller template")

if __name__ == "__main__":
    main() 