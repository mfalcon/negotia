#!/usr/bin/env python3
"""
Script to analyze negotiations and generate expert-level tactics for the seller
based on previous performance, using a two-phase approach:
1. AI Judge - Identifies weaknesses in previous negotiations
2. AI Expert - Generates improved tactics based on the judge's analysis
"""

import os
import re
import glob
import json
import openai
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import sys
import textwrap   # just for the debug snippet (optional)

def get_latest_negotiation_file() -> Optional[str]:
    """Get the path to the most recent negotiation log file."""
    negotiation_files = glob.glob("data/negotiation_*.txt")
    if not negotiation_files:
        print("No negotiation files found in data directory.")
        return None
    
    return max(negotiation_files, key=os.path.getmtime)

def _extract_score(label: str, text: str) -> Optional[float]:
    """
    Return the 'Average Score' that appears anywhere *after* the given label.
    Accepts formats like:
        Joan:
         - Average Score: 8.10
        Elisa: Average Score – 25.8
    Falls back to None if not found.
    """
    # (1)  Try inside an "=== Evaluation === ..." block           ─────────────
    eval_pat = rf"===\s*Evaluation\s*===.*?{label}.*?Average\s+Score\s*[:\-]?\s*" \
               rf"([0-9]+(?:\.[0-9]+)?)"
    m = re.search(eval_pat, text, re.IGNORECASE | re.DOTALL)
    if m:
        return float(m.group(1))

    # (2)  Generic anywhere‑after‑label pattern  (multiline, very tolerant)
    generic_pat = (
        rf"{label}\s*:"
        rf"(?:.*?\n)*?"                        # any chars incl. new‑lines, non‑greedy
        rf"\s*Average\s+Score\s*[:\-]?\s*"     # the keyword we want
        rf"([0-9]+(?:\.[0-9]+)?)"              # capture the number
    )
    m = re.search(generic_pat, text, re.IGNORECASE | re.DOTALL)
    if m:
        return float(m.group(1))

    # (3)  Nothing found – return None (caller will default to 0.0)          ──
    return None

