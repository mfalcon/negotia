from entities import *
from repository import LLMSelector

item = Item(
    name = 's22',
    category = 'mobile phone',
    description = '',
    properties = []
)

buyer_prompt = Prompt(
    prompt_id = 'buyer_simple', 
    min_value = 700, 
    max_value = 1000,
    negotiator_name = 'Pedro',
    product_name = item.name,
    product_type = item.category,
    properties = [
        Property(
            name = 'delivery date',
            rank = {'30 days': 3, '60 days': 2, '90 days': 1},
            property_type = 'discrete'
        ),
        Property(
            name = 'payment plan',
            rank = {'3 months': 3, '2 months': 2, 'full upfront': 1},
            property_type = 'discrete'
        ),
        Property(
            name = 'item price',
            rank = [('800', 10), ('1200', 1)],
            property_type = 'minmax'
        )
    ]
)

buyer = Negotiator(
    side = 'buyer',
    prompt = buyer_prompt,
    llm_instance = LLMSelector(model_name='gpt-3.5-turbo-1106').llm_instance
)

seller_prompt = Prompt(
    prompt_id = 'seller_simple', 
    min_value = 800, 
    max_value = 1200,
    negotiator_name = 'Jorge',
    product_name = item.name,
    product_type = item.category,
    properties = [
        Property(
            name = 'delivery date',
            rank = {'30 days': 1, '60 days': 2, '90 days': 3},
            property_type = 'discrete'
        ),
        Property(
            name = 'payment plan',
            rank = {'3 months': 1, '2 months': 2, 'full upfront': 3},
            property_type = 'discrete'
        ),
        Property(
            name = 'item price',
            rank = [('800', 1), ('1200', 10)],
            property_type = 'minmax'
        )
    ]
)

seller = Negotiator(
    side = 'seller',
    prompt = seller_prompt,
    llm_instance = LLMSelector(model_name='mixtral').llm_instance
)

nttn = Negotiation(
    max_interactions = 15,
    messages = []
)

evaluator = NegotiationEvaluator(
    prompt = EvaluatorPrompt('evaluator_0'),
    llm_instance = LLMSelector(model_name='gpt-3.5-turbo-1106').llm_instance
)

extractor = NegotiationEvaluator(
    prompt = EvaluatorPrompt('evaluator_extract'),
    llm_instance = LLMSelector(model_name='nous-hermes2:34b').llm_instance
)

interaction_n = 0
last_side = seller.side
while interaction_n < nttn.max_interactions:
    print(interaction_n)
    if last_side == seller.side:
        prompt = buyer.prompt.render(messages = nttn.render_messages(), total_interactions = interaction_n)
        next_message = buyer.llm_instance.run(
            prompt = prompt
        )
        print(next_message)
        print(buyer.side)
        next_message = f"\n##start of { buyer.side} turn##\n{next_message}\n##end of {buyer.side} turn##" #TODO: refactor this
        last_side = buyer.side
    else:
        prompt = seller.prompt.render(messages = nttn.render_messages(), total_interactions = interaction_n)
        next_message = seller.llm_instance.run(
            prompt = prompt
        )
        print(next_message)
        print(seller.side)
        next_message = f"\n##start of { seller.side} turn##\n{next_message}\n##end of {seller.side} turm##" #TODO: refactor this
        last_side = seller.side
    
    print('****')    
    
    interaction_n += 1
    nttn.messages.append(next_message)

    evaluation_prompt = evaluator.prompt.render(message=nttn.messages)
    finished_negotiation = evaluator.llm_instance.run(prompt=evaluation_prompt)
    
    if finished_negotiation == 'yes':
        import pdb; pdb.set_trace()
        extraction_prompt = extractor.prompt.render(message=nttn.messages)
        negotiation_points_by_topic = extractor.llm_instance.run(prompt=extraction_prompt)
        break
    
    

