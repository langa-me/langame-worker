from typing import List, Optional

import openai
from googleapiclient.discovery import build

from helpers import clean_text
from urllib.request import urlopen
from urllib.error import URLError
from bs4 import BeautifulSoup

class OpenAIClient:
    def __init__(self, api_token, google_search_api_token, google_search_cse_id, engine="davinci"):
        assert api_token, "You must give an OpenAI API token"
        assert google_search_api_token, "You must give a Google Search API token"
        assert google_search_cse_id, "You must give a Google Search CSE ID"
        openai.api_key = api_token
        self._engine = engine
        self._google_search_cse_id = google_search_cse_id
        self._google_search = build(
            "customsearch", "v1", developerKey=google_search_api_token).cse()

    def call_completion(self,
                        prompt: str,
                        stop: Optional[List[str]] = ["\"\n", "\n\n\n", "\n\""],
                        max_tokens: int = 100,
                        max_tries: int = 5,
                        ):
        """

        :param max_tries:
        :param max_tokens:
        :param stop:
        :param prompt:
        :return:
        """

        tries = 0
        print(f"call_completion with prompt {prompt}")
        while tries < max_tries:
            print(f"try n°{tries}/{max_tries}")
            response = openai.Completion.create(
                engine="davinci",
                prompt=prompt,
                temperature=0.7,
                max_tokens=max_tokens,
                top_p=1,
                frequency_penalty=1,
                presence_penalty=1,
                stop=stop,
                best_of=1,
            )
            choices = response.get("choices")
            print(response)
            if not choices \
                    or not isinstance(choices, list) \
                    or len(choices) == 0 \
                    or not choices[0].get("text"):
                tries += 1
                continue
            response = choices[0].get("text")
            response = clean_text(response)
            return response
        return None

    def openai_description(self, topic: str) -> Optional[str]:
        """
        returns openai generated description or None
        :param topic:
        :return:
        """

        description = f"""Below is a long paragraph which describes the topic of '{topic}' as following:"""

        print(f"calling openai_description with prompt {description}")
        description = self.call_completion(
            description, stop=["\"\n", "\n\n\n"])
        return description

    def wikipedia_description(self, topic: str) -> Optional[str]:
        """
        returns wikipedia description or None
        :param topic:
        :return:
        """
        search = self._google_search\
            .list(q=f"wikipedia {topic}", cx=self._google_search_cse_id, num=1)\
            .execute()
        items = search.get("items")
        if not items or len(items) == 0 or not items[0].get("link"):
            return None

        try:
            html = urlopen(items[0].get("link"))
        except URLError:
            # Rate limited
            return None
        soup = BeautifulSoup(html, "html.parser")
        short_description = soup.find("div", {"class": "shortdescription"})
        if not short_description:
            return None
        return short_description.text
