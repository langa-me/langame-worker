import unittest
from .ava_client import get_starter

class TestClient(unittest.TestCase):
    def test_get_starter(self):
        response, error = get_starter(None, ["ice breaker"])
        print(response, error)
        self.assertIsNotNone(response)
        self.assertIsNone(error)