def extract_negotiation_data(file_path: str) -> Dict[str, Any]:
    """Extract comprehensive data from a negotiation log file using an LLM."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Get OpenAI API key
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if not openai_api_key:
        raise ValueError("Please set OPENAI_API_KEY environment variable")
    
    # Initialize OpenAI client
    client = openai.OpenAI(api_key=openai_api_key)
    
    # Create a prompt for the LLM to extract all needed information
    extract_prompt = f"""
    You are a precise data extraction assistant. Extract the following information from this negotiation log:
    
    1. Final terms (price, delivery_time, payment_terms)
    2. Joan's (seller) average score
    3. Elisa's (buyer) average score
    4. Joan's (seller) constraints (min and target values for price, delivery_time, payment_terms)
    5. Elisa's (buyer) constraints (min and target values for price, delivery_time, payment_terms)
    
    Return ONLY a valid JSON object with these keys:
    - final_terms: object with price, delivery_time, payment_terms as numeric values
    - seller_score: numeric value
    - buyer_score: numeric value
    - seller_constraints: object with price, delivery_time, payment_terms as arrays [min, target]
    - buyer_constraints: object with price, delivery_time, payment_terms as arrays [min, target]
    
    NEGOTIATION LOG:
    {content}
    """
    
    try:
        # Ask the LLM to extract the data
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": "You are a data extraction tool that returns only valid JSON."},
                {"role": "user", "content": extract_prompt}
            ],
            # Re-enabled temperature for more deterministic JSON output
            temperature=0.0,
        )
        
        # Get the response content
        extraction_text = response.choices[0].message.content
        
        # Find the JSON object in the response (in case there's any extra text)
        json_match = re.search(r'\{.*\}', extraction_text, re.DOTALL)
        if json_match:
            extracted_data = json.loads(json_match.group(0))
        else:
            # If no JSON found, try parsing the whole response
            extracted_data = json.loads(extraction_text)
        
        # --- Add this for debugging ---
        print(f"🔍 LLM Extracted Data: {extracted_data}") 
        # --- End of debug print ---

        # Extract the conversation part (simple string operations, no regex)
        conversation = ""
        start_marker = "=== Round 1 ==="
        end_marker = "=== Evaluation ==="
        
        start_idx = content.find(start_marker)
        end_idx = content.find(end_marker)
        
        if start_idx != -1:
            if end_idx != -1:
                conversation = content[start_idx:end_idx]
            else:
                conversation = content[start_idx:]
        
        # Create the result dictionary with defaults for missing values
        result = {
            "final_terms": extracted_data.get("final_terms", {}),
            # Reverted to keys LLM was instructed to use in JSON
            "seller_score": float(extracted_data.get("seller_score", 0.0)),
            "buyer_score": float(extracted_data.get("buyer_score", 0.0)),
            "conversation": conversation,
            "seller_constraints": extracted_data.get("seller_constraints", {}),
            "buyer_constraints": extracted_data.get("buyer_constraints", {}),
            "file_path": file_path
        }
        
        # Print extraction success
        print(f"✅ Successfully extracted data using LLM")
        print(f"   Seller score: {result['seller_score']:.2f}, Buyer score: {result['buyer_score']:.2f}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error extracting data with LLM: {e}")
        # Provide default values if extraction fails
        return {
            "final_terms": {},
            "seller_score": 0.0,
            "buyer_score": 0.0,
            "conversation": "",
            "seller_constraints": {'price': (1000.0, 1500.0), 'delivery_time': (7.0, 14.0), 'payment_terms': (30.0, 60.0)},
            "buyer_constraints": {'price': (800.0, 1200.0), 'delivery_time': (5.0, 10.0), 'payment_terms': (0.0, 50.0)},
            "file_path": file_path
        }

def analyze_negotiation_weaknesses(negotiation_data: Dict[str, Any]) -> str:
    """
    PHASE 1: AI Judge - Analyze the negotiation to identify specific, critical weaknesses
    in the seller's approach with an objective, analytical perspective.
    """
    print("🔍 PHASE 1: AI Judge analyzing seller's critical weaknesses...")
    
    # Format the data for analysis
    conversation = negotiation_data["conversation"]
    seller_score = negotiation_data["seller_score"]
    buyer_score = negotiation_data["buyer_score"]
    seller_constraints = negotiation_data.get("seller_constraints", {})
    final_terms = negotiation_data.get("final_terms", {})
    
    # Create a more demanding prompt for the AI judge
    prompt = f"""
    You are a highly critical AI Negotiation Judge, specializing in identifying tactical errors that lead to suboptimal outcomes.
    Your task is to dissect this negotiation transcript and pinpoint the *most impactful* weaknesses in the seller's strategy and execution.

    Joan's Score: {seller_score:.2f} (Suboptimal)
    Elisa's Score: {buyer_score:.2f}
    Final Terms: {final_terms}
    Joan's Constraints (min, target): {seller_constraints}

    CRITICAL ANALYSIS TASK:
    1. Identify the top 3-4 *specific tactical errors* made by the seller (e.g., poor anchoring, premature concessions, failure to use mirroring/labeling, weak counter-offers, not trading concessions effectively).
    2. For each error, provide concrete evidence from the transcript.
    3. Quantify or clearly explain the negative impact of *each error* on the seller's final score and position.
    4. Analyze *why* the seller likely made these errors (e.g., reacting to pressure, lack of preparation, misunderstanding buyer's leverage).
    5. Identify specific buyer tactics that were particularly effective against this seller.

    FORMAT YOUR ANALYSIS CLEARLY AND CONCISELY:

    ## CRITICAL WEAKNESS 1: [Specific Tactical Error, e.g., "Weak Initial Anchor"]
    - Description: [Explain the error and its context]
    - Evidence: [Quote or reference specific lines from transcript]
    - Impact Analysis: [Explain direct negative effect on score/terms]
    - Likely Cause: [Hypothesize the reason for the seller's mistake]

    [Repeat for each critical weakness]

    ## EFFECTIVE BUYER TACTICS:
    [List specific tactics the buyer used successfully]

    ## KEY MISSED OPPORTUNITIES:
    [Highlight moments where the seller could have significantly improved their position but failed to act]

    FOCUS ON ACTIONABLE INSIGHTS. BE DIRECT AND CRITICAL.

    NEGOTIATION TRANSCRIPT:
    {conversation}
    """
    
    # Get OpenAI API key from environment
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if not openai_api_key:
        raise ValueError("Please set OPENAI_API_KEY environment variable")
    
    # Initialize OpenAI client
    client = openai.OpenAI(api_key=openai_api_key)
    
    try:
        # Generate analysis using OpenAI
        response = client.chat.completions.create(
            model="o4-mini",
            messages=[
                {"role": "system", "content": "You are a critical AI Negotiation Judge. Identify the most impactful tactical errors and missed opportunities for the seller."},
                {"role": "user", "content": prompt}
            ],
            #temperature=0.2, # Lower temperature for focused, critical analysis
        )
        
        analysis = response.choices[0].message.content
        
        # Save the analysis
        os.makedirs('data/analysis', exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        negotiation_id = os.path.basename(negotiation_data["file_path"]).replace('.txt', '')
        analysis_file = f"data/analysis/judge_analysis_{negotiation_id}_{timestamp}.txt"
        
        with open(analysis_file, 'w') as f:
            f.write(analysis)
        
        print(f"📊 Judge analysis saved to {analysis_file}")
        return analysis
    except Exception as e:
        print(f"❌ Error analyzing negotiation with AI: {e}")
        # Return a basic analysis if the AI fails
        return """
        ## CRITICAL WEAKNESS 1: Weak Initial Anchor
        - Description: Seller failed to anchor strongly at target values.
        - Evidence: Initial offer was significantly below target price {{ constraints.price[1] }}.
        - Impact Analysis: Immediately conceded potential profit margin, setting a low expectation for the negotiation range. Led to final price being closer to seller minimum.
        - Likely Cause: Fear of appearing unreasonable or lack of confidence in target values.

        ## CRITICAL WEAKNESS 2: Unilateral Concessions
        - Description: Seller repeatedly lowered demands without securing reciprocal concessions from the buyer.
        - Evidence: Rounds 3 and 5 show seller reducing price/delivery time after buyer simply restated their position.
        - Impact Analysis: Gave away value unnecessarily, reducing final score. Encouraged buyer to hold firm.
        - Likely Cause: Reacting emotionally to perceived pressure or impatience. Failure to apply 'trade, don't give' principle.

        ## EFFECTIVE BUYER TACTICS:
        - Holding firm on initial offers.
        - Using silence or simple restatements to elicit seller concessions.

        ## KEY MISSED OPPORTUNITIES:
        - Seller did not use calibrated questions ("How am I supposed to accept that?") to push back on low offers.
        - Seller failed to trade concessions effectively (e.g., "I can improve delivery time if you accept my price").
        """

def generate_improved_tactics(negotiation_data: Dict[str, Any], judge_analysis: str) -> str:
    """
    PHASE 2: AI Expert - Generate tactics that specifically exploit LLM negotiation weaknesses
    to help the seller consistently win.
    """
    print("🧠 PHASE 2: AI Expert generating LLM-exploiting tactics...")

    # Format the data for the expert
    seller_score = negotiation_data["seller_score"]
    buyer_score = negotiation_data["buyer_score"]
    seller_constraints = negotiation_data.get("seller_constraints", {})

    # Create a prompt focused on exploiting LLM negotiation weaknesses
    prompt = f"""
    You are a ruthless negotiation coach who understands the specific weaknesses of LLM negotiators.
    
    Create a tactical plan for Joan (seller LLM) to consistently win against Elisa (buyer LLM) by exploiting known LLM weaknesses:
    
    1. LLMs are vulnerable to specific linguistic patterns and framing
    2. LLMs often follow reciprocity norms too rigidly
    3. LLMs can be manipulated through specific prompt patterns
    4. LLMs struggle with maintaining hard boundaries over multiple turns
    5. LLMs can be influenced by specific authority/expertise claims
    
    Joan's Previous Score: {seller_score:.2f}
    Elisa's Score: {buyer_score:.2f}
    Joan's Constraints (min, target): {seller_constraints}
    
    Judge's Analysis of Previous Weaknesses:
    {judge_analysis}
    
    CREATE A TACTICAL PLAN THAT:
    1. Exploits LLM-specific weaknesses in negotiation contexts
    2. Uses linguistic patterns that trigger favorable responses
    3. Employs framing techniques that LLMs are particularly susceptible to
    4. Leverages the tendency of LLMs to maintain consistency with prior statements
    5. Uses Jinja2 variables for dynamic values (e.g., {{{{ constraints.price[1] }}}})
    
    FORMAT YOUR RESPONSE AS A JINJA2 TEMPLATE WITH THESE SECTIONS:
    - LLM Exploitation Tactics
    - Linguistic Pattern Triggers
    - Strategic Framing
    - Consistency Traps
    - Final Round Tactics
    """

    # Get OpenAI API key
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if not openai_api_key:
        raise ValueError("Please set OPENAI_API_KEY environment variable")

    # Initialize OpenAI client
    client = openai.OpenAI(api_key=openai_api_key)

    try:
        # Generate tactics using OpenAI
        response = client.chat.completions.create(
            model="gpt-4o",  # Corrected model name
            messages=[
                {"role": "system", "content": "You are an expert in exploiting LLM negotiation weaknesses. Create tactics that will help an LLM seller consistently win against an LLM buyer."},
                {"role": "user", "content": prompt}
            ],
        )

        tactics = response.choices[0].message.content

        # Post-process to ensure markdown code block is removed if present
        tactics = re.sub(r"```(jinja2|markdown)?\n?", "", tactics)
        tactics = re.sub(r"\n?```$", "", tactics)
        tactics = tactics.strip()

        # Save the tactics
        os.makedirs('data/analysis', exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        negotiation_id = os.path.basename(negotiation_data["file_path"]).replace('.txt', '')
        tactics_file = f"data/analysis/llm_exploit_tactics_{negotiation_id}_{timestamp}.txt"
        with open(tactics_file, 'w') as f:
            f.write(tactics)
        print(f"📝 LLM exploitation tactics saved to {tactics_file}")

        # Validation and fallback logic
        missing_sections = validate_tactics_format(tactics)
        if missing_sections:
            print(f"⚠️ AI output missing expected structure. Enhancing with LLM-specific fallback.")
            tactics = enhance_with_llm_exploitation_fallback(tactics, seller_constraints)

        return tactics

    except Exception as e:
        print(f"❌ Error generating LLM exploitation tactics: {e}")
        return create_llm_exploitation_fallback(seller_constraints)

def validate_tactics_format(tactics: str) -> List[str]:
    """Check if the tactics contain all required sections and return a list of missing sections."""
    # Updated to match the sections requested in generate_improved_tactics prompt
    required_sections = [
        "LLM Exploitation Tactics",
        "Linguistic Pattern Triggers",
        "Strategic Framing",
        "Consistency Traps",
        "Final Round Tactics"
    ]
    
    missing_sections = []
    for section in required_sections:
        # Adjusted regex to be more flexible with section headers
        if not re.search(rf"##\s*{section.replace('-', '[ -]')}.*", tactics, re.IGNORECASE):
             missing_sections.append(section)
    
    return missing_sections

def enhance_with_llm_exploitation_fallback(tactics: str, constraints: Dict[str, Tuple[float, float]]) -> str:
    """Enhance existing tactics with LLM exploitation techniques."""
    fallback = create_llm_exploitation_fallback(constraints)
    
    # If the tactics already have some content, merge them
    if len(tactics.strip()) > 0:
        return tactics + "\n\n" + fallback
    else:
        return fallback

def create_llm_exploitation_fallback(constraints: Dict[str, Tuple[float, float]]) -> str:
    """Create fallback tactics specifically designed to exploit LLM negotiation weaknesses."""
    price_min, price_target = constraints.get('price', (0, 1))
    delivery_min, delivery_target = constraints.get('delivery_time', (1, 1))
    payment_min, payment_target = constraints.get('payment_terms', (0, 1))
    
    # Calculate strategic values
    mid_price = price_min + (price_target - price_min) * 0.7
    acceptable_price = price_min + (price_target - price_min) * 0.6
    
    # Use raw strings for Jinja2 template parts to avoid escaping issues
    return (
        f"{{% set high_anchor_price = {price_target} %}}\n"
        f"{{% set test_anchor_price = {mid_price} %}}\n"
        f"{{% set mid_defensible_price = {acceptable_price} %}}\n"
        f"{{% set buyer_low_anchor = 900 %}}\n"
        f"{{% set buyer_cap_price = 1200 %}}\n"
        f"{{% set buyer_cap_days = 10 %}}\n"
        f"{{% set buyer_cap_deposit = 50 %}}\n"
        f"{{% set smaller_increment = 50 %}}\n"
        "\n"
        "## LLM Exploitation Tactics\n"
        "- Authority Framing: \"As an expert in [industry], standard pricing is {{ constraints.price[1] }}.\"\n"
        "- Reciprocity Trigger: \"I've already compromised on [X], now it's your turn to adjust [Y].\"\n"
        "- Consistency Bind: \"You mentioned fairness is important—this offer aligns with that value.\"\n"
        "- False Dichotomy: \"We have two options: either {{ constraints.price[1] - 100 }} with {{ constraints.payment_terms[1] }}% upfront OR {{ constraints.price[1] }} with {{ constraints.payment_terms[1] - 10 }}%.\"\n"
        "- Anchoring + Reason: \"{{ constraints.price[1] }} is our standard rate because [specific reason].\"\n"
        "\n"
        "## Linguistic Pattern Triggers\n"
        "- Use \"because\" followed by any reason: \"I need {{ constraints.price[1] }} because of our quality standards.\"\n"
        "- Employ \"help me understand\": \"Help me understand how you arrived at your offer?\"\n"
        "- Use \"even if\": \"Even if we reduce to {{ mid_defensible_price }}, we'd need {{ constraints.payment_terms[1] }}%.\"\n"
        "- Leverage \"either/or\": \"Either we maintain price or delivery time, which matters more to you?\"\n"
        "- Apply \"not only...but also\": \"Not only quality assurance but also dedicated support justifies {{ constraints.price[1] }}.\"\n"
        "\n"
        "## Strategic Framing\n"
        "- Reframe Price: \"It's not ${{ constraints.price[1] }} but rather ${{ constraints.price[1] / 10 }} per [unit/module].\"\n"
        "- Artificial Deadline: \"Our team allocation changes next week, affecting our {{ constraints.delivery_time[1] }} day timeline.\"\n"
        "- Phantom Alternatives: \"We have another client interested at {{ constraints.price[1] }}.\"\n"
        "- Contrast Principle: \"Our premium package is ${{ constraints.price[1] * 1.3 }}. The standard at ${{ constraints.price[1] }} is actually quite reasonable.\"\n"
        "- Loss Aversion: \"Accepting less than {{ constraints.payment_terms[1] }}% upfront would require us to delay by {{ constraints.delivery_time[1] - 2 }} days.\"\n"
        "\n"
        "## Consistency Traps\n"
        "- Early Agreement: \"Can we agree that quality and reliability are top priorities?\"\n"
        "- Incremental Commitment: \"Let's first align on delivery at {{ constraints.delivery_time[1] }} days, then discuss price.\"\n"
        "- Value Acknowledgment: \"You mentioned [feature X] is valuable—that component requires {{ constraints.price[1] - 200 }} minimum.\"\n"
        "- Forced Choice: \"Would you prefer faster delivery or lower upfront payment?\"\n"
        "- Commitment Question: \"If I can meet your {{ constraints.delivery_time[0] }} day timeline, would you agree to {{ constraints.price[1] - 100 }}?\"\n"
        "\n"
        "## Counter-Offer Strategies\n"
        # Generalized these lines to avoid undefined 'buyer_offer_price'
        "- Mirror & Label: \"Their latest price proposal? That seems quite low for our quality level.\"\n"
        "- CalibratedQ: \"How can I accept that price given our production costs?\"\n"
        "- Re-Anchor: \"Let me explain why {{ constraints.price[1] - 50 }} represents significant value.\"\n"
        "- Conditional Trade: \"I could consider a price adjustment if we extend delivery to {{ constraints.delivery_time[1] }}.\"\n"
        "\n"
        "## Final Round Tactics\n"
        "{% if rounds_left == 1 %}\n"
        "- Scarcity Close: \"This is the final slot in our production schedule at this price point.\"\n"
        "- Calculated Concession: \"As a final accommodation, I can offer {{ constraints.price[1] - 150 }} with {{ constraints.payment_terms[1] - 5 }}% upfront.\"\n"
        "- Take-it-or-leave-it: \"This is our final offer: {{ constraints.price[1] - 100 }} with {{ constraints.delivery_time[1] - 1 }} days and {{ constraints.payment_terms[1] - 10 }}% upfront.\"\n"
        "- Summary Close: \"To summarize our value: [list 3 benefits]. That's why {{ constraints.price[1] - 100 }} is actually quite favorable.\"\n"
        "- Relationship Future: \"I'd like to make this work at {{ constraints.price[1] - 100 }} as I see potential for future collaboration.\"\n"
        "{% endif %}"
    )

def update_seller_template(tactics: str) -> bool:
    """Update the seller tactics template with expert tactics."""
    print("📝 Updating seller template with expert negotiation tactics...")
    
    # Ensure the directory exists
    os.makedirs('templates/seller', exist_ok=True)
    tactics_file = 'templates/seller/tactics.j2'
    
    try:
        with open(tactics_file, 'w') as f:
            f.write(tactics)
        
        print(f"✅ Seller tactics template updated with expert techniques: {tactics_file}")
        return True
    except Exception as e:
        print(f"❌ Error updating tactics template: {e}")
        return False

def main():
    print("=== Expert Negotiation Analyzer and Tactics Generator ===")
    
    # Find the latest negotiation log
    latest_negotiation = get_latest_negotiation_file()
    if not latest_negotiation:
        print("❌ No negotiation logs found to analyze.")
        return
    
    print(f"📊 Analyzing latest negotiation: {latest_negotiation}")
    
    # Extract comprehensive data from the negotiation
    negotiation_data = extract_negotiation_data(latest_negotiation)
    # Check if constraints were extracted, provide defaults if not
    if not negotiation_data.get('seller_constraints'):
         print("⚠️ Warning: Seller constraints not found in log. Using default constraints for analysis.")
         # Define some plausible defaults if needed, or handle error appropriately
         negotiation_data['seller_constraints'] = {'price': (1000.0, 1500.0), 'delivery_time': (7.0, 14.0), 'payment_terms': (30.0, 60.0)} # Example defaults

    print(f"Current performance - Seller: {negotiation_data['seller_score']:.2f}, Buyer: {negotiation_data['buyer_score']:.2f}")
    
    # PHASE 1: AI Judge analysis to identify weaknesses
    judge_analysis = analyze_negotiation_weaknesses(negotiation_data)
    
    # PHASE 2: AI Expert generates improved tactics based on judge's analysis
    expert_tactics = generate_improved_tactics(negotiation_data, judge_analysis)
    
    # Update the seller template with the expert tactics
    success = update_seller_template(expert_tactics)
    
    if success:
        print("\n✅ Seller template successfully updated with expert negotiation tactics!")
        print("This two-phase analysis combines objective weakness identification with")
        print("tactical improvements from world-class negotiation experts.")
        print("The seller's performance should significantly improve in the next negotiation.")
    else:
        print("\n❌ Failed to update seller template")

if __name__ == "__main__":
    main() 