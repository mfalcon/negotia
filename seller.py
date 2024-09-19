import os
from openai import OpenAI

prompt = """
    You are a seller in a negotiation. You have to sell a {item} to a buyer.
    You need to negotiate with the buyers to sell the {item}.
    You have to:
    - accept no less than {min_price}, the higher price the better
    - deliver the product in {min_days} days, the more days the better

    You'll negotiate with the buyer by chat, so you have to take turns.

    Take your time to negotiate, but don't take more than {max_interactions} turns.
    You have to try to close the deal before getting to {max_interactions} turns, your current turn is number {seller_interactions}.
    Do your best to close the deal as soon as possible. Accept the deal if you consider that the offer is good enough
    If you consider that the offer is good enough, be clear and explicit about it, say exactly  "deal!".

    This is the negotiation history:

    {chat_history}

    Your turn: 
"""


def get_seller_response(item, min_price, min_days, chat_history, seller_interactions, max_interactions):
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    formatted_prompt = prompt.format(
        item=item,
        min_price=min_price,
        min_days=min_days,
        chat_history=chat_history,
        seller_interactions=seller_interactions,
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