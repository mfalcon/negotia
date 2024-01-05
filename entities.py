from prompts import PROMPTS

class EvaluatorPrompt():
    def __init__(
            self,
            prompt_id
    ):
        self.prompt_id = prompt_id
    
    def render(self, message):
        context = '\n'.join([e for e in message])
        rendered_prompt = PROMPTS[self.prompt_id].format(message=context)
        return rendered_prompt

class Prompt():

    def __init__( #TODO: use dataclasses instead
            self,
            prompt_id,
            negotiator_name,
            min_value,
            max_value,
            product_name,
            product_type,
            properties
    ):
        
        self.prompt_id = prompt_id
        self.negotiator_name = negotiator_name
        self.min_value = min_value
        self.max_value = max_value
        self.product_name = product_name
        self.product_type = product_type
        self.properties = properties
    
    def render_properties(self):
        if not self.properties:
            return ''
        
        properties_prompt = """
        ##additional negotiation topics##
        Besides the item price. You can also negotiate the following list
        of issues:

        """
        item_properties = []
        for prop in self.properties:

            ranks = [rank for rank in list(prop.rank.keys())]

            item_properties.append(
                f'''
                There are {len(prop.rank)} options for the {prop.name}.
                Here they are sorted from best deal to worst deal:
                1) {ranks[0]}
                2) {ranks[1]}
                3) {ranks[2]}
                '''
            )

        properties_prompt += '\n'.join([ip for ip in item_properties]) 
        properties_prompt += '\n' + 'Try to get the best deal you can with each issue. ##end of additional negotiation topics##'

        return properties_prompt

    def render(self, messages, total_interactions):

        rendered_prompt = PROMPTS[self.prompt_id].format(
            negotiator_name = self.negotiator_name,
            product_name = self.product_name,
            product_type = self.product_type,
            min_value = self.min_value,
            max_value = self.max_value,
            previous_messages = messages,
            total_interactions = total_interactions+1,
            properties = self.render_properties()

        )
        return rendered_prompt


class Negotiator():

    def __init__(
            self,
            side,
            prompt,
            llm_instance
    ):
        
        self.side = side
        self.prompt = prompt
        self.llm_instance = llm_instance


class Property(): #TODO: add extra negotiation properties to the negotiation

    def __init__(
            self,
            name,
            rank,
            property_type
    ):
        
        self.name = name
        self.rank = rank
        self.property_type = property_type #positive/negative #TODO: add available categories


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
    
class NegotiationEvaluator():

    def __init__(
            self,
            prompt,
            llm_instance

    ):
        
        self.prompt = prompt
        self.llm_instance = llm_instance