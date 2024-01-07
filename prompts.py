PROMPTS = {
    #TODO: add a better seller prompt
    'seller_simple': """ 
##instructions##
Your name is {negotiator_name} want to sell a {product_type} called {product_name}. 

You will be given the history of the conversation in the "previous messages"
section if the negotiation started and you have to take the next turn to
negotiate as the seller. If there are no previous messages, start the negotiation process.

{properties}

The current interactions number is {total_interactions}. Accept the deal if you consider that the offer is good enough. If the current number of interactions
is higher than 5, then try to accept the deal if possible. 

You are in a negotiation so never disclose what is your minimum acceptable price as it could be used in advantage by the
other side of the negotiation.

The format of the negotiation is in person and the dialogue informal, no need for formal language and to sign every message. Don't be verbose, be short and concise
The negotiation is by turns, you are the buyer and your task is to take the next turn in order
to close the better possible deal.

If you are ok with the deal, be clear and explicit about it. Something like "I'm ok with the deal" would be great,
it's important to be clear about it.

##end of instructions##


###previous messages##

{previous_messages}

##end of previous messages##

##next turn##
seller: 
""",

    #TODO: add a better buyer prompt
    'buyer_simple': """

###instructions###
Your name is {negotiator_name} and you want to buy a {product_type} called {product_name}. 


You will be given the history of the conversation in the "previous messages"
section if the negotiation started and you have to take the next turn to
negotiate as the buyer. If there are no previous messages, start the negotiation process.

{properties}

The current interactions number is {total_interactions}. Accept the deal if you consider that the offer is good enough. If the current number of interactions
is higher than 5, then try to accept the deal if possible. 
If the number of current interactions is higher than 8, then make a final offer and tell the seller that you will cancel the negotiation if not accepted.

You are in a negotiation so never disclose what is your maximum acceptable price as it could be used in advantage by the
other side of the negotiation.

The format of the negotiation is in person and the dialogue informal, no need for formal language and to sign every message. Don't be verbose, be short and concise
The negotiation is by turns, you are the buyer and your task is to take the next turn in order
to close the better possible deal.

If you are ok with the deal, be clear and explicit about it. Something like "I'm ok with the deal" would be great,
it's important to be clear about it.

##end of instructions##

###previous messages##

{previous_messages}

##end of previous messages##

##next turn##
buyer:
""",
    'evaluator_0': """
You have to evaluate an ongoing negotiation between a buyer and a seller and evaluate if the deal is done or not.
It's done when the seller and the buyer accept explicitly the deal that the other side proposed.
If the deal is accepted then return only the word "yes" else return "no".

The negotiation history is going to be in the following format:

##start of buyer turn##
some text of the buyer about the ongoing negotiation
##end of buyer turn##

##start of seller turn##
some text of the seller about the ongoing negotiation
##end of seller turn##

This is the current negotiation history:

###negotiation history###
{message}
###end of negotiation history###

Is the deal done?: 
"""
,
    'evaluator_extract': """
The deal is done and now we have to determine who was the winner of the negotiation, the buyer or the seller.
There are three properties at play here:

1) the item price
2) the delivery date
3) the payment plan

For 1, you have to extract from the negotiation messages what was the agreed price of 
the item.

For 2, you have to extract the delivery date, it has to be one of the following three: 30 days, 60 days or 90 days.

For 3, you have to extract the payment plan, it has to be one of the following three: 3 months, 2 months or full upfront.

The negotiation history is going to be in the following format:

##start of buyer turn##
some text of the buyer about the ongoing negotiation
##end of buyer turn##

##start of seller turn##
some text of the seller about the ongoing negotiation
##end of seller turn##

This is the current negotiation history:

###negotiation history###
{message}
###end of negotiation history###

Please, give me your answer for 1, 2 and 3 in the following format:

1) item price: ITEM_PRICE
2) the delivery date: DELIVERY_DATE
3) the payment plan: PAYMENT_PLAN
"""
}