import pytest
import os
from main import NegotiationLogger

def test_logger_initialization(mock_seller, mock_buyer):
    logger = NegotiationLogger(mock_seller, mock_buyer)
    assert os.path.exists(logger.filename)
    os.remove(logger.filename)  # Cleanup

def test_log_initial_terms(mock_seller, mock_buyer):
    logger = NegotiationLogger(mock_seller, mock_buyer)
    terms = {
        "price": 1100,
        "delivery_time": 10,
        "payment_terms": 50
    }
    logger.log_initial_terms(terms)
    
    with open(logger.filename, 'r') as f:
        content = f.read()
        assert "Initial terms:" in content
        assert "$1100" in content
    os.remove(logger.filename)  # Cleanup

def test_log_round(mock_seller, mock_buyer):
    logger = NegotiationLogger(mock_seller, mock_buyer)
    logger.log_round(1)
    
    with open(logger.filename, 'r') as f:
        content = f.read()
        assert "Round 1" in content
    os.remove(logger.filename)  # Cleanup

def test_log_deal_reached(mock_seller, mock_buyer):
    logger = NegotiationLogger(mock_seller, mock_buyer)
    terms = {
        "price": 1100,
        "delivery_time": 10,
        "payment_terms": 50
    }
    logger.log_deal_reached(
        "Seller",
        terms,
        mock_seller.constraints,
        mock_buyer.constraints
    )
    
    with open(logger.filename, 'r') as f:
        content = f.read()
        assert "Deal reached" in content
        assert "Final Evaluation" in content
    os.remove(logger.filename)  # Cleanup 