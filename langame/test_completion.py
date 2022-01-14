from langame.completion import (
    CompletionType,
    build_prompt,
    openai_completion,
    local_completion,
    huggingface_api_completion,
)
from firebase_admin import credentials, firestore
import firebase_admin
import unittest
import openai
import os
import time


class TestLogic(unittest.TestCase):
    def setUp(self) -> None:
        openai.api_key = os.environ["OPENAI_KEY"]
        openai.organization = os.environ["OPENAI_ORG"]
        cred = credentials.Certificate("./svc.dev.json")
        firebase_admin.initialize_app(cred)
        return super().setUp()

    def test_build_prompt(self):
        firestore_client = firestore.client()
        memes = [
            (e.id, e.to_dict()) for e in firestore_client.collection("memes").stream()
        ]
        topics = ["philosophy"]
        prompt = build_prompt(memes, topics)
        assert prompt is not None
        # Check that prompt end with "\nphilosophy ###"
        assert prompt.endswith("\nphilosophy ###")

        # Now with unknown topics
        topics = ["foo", "bar"]
        prompt = build_prompt(memes, topics)
        assert prompt is not None
        # Check that prompt end with "\nfoo,bar ###"
        assert prompt.endswith("\nfoo,bar ###")

    def test_openai_completion(self):
        response = openai_completion("The color of the white horse of Henry IV is")
        assert response is not None

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
            model, tokenizer, "future of humanity ###", deterministic=False, use_gpu=use_gpu
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

    def test_zz(self):
        print("z")
