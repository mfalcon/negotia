import unittest
from main import NegotiationEvaluator

class TestNegotiationEvaluator(unittest.TestCase):
    def setUp(self):
        self.seller_constraints = {
            "price": (1000, 1500),
            "delivery_time": (7, 14),
            "payment_terms": (50, 100)
        }
        self.buyer_constraints = {
            "price": (800, 1200),
            "delivery_time": (5, 10),
            "payment_terms": (0, 50)
        }
        self.evaluator = NegotiationEvaluator(
            self.seller_constraints,
            self.buyer_constraints
        )

    def test_evaluate_optimal_for_seller(self):
        terms = {
            "price": 1500,
            "delivery_time": 14,
            "payment_terms": 100
        }
        evaluation = self.evaluator.evaluate(terms)
        
        # Verify seller got maximum scores
        self.assertAlmostEqual(evaluation["seller"]["average_score"], 100.0)
        
        # Verify buyer got minimum scores
        self.assertAlmostEqual(evaluation["buyer"]["average_score"], 0.0)

    def test_evaluate_optimal_for_buyer(self):
        terms = {
            "price": 800,
            "delivery_time": 5,
            "payment_terms": 0
        }
        evaluation = self.evaluator.evaluate(terms)
        
        # Verify buyer got maximum scores
        self.assertAlmostEqual(evaluation["buyer"]["average_score"], 100.0)
        
        # Verify seller got minimum scores
        self.assertAlmostEqual(evaluation["seller"]["average_score"], 0.0)

    def test_evaluate_compromise(self):
        terms = {
            "price": 1100,
            "delivery_time": 10,
            "payment_terms": 50
        }
        evaluation = self.evaluator.evaluate(terms)
        
        # Verify both parties got moderate scores
        self.assertGreater(evaluation["seller"]["average_score"], 0)
        self.assertLess(evaluation["seller"]["average_score"], 100)
        self.assertGreater(evaluation["buyer"]["average_score"], 0)
        self.assertLess(evaluation["buyer"]["average_score"], 100) 