from langame.logic import (
    generate_conversation_starter,
)
from langame.completion import CompletionType, build_prompt
from langame.profanity import (
    ProfanityThreshold, ProfaneException
)
from firebase_admin import credentials, firestore
import firebase_admin
import unittest
import openai
import os
import time
from transformers import AutoConfig, AutoTokenizer, GPT2LMHeadModel

class TestLogic(unittest.TestCase):
    def setUp(self) -> None:
        openai.api_key = os.environ["OPENAI_KEY"]
        openai.organization = os.environ["OPENAI_ORG"]
        cred = credentials.Certificate("./svc.dev.json")
        firebase_admin.initialize_app(cred)
        firestore_client = firestore.client()
        self.memes = [
            (e.id, e.to_dict()) for e in firestore_client.collection("memes").stream()
        ]
        return super().setUp()

    def test_build_prompt(self):
        
        topics = ["philosophy"]
        prompt = build_prompt(self.memes, topics)
        assert prompt is not None
        # Check that prompt end with "\nphilosophy ###"
        assert prompt.endswith("\nphilosophy ###")

        # Now with unknown topics
        topics = ["foo", "bar"]
        prompt = build_prompt(self.memes, topics)
        assert prompt is not None
        # Check that prompt end with "\nfoo,bar ###"
        assert prompt.endswith("\nfoo,bar ###")

    def test_generate_conversation_starter_openai(self):
        start = time.time()
        conversation_starter = generate_conversation_starter(self.memes, ["philosophy"])
        elapsed_seconds = str(time.time() - start)
        print(f"Elapsed seconds: {elapsed_seconds}")
        print(conversation_starter)

    def test_generate_conversation_starter_local(self):
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

        conversation_starter = generate_conversation_starter(
            conversation_starter_examples=self.memes,
            topics=["philosophy"],
            completion_type=CompletionType.local,
            prompt_rows=5,
            model=model,
            tokenizer=tokenizer,
            use_gpu=use_gpu,
        )
        elapsed_seconds = str(time.time() - start)
        print(f"Elapsed seconds: {elapsed_seconds}")
        print(conversation_starter)


    def test_generate_conversation_starter_huggingface_api(self):
        start = time.time()
        conversation_starter = generate_conversation_starter(
            conversation_starter_examples=self.memes,
            topics=["philosophy"],
            completion_type=CompletionType.huggingface_api,
            prompt_rows=5,
        )
        elapsed_seconds = str(time.time() - start)
        print(f"Elapsed seconds: {elapsed_seconds}")
        print(conversation_starter)

    def test_generate_conversation_starter_profane(self):
        with self.assertRaises(ProfaneException):
            conversation_starter = generate_conversation_starter(
                self.memes, ["god"], profanity_threshold=ProfanityThreshold.strict
            )
            # Non deterministic tests, don't run in CI?
            self.assertEqual(conversation_starter, None)
        conversation_starter = generate_conversation_starter(
            self.memes, ["god"], profanity_threshold=ProfanityThreshold.tolerant
        )
        assert conversation_starter is not None
        conversation_starter = generate_conversation_starter(
            self.memes, ["god"], profanity_threshold=ProfanityThreshold.open
        )
        assert conversation_starter is not None
