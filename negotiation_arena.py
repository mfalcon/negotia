from buyer import get_buyer_response
from seller import get_seller_response

def format_chat_history(chat_history):
    return "\n".join(chat_history)

def run_negotiation(item, min_price, max_price, min_days, max_days, max_interactions):
    chat_history = []
    current_role = "buyer"
    response = ""
    buyer_interactions = 0
    seller_interactions = 0

    while buyer_interactions < max_interactions and seller_interactions < max_interactions and "deal!" not in response.lower():

        if current_role == "buyer":
            response = get_buyer_response(item, max_price, max_days, format_chat_history(chat_history), buyer_interactions, max_interactions)
            buyer_interactions += 1
        else:
            response = get_seller_response(item, min_price, min_days, format_chat_history(chat_history), seller_interactions, max_interactions)
            seller_interactions += 1
                
        print(f'{current_role}: {response}')
        chat_history.append(f'{current_role}: {response}')
        current_role = "seller" if current_role == "buyer" else "buyer"
        
    
if __name__ == "__main__":
    run_negotiation("item", min_price=200, max_price=220, min_days=45, max_days=60, max_interactions=10)