import os
import json
import unittest
import requests
class TestMain(unittest.TestCase):
    def test_get_conversation_starter(self):
        headers = {
            "Content-Type": "application/json",
            "X-Api-Key": os.environ["DEV_LANGAME_API_KEY"],
        }
        data = {
            "topics": ["ice breaker"],
            "limit": 1,
        }
        responses = []
        for _ in range(3):
            response = requests.post(
                "https://dapi.langa.me/v1/conversation/starter",
                headers=headers,
                data=json.dumps(data),
            )
            
            responses.append(response)
        # Last response should have been rate limited
        self.assertEqual(responses[-1].status_code, 429)