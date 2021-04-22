from typing import List, Optional

import openai
from googleapiclient.discovery import build

from helpers import clean_text, get_synonyms, get_related_topics, get_suggestions
from langame.protobuf.langame_pb2 import Question
from bs4 import BeautifulSoup
from urllib.request import urlopen

class OpenAIClient:
    def __init__(self, api_token, google_search_api_token, google_search_cse_id, engine="davinci"):
        assert api_token, "You must give an OpenAI API token"
        assert google_search_api_token, "You must give a Google Search API token"
        assert google_search_cse_id, "You must give a Google Search CSE ID"
        openai.api_key = api_token
        self._engine = engine
        self._google_search_cse_id = google_search_cse_id
        self._google_search = build("customsearch", "v1", developerKey=google_search_api_token).cse()

    def call_completion(self, prompt: str, stop: Optional[List[str]] = None, max_tokens: int = 20):
        """

        :param max_tokens:
        :param stop:
        :param prompt:
        :return:
        """
        response = openai.Completion.create(
            engine="davinci",
            prompt=prompt,
            temperature=0.7,
            max_tokens=max_tokens,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0.1,
            stop=stop,
            best_of=1,
        )
        choices = response.get("choices")
        if not choices or not isinstance(choices, list) or len(choices) == 0:
            return None
        text = choices[0].get("text")
        if text:
            text = clean_text(text)
        return text

    def wikipedia_description(self, search_term: str) -> Optional[str]:
        """
        returns wikipedia description or None
        :param search_term:
        :return:
        """
        search = self._google_search\
            .list(q=f"wikipedia {search_term}", cx=self._google_search_cse_id, num=1)\
            .execute()
        items = search.get("items")
        if not items or len(items) == 0 or not items[0].get("link"):
            return None

        html = urlopen(items[0].get("link"))
        soup = BeautifulSoup(html, "html.parser")
        short_description = soup.find("div", {"class": "shortdescription"})
        if not short_description:
            return None
        return short_description.text

    def question_generation(self,
                            topic: str,
                            wikipedia_description: bool = True,
                            self_contexts: int = 0,
                            synonymous_contexts: int = 0,
                            related_contexts: int = 0,
                            suggested_contexts: int = 0,
                            ) -> Optional[Question]:
        """
        Generate a question using OpenAI API
        :param wikipedia_description: whether to add Wikipedia description
        :param self_contexts: generate context using generated question
        :param synonymous_contexts: generate context using topic synonym
        :param related_contexts: generate context using related topic
        :param suggested_contexts: generate context using suggestions
        :param topic:
        :return:
        """
        basic_stops = ["?", "\\n", "<|endoftext|>"]

        def prompt(p: str):
            return f"What is the most interesting question in {p}?"

        def prompt_synonymous(p: str):
            return f"I will present {p} as the following:"

        question_text = self.call_completion(prompt(topic), stop=basic_stops)

        if not question_text:
            return None

        q = Question()
        q.content = question_text + "?"
        if wikipedia_description:
            text = self.wikipedia_description(topic)
            if text:
                q.contexts.append(text)
        for _ in range(self_contexts):
            text = self.call_completion(prompt(topic) + q.content, stop=basic_stops)
            if not text:
                continue
            q.contexts.append(text)

        if synonymous_contexts > 0:
            synonyms = get_synonyms(topic, synonymous_contexts)
            for synonym in synonyms:
                if not synonym.get("synonym"):
                    continue
                text = self.call_completion(
                    prompt_synonymous(synonym.get("synonym")),
                    stop=basic_stops,
                    max_tokens=40,
                )
                if not text:
                    continue
                q.contexts.append(text)

        if related_contexts > 0:
            related_topics = get_related_topics(topic, related_contexts)
            for related_topic in related_topics:
                if not related_topic.get("topic"):
                    continue
                text = self.call_completion(
                    prompt_synonymous(related_topic.get("topic")),
                    stop=basic_stops,
                    max_tokens=40,
                )
                if not text:
                    continue
                q.contexts.append(text)

        if suggested_contexts > 0:
            suggestions = get_suggestions(topic, suggested_contexts)
            for suggestion in suggestions:
                if not suggestion:
                    continue
                text = self.call_completion(
                    prompt_synonymous(suggestion),
                    stop=basic_stops,
                    max_tokens=40,
                )
                if not text:
                    continue
                q.contexts.append(text)

        return q
