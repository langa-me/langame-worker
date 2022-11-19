import os
import json
import unittest
import requests


class TestMain(unittest.TestCase):
    # pylint: disable=missing-docstring
    def test_get_conversation_collection(self):
        headers = {
            "Content-Type": "application/json",
            "X-Api-Key": os.environ["LANGAME_API_KEY"],
        }
        # pylint: disable=missing-timeout
        response = requests.post(
            "http://localhost:8080/conversation/collection",
            headers=headers,
        )

        self.assertEqual(response.status_code, 200)
