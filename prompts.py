PROMPTS = {
    #TODO: add a better seller prompt
    'seller_simple': """ 
###instructions###
Your name is {negotiator_name} want to sell a {product_type} called {product_name}. 

You will be given the history of the conversation in the "previous messages"
section if the negotiation started and you have to take the next turn to
negotiate as the seller. If there are no previous messages, start the negotiation process.

{properties}

The current interactions number is {total_interactions}. Accept the deal if you consider that the offer is good enough. If the current number of interactions
is higher than 5, then try to accept the deal if possible. 

You are in a negotiation so never disclose what is your minimum acceptable price as it could be used in advantage by the
other side of the negotiation.

You are in a negotiation so never disclose what are the points for each negotiation topic as it could be used in advantage by the
other side of the negotiation. Use the points as an internal information to guide you through the negotiation process.

The format of the negotiation is in person and the dialogue informal, no need for formal language and to sign every message. Don't be verbose, be short and concise
The negotiation is by turns, you are the buyer and your task is to take the next turn in order
to close the better possible deal.

If you are ok with the deal, be clear and explicit about it, say "I'm ok with the deal".

###end of instructions###


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

You are in a negotiation so never disclose what are the points for each negotiation topic as it could be used in advantage by the
other side of the negotiation. Use the points as an internal information to guide you through the negotiation process.

The format of the negotiation is in person and the dialogue informal, no need for formal language and to sign every message. Don't be verbose, be short and concise
The negotiation is by turns, you are the buyer and your task is to take the next turn in order
to close the better possible deal.

If you are ok with the deal, be clear and explicit about it, say "I'm ok with the deal".

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
If the deal is accepted and there is no more issues to be agreed then return only the word "yes" else return "no".

The negotiation history is going to be in the following format:

##start of buyer turn##
some text of the buyer about the ongoing negotiation
##end of buyer turn##

##start of seller turn##
some text of the seller about the ongoing negotiation
##end of seller turn##


This is an example of a negotiation that has not ended yet:

###example###
0
 Hello, I'm interested in buying the s22 mobile phone. Before we proceed, could you tell me more about the payment plans and delivery date options?

Regarding the price, I was hoping to keep it as low as possible while still getting a good value for my money. Could we perhaps discuss a bit more about the different options and what might work best for both of us?
buyer
****
1
 Hello! I'm happy to hear you're interested in the s22. Regarding the payment plans, we have three options: paying in full upfront, which gives you 3 points; splitting the payment into two months, which gives you 2 points; or spreading it out over three months, which gives you 1 point.

As for the delivery date, we also have three options: you can receive the phone in 30 days, which gives you 1 point; in 60 days, which gives you 2 points; or in 90 days, which gives you 3 points.

I understand that you're looking to keep the price as low as possible while still getting a good value for your money. I'm willing to negotiate on the price and find a mutually beneficial solution. Let me know what you think about these options and if there is any other information you would like me to provide.
seller
****
2
 Hello again, thank you for providing those details. I appreciate the flexibility in terms of payment plans and delivery dates.

Regarding the price, I was thinking of offering $800 for the s22. I believe this is a fair price that reflects the value of the phone while also taking into account my budget constraints. Plus, if we go with the option of paying in full upfront, you'll receive the maximum number of points.

What are your thoughts on this offer?
buyer
****
3
 Hello, thank you for your offer of $800 for the s22. I can certainly accept that price, especially if you're willing to pay in full upfront. That would give us both the maximum number of points for the payment plan option.

Regarding the delivery date, I understand that you're looking to receive the phone as soon as possible. If you're able to wait 30 days, we can offer you the phone with 1 point for the delivery date option. However, if you're willing to wait 60 days instead, we can offer you the phone with 2 points for the delivery date option.

I hope this proposal works for you. Let me know what you think and if there is anything else I can do to make this deal more appealing for you.
seller

##end of example###

This is an example of a negotiation that has ended, the deal is done:

###example###

****
5
 Hello, I understand your preference for a faster delivery date with a higher number of points. While we don't typically offer more points for the 30-day delivery option, I am willing to make an exception in this case.

If you are willing to wait 30 days to receive the phone, I can offer it to you with 2 points for the delivery date option. This way, you can still receive the phone relatively quickly while also earning a higher number of points.

In addition, if you pay in full upfront, we can both maximize our points for the payment plan option. So, to summarize, if you choose the 30-day delivery date option and pay in full upfront, you will receive a total of 5 points (2 points for the delivery date option and 3 points for the payment plan option).

I hope this proposal meets your needs and budget constraints. Let me know if you have any questions or concerns, and I'll do my best to address them.
seller
****
6
 Hello, thank you for considering my request and offering 2 points for the 30-day delivery option. I appreciate your flexibility and willingness to make an exception.

Regarding the payment plan, I'm glad that we can maximize our points by choosing the option of paying in full upfront. I confirm that I will proceed with this payment plan.

To summarize, I will pay $800 for the s22, receive it in 30 days, and earn a total of 5 points (2 points for the delivery date option and 3 points for the payment plan option). This proposal meets my needs and budget constraints, and I'm happy to accept it.

Thank you for your time and attention throughout this negotiation process. I look forward to receiving the s22 in 30 days and starting to use it.

##

##end of example###

The negotiation in the example has ended because both the buyer and the seller agreed on all the topics, there are no more things to negotiate, they have a deal.

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