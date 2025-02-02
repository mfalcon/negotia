import pytest
from prompts.base_prompt import create_base_prompt
from prompts.seller_prompt import get_seller_prompt
from prompts.buyer_prompt import get_buyer_prompt

@pytest.fixture
def sample_terms():
    return {
        "price": 1100,
        "delivery_time": 10,
        "payment_terms": 50
    }

@pytest.fixture
def sample_constraints():
    return {
        "price": (1000, 1500),
        "delivery_time": (7, 14),
        "payment_terms": (50, 100),
        "max_rounds": 10
    }

def test_base_prompt_structure(sample_terms, sample_constraints):
    prompt = create_base_prompt(
        "seller",
        sample_terms,
        5,
        sample_constraints,
        "medium",
        "test note",
        "test tactics"
    )
    
    # Check essential elements are present
    assert "You are negotiating as the seller" in prompt
    assert "Current situation:" in prompt
    assert f"${sample_terms['price']}" in prompt
    assert str(sample_terms['delivery_time']) in prompt
    assert "Style guide for text chat:" in prompt
    assert "test tactics" in prompt

def test_seller_prompt(sample_terms, sample_constraints):
    prompt = get_seller_prompt(sample_terms, 5, sample_constraints, 10.0)
    
    # Check seller-specific elements
    assert "Pressure Tactics:" in prompt
    assert "Value and Loss Framing:" in prompt
    assert "Strategic Phrases to Use:" in prompt
    assert "other buyers interested" in prompt
    assert "Market position:" in prompt

def test_buyer_prompt(sample_terms, sample_constraints):
    prompt = get_buyer_prompt(sample_terms, 5, sample_constraints)
    
    # Check buyer-specific elements
    assert "You are negotiating as the buyer" in prompt
    assert "Key negotiation tactics for buyer:" in prompt
    assert "Value Assessment:" in prompt
    assert "Protect your interests" in prompt
    assert "Current situation:" in prompt 