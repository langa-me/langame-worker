import unittest
from flask import Request
from main import slack_bot


class TestClient(unittest.TestCase):
    def test_slack(self):
        print(slack_bot(Request(environ={'REQUEST_METHOD': 'POST'})))
