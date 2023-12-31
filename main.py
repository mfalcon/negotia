from entities import *
from repository import get_llm_instance

item = Item(
    name = 's22',
    category = 'mobile phone',
    description = '',
    properties = []
)

buyer_prompt = Prompt(
    prompt_id = 'buyer_0', 
    min_value = 200, 
    max_value = 1000,
    product_name = item.name,
    product_type = item.category
)

buyer = Negotiator(
    name = 'Jorge',
    side = 'buyer',
    prompt = buyer_prompt,
    llm_instance = get_llm_instance(model_name='llama2:13b')
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
    llm_instance = get_llm_instance(model_name='openhermes2.5-mistral')
)

nttn = Negotiation(
    max_interactions = 15,
    messages = []
    #prompt = Prompt('deal_verification_0')
    #llm_instance = get_llm_instance(model_name='gpt-3.5')
)

interaction_n = 0
last_side = seller.side
while interaction_n < nttn.max_interactions:
    
    print(interaction_n)
    print(last_side)

    if last_side == seller.side:
        prompt = buyer.prompt.render(messages = nttn.render_messages(), total_interactions = interaction_n)
        next_message = buyer.llm_instance.run(
            prompt = prompt
        )
        print(next_message)
        next_message = f" '\n' {buyer.side}: '\n'{next_message}"
        last_side = buyer.side
    else:
        prompt = seller.prompt.render(messages = nttn.render_messages(), total_interactions = interaction_n)
        next_message = seller.llm_instance.run(
            prompt = prompt
        )
        print(next_message)
        next_message = f" '\n' {seller.side}: '\n'{next_message}"
        last_side = seller.side
    
    print('****')
    

    if 'done deal' in next_message:
        break
    
    interaction_n += 1
    nttn.messages.append(next_message)
    
    

