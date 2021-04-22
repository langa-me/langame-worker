import os
import unittest
from typing import Optional

from langame.protobuf.langame_pb2 import Question
from langame_client import LangameClient
from openai_client import OpenAIClient


class TestOpenAIClient(unittest.TestCase):
    def setUp(self):
        self._open_ai_client = OpenAIClient(os.environ['OPEN_AI_TOKEN'])

    def test_question_generation(self):
        qs_ts = self._open_ai_client.question_generation(
            "philosophy",
            self_contexts=1,
            synonymous_contexts=1,
            related_contexts=1,
            suggested_contexts=1,
        )
        print(qs_ts)


if __name__ == '__main__':
    unittest.main()
