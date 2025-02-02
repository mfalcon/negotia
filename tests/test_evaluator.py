import pytest
from main import NegotiationEvaluator

def test_evaluate_optimal_for_seller(seller_constraints, buyer_constraints):
    evaluator = NegotiationEvaluator(seller_constraints, buyer_constraints)
    terms = {
        "price": 1500,
        "delivery_time": 14,
        "payment_terms": 100
    }
    evaluation = evaluator.evaluate(terms)
    
    assert pytest.approx(evaluation["seller"]["average_score"]) == 100.0
    assert pytest.approx(evaluation["buyer"]["average_score"]) == 0.0

def test_evaluate_optimal_for_buyer(seller_constraints, buyer_constraints):
    evaluator = NegotiationEvaluator(seller_constraints, buyer_constraints)
    terms = {
        "price": 800,
        "delivery_time": 5,
        "payment_terms": 0
    }
    evaluation = evaluator.evaluate(terms)
    
    assert pytest.approx(evaluation["buyer"]["average_score"]) == 100.0
    assert pytest.approx(evaluation["seller"]["average_score"]) == 0.0

def test_evaluate_compromise(seller_constraints, buyer_constraints):
    evaluator = NegotiationEvaluator(seller_constraints, buyer_constraints)
    terms = {
        "price": 1100,
        "delivery_time": 10,
        "payment_terms": 50
    }
    evaluation = evaluator.evaluate(terms)
    
    assert 0 < evaluation["seller"]["average_score"] < 100
    assert 0 < evaluation["buyer"]["average_score"] < 100 