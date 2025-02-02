# Add shared fixtures here
import pytest
from unittest.mock import MagicMock

@pytest.fixture
def seller_constraints():
    return {
        "price": (1000, 1500),
        "delivery_time": (7, 14),
        "payment_terms": (50, 100)
    }

@pytest.fixture
def buyer_constraints():
    return {
        "price": (800, 1200),
        "delivery_time": (5, 10),
        "payment_terms": (0, 50)
    }

@pytest.fixture
def mock_seller(seller_constraints):
    seller = MagicMock()
    seller.constraints = seller_constraints
    # Create the full mock structure
    seller.ai_model = MagicMock()
    seller.ai_model.repository = MagicMock()
    seller.ai_model.repository.model_name = "test-model"
    return seller

@pytest.fixture
def mock_buyer(buyer_constraints):
    buyer = MagicMock()
    buyer.constraints = buyer_constraints
    # Create the full mock structure
    buyer.ai_model = MagicMock()
    buyer.ai_model.repository = MagicMock()
    buyer.ai_model.repository.model_name = "test-model"
    return buyer 