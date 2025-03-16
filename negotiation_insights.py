import os
import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime

class NegotiationInsights:
    """
    Class to manage and store insights from previous negotiations
    that can be used to improve future negotiations.
    """
    
    def __init__(self, insights_file: str = "data/negotiation_insights.json"):
        self.insights_file = insights_file
        self.insights = self._load_insights()
    
    def _load_insights(self) -> Dict[str, Any]:
        """Load insights from file or create a new insights structure."""
        os.makedirs(os.path.dirname(self.insights_file), exist_ok=True)
        
        if os.path.exists(self.insights_file):
            try:
                with open(self.insights_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"Error loading insights file. Creating new insights.")
        
        # Initialize with empty structure
        return {
            "seller": {
                "improvement_suggestions": [],
                "effective_techniques": [],
                "last_updated": datetime.now().isoformat()
            },
            "buyer": {
                "improvement_suggestions": [],
                "effective_techniques": [],
                "last_updated": datetime.now().isoformat()
            }
        }
    
    def _save_insights(self):
        """Save insights to file."""
        with open(self.insights_file, 'w') as f:
            json.dump(self.insights, f, indent=2)
    
    def add_seller_insights(self, analysis_file: str):
        """Extract and add seller insights from an analysis file."""
        if not os.path.exists(analysis_file):
            print(f"Analysis file {analysis_file} not found.")
            return
        
        with open(analysis_file, 'r') as f:
            content = f.read()
        
        # Extract improvement suggestions
        suggestions_section = re.search(r"--- IMPROVEMENT SUGGESTIONS ---\n(.*?)(?=\n\n|\Z)", 
                                       content, re.DOTALL)
        if suggestions_section:
            suggestions_text = suggestions_section.group(1)
            suggestions = re.findall(r"- (.*?)(?=\n-|\Z)", suggestions_text, re.DOTALL)
            suggestions = [s.strip() for s in suggestions if s.strip()]
            
            # Add new unique suggestions
            for suggestion in suggestions:
                if suggestion not in self.insights["seller"]["improvement_suggestions"]:
                    self.insights["seller"]["improvement_suggestions"].append(suggestion)
        
        # Extract effective techniques
        techniques_section = re.search(r"--- NEGOTIATION TECHNIQUES USED ---\n(.*?)(?=\n\n|\Z)", 
                                      content, re.DOTALL)
        if techniques_section:
            techniques_text = techniques_section.group(1)
            techniques = re.findall(r"- (.*?)(?=\n-|\Z)", techniques_text, re.DOTALL)
            
            for technique_line in techniques:
                # Extract technique name and count
                technique_match = re.match(r"(.*?):\s*(\d+)\s*instances", technique_line)
                if technique_match and int(technique_match.group(2)) > 1:  # Only add if used multiple times
                    technique = technique_match.group(1).strip()
                    if technique not in self.insights["seller"]["effective_techniques"]:
                        self.insights["seller"]["effective_techniques"].append(technique)
        
        # Update timestamp
        self.insights["seller"]["last_updated"] = datetime.now().isoformat()
        
        # Save updated insights
        self._save_insights()
        print(f"Added seller insights from {analysis_file}")
    
    def add_buyer_insights(self, analysis_file: str):
        """Extract and add buyer insights from an analysis file."""
        # Similar implementation for buyer insights
        # ...
    
    def get_seller_insights(self, max_suggestions: int = 3, max_techniques: int = 3) -> Dict[str, List[str]]:
        """Get the most recent seller insights for use in prompts."""
        return {
            "improvement_suggestions": self.insights["seller"]["improvement_suggestions"][-max_suggestions:],
            "effective_techniques": self.insights["seller"]["effective_techniques"][-max_techniques:]
        }
    
    def get_buyer_insights(self, max_suggestions: int = 3, max_techniques: int = 3) -> Dict[str, List[str]]:
        """Get the most recent buyer insights for use in prompts."""
        return {
            "improvement_suggestions": self.insights["buyer"]["improvement_suggestions"][-max_suggestions:],
            "effective_techniques": self.insights["buyer"]["effective_techniques"][-max_techniques:]
        } 