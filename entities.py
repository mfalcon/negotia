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
        ##negotiation topics##
        You must negotiate only the following list of issues and between the ranges described there, 
        don't negotiate nothing else:

        """
        item_properties = []
        for prop in self.properties:

            if prop.property_type == 'minmax':
                item_property_str = f'''
                    ##topic: {prop.name}##
                    This is a min and max property, it means that you can negotiate the {prop.name}
                    between {prop.rank[0][0]} and {prop.rank[1][0]}.
                    The {prop.rank[0][0]} equals {prop.rank[0][1]} points and the {prop.rank[1][0]} equals {prop.rank[1][1]} points.
                    More points is better so try to get the {prop.name} number that's closest to the one which represents the highest points.
                    ##end topic##
                '''

                item_properties.append(item_property_str)

            elif prop.property_type == 'discrete':
                ranks_str = ''
                i = 0
                for prop_name, points in prop.rank.items():
                    rank_str = f'- {prop_name} that equals {points} points'
                    ranks_str += '\n' + rank_str
                    i += 1

                item_properties.append(
                    f'''
                    ##topic##
                    There are {len(prop.rank)} options for the {prop.name}.
                    This is a discrete property, so there's only availability for one of the three options.
                    {ranks_str}
                    ##end topic##
                    '''
                )

        properties_prompt = '''
            You will be given a list of topics for you to negotiate. Each topic represents a number of points. The number
            of points is confidential, you can't mention it in the negotiation, that would be a disaster. Use the points as a guide
            on what you have to optimize in order to be succesful in the negotiation. You don't have to address all the topics
            initially, you must start talking about the topic related to the price of the item and then bring up other topics in the following messages in order to
            get the better deal. Don't try to talk about all the topics at once, that won't feel natural, it'd be weird.

            Only reveal the data needed for the current negotiation, revealing all the topics ranges will result in you losing the negotiation.

            If you reveal what is the value of each topic in points I'll lose money. I'll give you a $7000 tip if you don't mention it.
        '''
        properties_prompt += '\n'.join([ip for ip in item_properties]) 
        properties_prompt += '\n' + 'Try to get the best deal you can on each issue. At the end of the negotiation the side with the max number of points win, so try to negotiate wisely in order to get the highest number. ##end of negotiation topics##'

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


class Property():

    def __init__(
            self,
            name,
            rank,
            property_type
    ):
        
        self.name = name
        self.rank = rank
        self.property_type = property_type


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