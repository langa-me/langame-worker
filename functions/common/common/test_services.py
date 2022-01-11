import unittest
from .services import request_starter_for_service
import os
class TestServices(unittest.TestCase):
    def test_request_starter_for_service(self):
        responses = []
        for _ in range(3):
            response = request_starter_for_service(
                api_key_id=os.environ["DEV_LANGAME_API_KEY_ID"],
                logger=None,
                topics=["ice breaker"],
                quantity=1,
            )
            responses.append(response)
        # Last response should have been rate limited
        self.assertEqual(responses[-1]["error"]["code"], 429)