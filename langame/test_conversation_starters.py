from langame.conversation_starters import (
    get_existing_conversation_starters,
    generate_conversation_starter,
)
from langame.completion import CompletionType
from langame.profanity import ProfaneException, ProfanityThreshold
from langame.quality import is_garbage
from firebase_admin import credentials, firestore
import firebase_admin
import unittest
import openai
import os
import numpy as np
from transformers import GPT2LMHeadModel, AutoTokenizer
import time


class TestConversationStarters(unittest.TestCase):
    def setUp(self) -> None:
        openai.api_key = os.environ["OPENAI_KEY"]
        openai.organization = os.environ["OPENAI_ORG"]
        cred = credentials.Certificate("./svc.prod.json")
        firebase_admin.initialize_app(cred)
        return super().setUp()

    def basic_assertions(self, conversation_starters, index, limit):
        # index should not be None then
        self.assertIsNotNone(index)
        # conversation_starters should be a list
        self.assertIsInstance(conversation_starters, list)
        # conversation_starters should not be empty
        self.assertTrue(len(conversation_starters) > 0)
        # should be close to length "limit" (potentially less because of garbage)
        self.assertLess(len(conversation_starters), limit)
        # elements should be a tuple of (id, dict)
        self.assertIsInstance(conversation_starters[0], tuple)
        # all dicts should contains the key "content" and "topics"
        for e in conversation_starters:
            self.assertIn("content", e[1])
            self.assertIn("topics", e[1])
        # should not contain garbage
        for e in conversation_starters:
            self.assertFalse(is_garbage(e[1]))

    def test_get_existing_conversation_starters_no_embeddings(self):
        firestore_client = firestore.client()
        conversation_starters, index, _ = get_existing_conversation_starters(
            firestore_client,
            embeddings=False,
            limit=20,
        )
        self.basic_assertions(conversation_starters, index, 21)

    def test_get_existing_conversation_starters_embeddings(self):
        firestore_client = firestore.client()
        conversation_starters, index, _ = get_existing_conversation_starters(
            firestore_client,
            embeddings=True,
            limit=3,
        )
        self.basic_assertions(conversation_starters, index, 4)

        # directories "embeddings" and "indexes" should have been created
        self.assertTrue(os.path.isdir("./embeddings"))
        self.assertTrue(os.path.isdir("./indexes"))

    def test_get_existing_conversation_starters_rebuild_embeddings(self):
        firestore_client = firestore.client()
        (
            conversation_starters,
            index,
            sentence_embeddings_model,
        ) = get_existing_conversation_starters(
            firestore_client,
            embeddings=True,
            limit=3,
            rebuild_embeddings=True,
        )
        self.basic_assertions(conversation_starters, index, 4)
        query = sentence_embeddings_model.encode("immortality", show_progress_bar=False)
        _, I = index.search(np.array([query]), 20)
        memes = [conversation_starters[i][1] for i in I[0]]
        self.assertTrue(len(memes) > 0)

    def test_generate_conversation_starter_openai(self):
        firestore_client = firestore.client()
        conversation_starters, index, _ = get_existing_conversation_starters(
            firestore_client,
            embeddings=True,
            limit=200,
            rebuild_embeddings=False,
        )
        start = time.time()
        conversation_starter = generate_conversation_starter(
            index=index,
            conversation_starter_examples=conversation_starters,
            topics=["philosophy"],
        )
        elapsed_seconds = str(time.time() - start)
        print(f"Elapsed seconds: {elapsed_seconds}")
        print(conversation_starter)

    def test_generate_conversation_starter_openai_new_topic(self):
        firestore_client = firestore.client()
        conversation_starters, index, _ = get_existing_conversation_starters(
            firestore_client,
            embeddings=True,
            limit=4000,
            rebuild_embeddings=False,
        )
        start = time.time()
        conversation_starter = generate_conversation_starter(
            index=index,
            conversation_starter_examples=conversation_starters,
            topics=["monkey"],
        )
        elapsed_seconds = str(time.time() - start)
        print(f"Elapsed seconds: {elapsed_seconds}")
        print(conversation_starter)

    def test_generate_conversation_starter_openai_with_new_embeddings(self):
        firestore_client = firestore.client()
        (
            conversation_starters,
            index,
            sentence_embeddings_model,
        ) = get_existing_conversation_starters(
            firestore_client,
            embeddings=True,
            limit=200,
            rebuild_embeddings=True,
        )
        start = time.time()
        conversation_starter = generate_conversation_starter(
            index=index,
            conversation_starter_examples=conversation_starters,
            topics=["monkey"],
            sentence_embeddings_model=sentence_embeddings_model,
        )
        elapsed_seconds = str(time.time() - start)
        print(f"Elapsed seconds: {elapsed_seconds}")
        print(conversation_starter)

    def test_generate_conversation_starter_local(self):
        model_name_or_path = "Langame/distilgpt2-starter"
        token = os.environ.get("HUGGINGFACE_TOKEN")
        use_gpu = False
        device = "cuda:0" if use_gpu else "cpu"
        model = GPT2LMHeadModel.from_pretrained(
            model_name_or_path, use_auth_token=token
        ).to(device)
        tokenizer = AutoTokenizer.from_pretrained(
            model_name_or_path, use_auth_token=token
        )
        firestore_client = firestore.client()
        conversation_starters, index, _ = get_existing_conversation_starters(
            firestore_client,
            embeddings=True,
            limit=4000,
            rebuild_embeddings=False,
        )
        start = time.time()

        conversation_starter = generate_conversation_starter(
            index=index,
            conversation_starter_examples=conversation_starters,
            topics=["monkey"],
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
        firestore_client = firestore.client()
        conversation_starters, index, _ = get_existing_conversation_starters(
            firestore_client,
            embeddings=True,
            limit=4000,
            rebuild_embeddings=False,
        )
        start = time.time()

        conversation_starter = generate_conversation_starter(
            index=index,
            conversation_starter_examples=conversation_starters,
            topics=["monkey"],
            completion_type=CompletionType.huggingface_api,
            prompt_rows=20,
        )
        elapsed_seconds = str(time.time() - start)
        print(f"Elapsed seconds: {elapsed_seconds}")
        print(conversation_starter)

    def test_generate_conversation_starter_profane(self):
        firestore_client = firestore.client()
        conversation_starters, index, _ = get_existing_conversation_starters(
            firestore_client,
            embeddings=True,
            limit=4000,
            rebuild_embeddings=False,
        )
        with self.assertRaises(ProfaneException):
            conversation_starter = generate_conversation_starter(
                index=index,
                conversation_starter_examples=conversation_starters,
                topics=["god"],
                profanity_threshold=ProfanityThreshold.strict,
            )
            # Non deterministic tests, don't run in CI?
            self.assertEqual(conversation_starter, None)
        conversation_starter = generate_conversation_starter(
            index=index,
            conversation_starter_examples=conversation_starters,
            topics=["god"],
            profanity_threshold=ProfanityThreshold.tolerant,
        )
        assert conversation_starter is not None
        conversation_starter = generate_conversation_starter(
            index=index,
            conversation_starter_examples=conversation_starters,
            topics=["god"],
            profanity_threshold=ProfanityThreshold.open,
        )
        assert conversation_starter is not None
