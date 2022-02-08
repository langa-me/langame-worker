from random import randint
from typing import List, Optional
import openai
from enum import Enum
import os
import json
import requests
from transformers import GPT2LMHeadModel, AutoTokenizer, set_seed


class CompletionType(Enum):
    openai_api = 1
    local = 2
    huggingface_api = 3
    gooseai = 4


class FinishReasonLengthException(Exception):
    pass


def openai_completion(prompt: str, 
    fine_tuned_model: Optional[str] = None,
    stop: List[str] = None) -> str:
    """
    OpenAI completion
    :param prompt:
    :param fine_tuned_model:
    :param stop:
    """
    response = openai.Completion.create(
        engine="davinci-codex",
        prompt=prompt,
        temperature=1,
        max_tokens=200,
        top_p=1,
        frequency_penalty=0.7,
        presence_penalty=0,
        stop=stop if stop else ["\n"],
    ) if not fine_tuned_model else openai.Completion.create(
        model=fine_tuned_model,
        prompt=prompt,
        temperature=0,
        max_tokens=100,
        stop=stop if stop else ["\n"],
    )
    if (
        response["choices"][0]["finish_reason"] == "length"
        or not response["choices"][0]["text"]
    ):
        raise FinishReasonLengthException()
    if "error" in response:
        raise Exception(response["error"])
    return str(response["choices"][0]["text"].strip())


def local_completion(
    model: GPT2LMHeadModel,
    tokenizer: AutoTokenizer,
    prompt: str,
    deterministic: bool = False,
    use_gpu: bool = False,
) -> str:
    """
    Local completion
    """
    device = "cuda:0" if use_gpu else "cpu"
    set_seed(42 if deterministic else randint(0, 100))
    processed_prompt = prompt.strip()
    encoded_input = tokenizer(processed_prompt, return_tensors="pt").to(device)
    outputs = model.generate(
        **encoded_input,
        return_dict_in_generate=True,
        eos_token_id=198,  # line break
        max_length=(len(prompt) / 5) + 300,
        num_return_sequences=1,
        return_text=False,
        return_full_text=False,
        do_sample=True,
        top_k=50,
        top_p=0.95,
        device=device,
    )
    outputs_as_string = tokenizer.decode(outputs["sequences"].tolist()[0])
    return outputs_as_string.replace(
        processed_prompt, ""
    ).strip()  # TODO: return_text doesn't work for some reason


def huggingface_api_completion(prompt: str) -> str:
    """
    Huggingface API completion
    """
    API_URL = "https://api-inference.huggingface.co/models/Langame/gpt2-starter-2"
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
                "end_sequence": "\n",
            },
            "options": {
                "wait_for_model": True,
                "use_cache": False,  # TODO: should be in public api args
            },
        }
    )
    response = requests.request("POST", API_URL, headers=headers, data=data)
    data = json.loads(response.content.decode("utf-8"))
    completions = data[0]["generated_text"].strip()
    return completions


def gooseai_completion(prompt: str) -> str:
    """
    https://goose.ai/docs/api/completions
    """
    API_URL = "https://api.goose.ai/v1/engines/gpt-neo-20b/completions"
    headers = {"Authorization": f"Bearer {os.environ.get('GOOSEAI_KEY')}"}
    data = json.dumps(
        {
            "prompt": prompt,
            "stop": ["\n"],
            "presence_penalty": 0,
            "frequency_penalty": 0.7,
            "max_tokens": 100,
        }
    )
    response = requests.request("POST", API_URL, headers=headers, data=data)
    data = json.loads(response.content.decode("utf-8"))
    if "error" in data:
        raise Exception(data["error"])
    if (
        data["choices"][0]["finish_reason"] == "length"
        or not data["choices"][0]["text"]
    ):
        raise FinishReasonLengthException()
    return data["choices"][0]["text"].strip()

