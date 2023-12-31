from prompts import PROMPTS

class Prompt():

    def __init__(
            self,
            prompt_id,
            min_value,
            max_value,
            product_name,
            product_type
    ):
        
        self.prompt_id = prompt_id
        self.min_value = min_value
        self.max_value = max_value
        self.product_name = product_name
        self.product_type = product_type

    def render(self, messages, total_interactions):
        rendered_prompt = PROMPTS[self.prompt_id].format(
            product_name = self.product_name,
            product_type = self.product_type,
            min_value = self.min_value,
            max_value = self.max_value,
            previous_messages = messages,
            total_interactions = total_interactions
        )
        return rendered_prompt


class Negotiator():

    def __init__(
            self,
            name,
            side,
            prompt,
            llm_instance
    ):
        
        self.name = name
        self.side = side
        self.prompt = prompt
        self.llm_instance = llm_instance


class Property():

    def __init__(
            self,
            name,
            rank,
            property_type
    ):
        
        self.name = name
        self.rank = rank
        self.property_type = property_type #positive/negative


class Item():

    def __init__(
            self,
            name,
            category,
            description,
            properties
    ):
        
        self.name = name
        self.category = category
        self.description = description
        self.properties = properties


class Message():

    def __init__(
            self,
            side,
            text
    ):
    
        self.side = side #buyer, seller
        self.text = text

class Negotiation():

    def __init__(
            self,
            max_interactions,
            messages
    ):
        self.max_interactions = max_interactions
        self.messages = messages

    def render_messages(self):
        return '\n'.join([e for e in self.messages])