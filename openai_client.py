import json
from typing import List, Optional

import requests
import os
import openai

from langame.protobuf.langame_pb2 import Question


class OpenAIClient:
    def __init__(self, api_token, engine="davinci"):
        openai.api_key = api_token
        self._engine = engine

    def question_generation(self, topic: str) -> Optional[Question]:
        """
        Generate a question using OpenAI API
        :param topic:
        :return:
        """
        response = openai.Completion.create(
            engine="davinci",
            prompt=f"What are the hottest questions in ${topic} nowadays?\n1.",
            temperature=0.7,
            max_tokens=20,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0.1
        )
        choices = response.get("choices")
        if not choices or not isinstance(choices, list) or len(choices) == 0:
            return None

        text = choices[0].get("text")

        if not text or "?" not in text:
            return None

        q = Question()
        q.content = text.split("?")[0]+"?"
        q.content = q.content.lstrip()
        q.content = q.content.rstrip()
        return q
