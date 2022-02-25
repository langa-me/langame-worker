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


class FinishReasonLengthException(Exception):
    pass


    

def is_base_openai_model(model: str) -> bool:
    """
    Returns whether the model is a fine-tuned model.
    :param model: Model name
    :return: True if fine-tuned model, False otherwise
    """
    return model in [
        "davinci",
        "curie",
        "ada",
        "babbage",
        "davinci-codex",
        "davinci-instruct-beta-v3",
    ]


def is_base_gooseai_model(model: str) -> bool:
    """
    Returns whether the model is a fine-tuned model.
    :param model: Model name
    :return: True if fine-tuned model, False otherwise
    """
    # "gpt" or "fairseq" in model
    return "gpt" in model or "fairseq" in model

def is_fine_tuned_openai(model: str) -> bool:
    """
    Returns whether the model is an OpenAI fine-tuned model.
    :param model: Model name
    :return: True if an OpenAI fine-tuned model, False otherwise
    """
    return not is_base_openai_model(model) and not is_base_gooseai_model(model)

def openai_completion(
    prompt: str,
    model: str = "davinci-codex",
    stop: List[str] = None,
    is_classification: bool = False,
    temperature: float = 1,
    max_tokens: int = 100,
    ignore_finish_reason: bool = False,
) -> str:
    """
    OpenAI completion
    :param prompt:
    :param model:
    :param stop:
    """
    is_gooseai = is_base_gooseai_model(model)
    is_openai_model = is_base_openai_model(model)
    openai.api_base = (
        "https://api.goose.ai/v1" if is_gooseai else "https://api.openai.com/v1"
    )
    openai.api_key = os.environ.get("GOOSEAI_KEY" if is_gooseai else "OPENAI_KEY")
    openai.organization = "" if is_gooseai else os.environ.get("OPENAI_ORG")
    response = (
        openai.Completion.create(
            engine=model if is_gooseai else "davinci-codex",
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=1,
            frequency_penalty=0.7,
            presence_penalty=0,
            stop=stop if stop else ["\n", "##"],
        )
        # If not gooseai and not default openai model, must be a fine tuned one
        if is_gooseai or is_openai_model
        else openai.Completion.create(
            model=model,
            prompt=prompt,
            temperature=0 if is_classification else temperature,
            max_tokens=max_tokens,
            top_p=1,
            frequency_penalty=0.7,
            presence_penalty=0,
            stop=stop if stop else ["\n", "##"],
        )
    )
    if (
        not ignore_finish_reason
        and response["choices"][0]["finish_reason"] == "length"
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
