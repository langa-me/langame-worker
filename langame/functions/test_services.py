import unittest
from .services import request_starter_for_service
import os


class TestServices(unittest.TestCase):
    def test_request_starter_for_service(self):
        responses = []
        for _ in range(3):
            response = request_starter_for_service(
                url=os.environ["GET_MEMES_URL"],
                api_key_id=os.environ["LANGAME_API_KEY_ID"],
                logger=None,
                topics=["porn"],
                quantity=1,
                fix_grammar=False,
                profanity_threshold="open",
            )
            responses.append(response)
        # Last response should have been rate limited
        print("foo")
        # self.assertEqual(responses[-1]["error"]["code"], 429)
