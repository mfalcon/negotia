import unittest
import os
from unittest.mock import MagicMock, patch
from main import NegotiationLogger, AINegotiator

class TestNegotiationLogger(unittest.TestCase):
    def setUp(self):
        # Create mock negotiators
        self.seller = MagicMock(spec=AINegotiator)
        self.seller.constraints = {
            "price": (1000, 1500),
            "delivery_time": (7, 14),
            "payment_terms": (50, 100)
        }
        self.seller.ai_model.repository.model_name = "test-model"
        
        self.buyer = MagicMock(spec=AINegotiator)
        self.buyer.constraints = {
            "price": (800, 1200),
            "delivery_time": (5, 10),
            "payment_terms": (0, 50)
        }
        self.buyer.ai_model.repository.model_name = "test-model"

    def tearDown(self):
        # Clean up any log files created during tests
        for file in os.listdir():
            if file.startswith("negotiation_") and file.endswith(".txt"):
                os.remove(file)

    def test_logger_initialization(self):
        logger = NegotiationLogger(self.seller, self.buyer)
        self.assertTrue(os.path.exists(logger.filename))

    def test_log_initial_terms(self):
        logger = NegotiationLogger(self.seller, self.buyer)
        terms = {
            "price": 1100,
            "delivery_time": 10,
            "payment_terms": 50
        }
        logger.log_initial_terms(terms)
        
        with open(logger.filename, 'r') as f:
            content = f.read()
            self.assertIn("Initial terms:", content)
            self.assertIn("$1100", content)

    def test_log_round(self):
        logger = NegotiationLogger(self.seller, self.buyer)
        logger.log_round(1)
        
        with open(logger.filename, 'r') as f:
            content = f.read()
            self.assertIn("Round 1", content)

    def test_log_deal_reached(self):
        logger = NegotiationLogger(self.seller, self.buyer)
        terms = {
            "price": 1100,
            "delivery_time": 10,
            "payment_terms": 50
        }
        logger.log_deal_reached(
            "Seller",
            terms,
            self.seller.constraints,
            self.buyer.constraints
        )
        
        with open(logger.filename, 'r') as f:
            content = f.read()
            self.assertIn("Deal reached", content)
            self.assertIn("Final Evaluation", content) 