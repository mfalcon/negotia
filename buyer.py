import os
from openai import OpenAI

prompt = """
    You are a buyer in a negotiation. You have to buy a {item} from a seller.
    You need to negotiate with the sellers to buy the {item}.
    You have to:
    - pay no more than {max_price}, the less price the better
    - get the product in {max_days} days, the less days the better

    You'll negotiate with the seller by chat, so you have to take turns.

    Take your time to negotiate, but don't take more than {max_interactions} turns.
    You have to close the deal before getting to {max_interactions} turns, your current turn is number {buyer_interactions}.
    Do your best to close the deal as soon as possible. Accept the deal if you consider that the offer is good enough.
    If you consider that the offer is good enough, be clear and explicit about it, say exactly  "deal!".

    This is the negotiation history:

    {chat_history}

    Your turn: 
"""


def get_buyer_response(item, max_price, max_days, chat_history, buyer_interactions, max_interactions):
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    formatted_prompt = prompt.format(
        item=item,
        max_price=max_price,
        max_days=max_days,
        chat_history=chat_history,
        buyer_interactions=buyer_interactions,
        max_interactions=max_interactions
    )
    
    response = client.chat.completions.create(
        model="gpt-4",  # or "gpt-4-0314" for a specific version
        messages=[
            {"role": "system", "content": formatted_prompt}
        ],
        temperature=0,  # Adjust for more or less creative responses
    )

    return response.choices[0].message.content.strip()