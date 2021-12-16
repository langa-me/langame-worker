from random import choices, randint
from typing import Any, List
from langame.arrays import intersection
import openai
from enum import Enum
import os
import json
import requests
from transformers import pipeline, set_seed, TextGenerationPipeline

class CompletionType(Enum):
    openai_api = 1
    local = 2
    huggingface_api = 3


class FinishReasonLengthException(Exception):
    pass


def build_prompt(
    conversation_starter_examples: List[Any], topics: List[str], prompt_rows: int = 60,
) -> str:
    """
    Build a prompt for a GPT-like model based on a list of conversation starters.
    :param conversation_starter_examples: The list of conversation starters.
    :param topics: The list of topics.
    :param prompt_rows: The number of rows in the prompt.
    :return: prompt
    """
    random_conversation_starters = choices(conversation_starter_examples, k=500)
    found_conversation_starters = [
        f"{','.join(e[1]['topics'])} ### {e[1]['content']}"
        for e in random_conversation_starters
        if len(intersection(e[1]["topics"], topics)) > 0
    ]

    prompt = (
        (
            "\n".join(
                [
                    f"{','.join(e[1]['topics'])} ### {e[1]['content']}"
                    for e in random_conversation_starters
                ][0:prompt_rows]
            )
        )
        if not found_conversation_starters
        else "\n".join(found_conversation_starters[0:prompt_rows])
    )

    return prompt + "\n" + ",".join(topics) + " ###"


def openai_completion(prompt: str, stop=["\n"]):
    response = openai.Completion.create(
        engine="davinci-codex",
        prompt=prompt,
        temperature=1,
        max_tokens=200,
        top_p=1,
        frequency_penalty=0.7,
        presence_penalty=0,
        stop=stop,
    )
    if (
        response["choices"][0]["finish_reason"] == "length"
        or not response["choices"][0]["text"]
    ):
        raise FinishReasonLengthException()
    return response["choices"][0]["text"]


def local_completion(prompt: str, deterministic: bool = False) -> str:
    generator: TextGenerationPipeline = pipeline(
        "text-generation",
        model="Langame/gpt2-starter",
        tokenizer="gpt2",
        use_auth_token=os.environ.get("HUGGINGFACE_TOKEN"),
    )
    set_seed(42 if deterministic else randint(0, 100))
    gen = generator(
        prompt,
        max_length=(len(prompt) / 5) + 100,
        num_return_sequences=1,
        return_text=False,
        return_full_text=False,
        do_sample=True,
        top_k=50,
        top_p=0.95,
    )[0]
    completions = gen["generated_text"].split("\n")[0]
    return completions


def huggingface_api_completion(prompt: str) -> str:
    API_URL = "https://api-inference.huggingface.co/models/Langame/gpt2-starter"
    headers = {"Authorization": f"Bearer {os.environ.get('HUGGINGFACE_KEY')}"}

    data = json.dumps(
        {
            "inputs": prompt,
            "parameters": {
                "max_length": round(len(prompt) / 5) + 100,
                "num_return_sequences": 1,
                "return_text": False,
                "return_full_text": False,
                "do_sample": True,
                "top_k": 50,
                "top_p": 0.95,
            },
            "options": {"wait_for_model": True,},
        }
    )
    response = requests.request("POST", API_URL, headers=headers, data=data)
    data = json.loads(response.content.decode("utf-8"))
    completions = data[0]["generated_text"].split("\n")[0]
    return completions
