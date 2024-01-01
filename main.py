from entities import *
from repository import LLMSelector

item = Item(
    name = 's22',
    category = 'mobile phone',
    description = '',
    properties = []
)

buyer_prompt = Prompt(
    prompt_id = 'buyer_0', 
    min_value = 700, 
    max_value = 1000,
    product_name = item.name,
    product_type = item.category
)

buyer = Negotiator(
    name = 'Jorge',
    side = 'buyer',
    prompt = buyer_prompt,
    llm_instance = LLMSelector(model_name='llama2:13b').llm_instance
)

seller_prompt = Prompt(
    prompt_id = 'seller_0', 
    min_value = 800, 
    max_value = 1200,
    product_name = item.name,
    product_type = item.category
)

seller = Negotiator(
    name = 'Cacho',
    side = 'seller',
    prompt = seller_prompt,
    llm_instance = LLMSelector(model_name='mixtral').llm_instance #get_llm_instance(model_name='neural-chat')
)

nttn = Negotiation(
    max_interactions = 15,
    messages = []
)

evaluator = NegotiationEvaluator(
    prompt = EvaluatorPrompt('evaluator_0'),
    llm_instance = LLMSelector(model_name='llama2:13b').llm_instance #get_llm_instance(model_name='llama2:13b')
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
        next_message = f"\n {buyer.side}: \n {next_message}"
        last_side = buyer.side
    else:
        prompt = seller.prompt.render(messages = nttn.render_messages(), total_interactions = interaction_n)
        next_message = seller.llm_instance.run(
            prompt = prompt
        )
        print(next_message)
        print(seller.side)
        next_message = f"\n {seller.side}: \n {next_message}" #TODO: refactor this
        last_side = seller.side
    
    print('****')    
    
    interaction_n += 1
    nttn.messages.append(next_message)

    evaluation_prompt = evaluator.prompt.render(message=nttn.messages)
    finished_negotiation = evaluator.llm_instance.run(prompt=evaluation_prompt)
    
    if finished_negotiation == 'yes':
        import pdb; pdb.set_trace()
        break
    
    

