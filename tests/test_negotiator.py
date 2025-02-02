import unittest
from main import AINegotiator

class TestAINegotiator(unittest.TestCase):
    def setUp(self):
        self.constraints = {
            "price": (1000, 1500),
            "delivery_time": (7, 14),
            "payment_terms": (50, 100)
        }
        self.negotiator = AINegotiator(
            name="Test Seller",
            is_seller=True,
            constraints=self.constraints,
            repository_type="ollama",
            model_name="test-model"
        )

    def test_extract_terms(self):
        # Test price extraction
        response = "I propose a price of $1200"
        terms = self.negotiator._extract_terms(response)
        self.assertEqual(terms.get("price"), 1200)

        # Test delivery time extraction
        response = "Delivery in 10 days"
        terms = self.negotiator._extract_terms(response)
        self.assertEqual(terms.get("delivery_time"), 10)

        # Test payment terms extraction
        response = "75% upfront payment"
        terms = self.negotiator._extract_terms(response)
        self.assertEqual(terms.get("payment_terms"), 75)

    def test_extract_acceptance(self):
        # Test positive acceptance
        response = "I accept these terms"
        self.assertTrue(self.negotiator._extract_acceptance(response))

        # Test negative case
        response = "Let me propose different terms"
        self.assertFalse(self.negotiator._extract_acceptance(response))

        # Test rejection
        response = "I don't accept these terms"
        self.assertFalse(self.negotiator._extract_acceptance(response))

    def test_create_negotiation_prompt(self):
        current_terms = {
            "price": 1200,
            "delivery_time": 10,
            "payment_terms": 75
        }
        prompt = self.negotiator._create_negotiation_prompt(current_terms, 5)
        
        # Verify prompt contains key elements
        self.assertIn("Current situation:", prompt)
        self.assertIn("$1200", prompt)
        self.assertIn("10 days", prompt)
        self.assertIn("75%", prompt) 