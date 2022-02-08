from langame.completion import (
    openai_completion,
    local_completion,
    huggingface_api_completion,
    gooseai_completion,
)
from firebase_admin import credentials
import firebase_admin
import unittest
import openai
import os
import time


class TestCompletion(unittest.TestCase):
    def setUp(self) -> None:
        openai.api_key = os.environ["OPENAI_KEY"]
        openai.organization = os.environ["OPENAI_ORG"]
        cred = credentials.Certificate("./svc.dev.json")
        firebase_admin.initialize_app(cred)
        return super().setUp()

    def test_openai_completion(self):
        response = openai_completion("The color of the white horse of Henry IV is")
        assert response is not None

    def test_openai_completion_fine_tune(self):
        classification = openai_completion(
            prompt=f"ice breaker ### foo bar? ~~~",
            fine_tuned_model="ada:ft-personal-2022-02-08-19-57-38",
        )
        assert classification is not None
        assert classification == "0"

    def test_custom_completion(self):
        from transformers import AutoConfig, AutoTokenizer, GPT2LMHeadModel

        model_name_or_path = "Langame/gpt2-starter-2"
        token = os.environ.get("HUGGINGFACE_TOKEN")
        use_gpu = False
        device = "cuda:0" if use_gpu else "cpu"
        config = AutoConfig.from_pretrained(model_name_or_path, use_auth_token=token)
        model = GPT2LMHeadModel.from_pretrained(
            model_name_or_path, config=config, use_auth_token=token
        ).to(device)
        tokenizer = AutoTokenizer.from_pretrained(
            model_name_or_path, config=config, use_auth_token=token
        )
        start = time.time()
        response = local_completion(
            model,
            tokenizer,
            "future of humanity ###",
            deterministic=False,
            use_gpu=use_gpu,
        )
        assert response is not None
        elapsed_seconds = str(time.time() - start)
        print(f"Elapsed seconds: {elapsed_seconds}")
        print(response)

    def test_huggingface_api_completion(self):
        start = time.time()
        response = huggingface_api_completion("ice breaker ###")
        assert response is not None
        elapsed_seconds = str(time.time() - start)
        print(f"Elapsed seconds: {elapsed_seconds}")
        print(response)

    def test_gooseai_completion(self):
        start = time.time()
        response = gooseai_completion("- foo\n- bar\n-")
        assert response is not None
        elapsed_seconds = str(time.time() - start)
        print(f"Elapsed seconds: {elapsed_seconds}")
        print(response)