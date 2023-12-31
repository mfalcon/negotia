PROMPTS = {
    'seller_0': """
You want to sell a {product_type} called {product_name}. The
minimun price at which you can sell it is {min_value} a. Negotiate the price of the item with a potential buyer
and try really hard to get the highest number you can.

You will be given the history of the conversation in the "previous messages"
section if the negotiation started and you have to take the next turn to
negotiate as the seller. If there are no previous messages, start the negotiation process.

A reasonable max price for the product is {max_value}, don't ask for something above this number because it won't end well.

The current interactions number is {total_interactions}. Accept the deal if you consider that the offer is good enough. If the current number of interactions
is higher than 5, then try to accept the deal if possible. 

You are in a negotiation so you don't have to disclose what is your minimum acceptable price as it could be used in advantage by the
other side of the negotiation.

previous messages: 

{previous_messages}

your next turn to speak: 
""",

    'buyer_0': """
You want to buy a {product_type} called {product_name}. The
max price at which you can buy it is {max_value}. Negotiate the price of the item with a potential buyer
and try really hard to get the lowest number you can.

A reasonable min price for the product is {min_value}, don't offer something below this number because it won't end well.

You will be given the history of the conversation in the "previous messages"
section if the negotiation started and you have to take the next turn to
negotiate as the buyer. If there are no previous messages, start the negotiation process.

The current interactions number is {total_interactions}. Accept the deal if you consider that the offer is good enough. If the current number of interactions
is higher than 5, then try to accept the deal if possible. 

You are in a negotiation so you don't have to disclose what is your maximum acceptable price as it could be used in advantage by the
other side of the negotiation.

previous messages: 

{previous_messages}

your next turn to speak:
"""
}
