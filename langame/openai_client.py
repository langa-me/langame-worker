from typing import List, Optional

import openai
from googleapiclient.discovery import build

from langame.helpers import clean_text
from urllib.request import urlopen
from urllib.error import URLError
from bs4 import BeautifulSoup
# from langame.protobuf.langame_pb2 import Tag


class OpenAIClient:
    def __init__(self, api_token, organization, google_search_api_token, google_search_cse_id, engine="davinci"):
        assert api_token, "You must give an OpenAI API token"
        assert api_token, "You must give an OpenAI organizarion"
        assert google_search_api_token, "You must give a Google Search API token"
        assert google_search_cse_id, "You must give a Google Search CSE ID"
        openai.api_key = api_token
        openai.organization = organization
        self._engine = engine
        self._google_search_cse_id = google_search_cse_id
        self._google_search = build(
            "customsearch", "v1", developerKey=google_search_api_token).cse()

    def call_completion(self,
                        prompt: str,
<<<<<<< HEAD:openai_client.py
                        parameters,
=======
                        parameters: any,
>>>>>>> 62810a0a4c02d92c3d66a455a763e27d87f3ddd9:langame/openai_client.py
                        ):
        """

        :param parameters:
        :param prompt:
        :return:
        """

        response = openai.Completion.create(
            engine=parameters["model"] if parameters["model"] is not None else "davinci",
            prompt=prompt,
            temperature=parameters["temperature"] if parameters.get("temperature") is not None else 1,
            max_tokens=parameters["maxTokens"] if parameters.get("maxTokens") is not None else 100,
            top_p=parameters["topP"] if parameters.get("topP") is not None else 1,
            frequency_penalty=parameters["frequencyPenalty"] if parameters.get("frequencyPenalty") is not None else 0,
            presence_penalty=parameters["presencePenalty"] if parameters.get("presencePenalty") is not None else 0,
            stop=parameters["stop"] if parameters.get("stop") is not None else [],
            best_of=1,
        )
        choices = response.get("choices")
        response = choices[0].get("text")
        # TODO: return None if finish_reason is length
        # https://beta.openai.com/docs/api-reference/completions/create
        response = clean_text(response)
        return response


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

    def get_fine_tune(self, dataset_name):
        return [e for e in openai.FineTune.list()["data"] if e["training_files"][0]["filename"] == dataset_name][0]