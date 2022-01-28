from random import randint
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
    return response["choices"][0]["text"].strip()


def local_completion(
    model: GPT2LMHeadModel,
    tokenizer: AutoTokenizer,
    prompt: str,
    deterministic: bool = False,
    use_gpu: bool = False,
) -> str:
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
