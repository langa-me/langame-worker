import unittest
from main import conversation_starter
import re
import json
class TestConversationStarter(unittest.TestCase):
    def test_basic(self):
        response = conversation_starter(None)
        # assert that the response looks like this
        # {'output': "\n ('What is the craziest conversation you have had?', ['ice breaker']),"}
        jsonned = json.loads(response)
        self.assertTrue(jsonned['output'], re.compile(r".*([\"']+[\"']+).*"))
        # contains "ice breaker"
        self.assertTrue(jsonned['output'], re.compile(r".*ice breaker.*"))