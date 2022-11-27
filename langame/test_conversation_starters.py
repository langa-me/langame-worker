from typing import Any, List
from langame.conversation_starters import (
    get_existing_conversation_starters,
    generate_conversation_starter,
)
from langame.completion import CompletionType, get_last_model
from langame.profanity import ProfaneException, ProfanityThreshold
from langame.quality import is_garbage
from firebase_admin import credentials, firestore
import firebase_admin
import unittest
import openai
import os
import numpy as np
from transformers import (
    T5ForConditionalGeneration,
    T5Tokenizer,
    AutoTokenizer,
    GPT2LMHeadModel,
)
import time
from faiss.swigfaiss import IndexFlat


class TestConversationStarters(unittest.TestCase):
    def setUp(self) -> None:
        openai.api_key = os.environ["OPENAI_KEY"]
        openai.organization = os.environ["OPENAI_ORG"]
        cred = credentials.Certificate("./svc.prod.json")
        firebase_admin.initialize_app(cred)
        return super().setUp()

    def basic_assertions(
        self, conversation_starters: List[Any], index: IndexFlat, limit: int
    ):
        # index should not be None then
        self.assertIsNotNone(index)
        # conversation_starters should be a list
        self.assertIsInstance(conversation_starters, list)
        # conversation_starters should not be empty
        self.assertTrue(len(conversation_starters) > 0)
        # should be close to length "limit" (potentially less because of garbage)
        self.assertLess(len(conversation_starters), limit)
        # all dicts should contains the key "content" and "topics" and "id"
        for e in conversation_starters:
            self.assertIn("content", e)
            self.assertIn("topics", e)
            self.assertIn("id", e)
        # should not contain garbage
        for e in conversation_starters:
            self.assertFalse(is_garbage(e))

    def test_get_existing_conversation_starters_rebuild_embeddings(self):
        firestore_client = firestore.client()
        (
            conversation_starters,
            index,
            sentence_embeddings_model,
        ) = get_existing_conversation_starters(
            client=firestore_client,
            limit=3,
        )
        self.basic_assertions(conversation_starters, index, 4)
        query = sentence_embeddings_model.encode(
            "immortality", show_progress_bar=False, device="cpu"
        )
        _, I = index.search(np.array([query]), 20)
        memes = [conversation_starters[i] for i in I[0]]
        self.assertTrue(len(memes) > 0)

        # directories "embeddings" and "indexes" should have been created
        self.assertTrue(os.path.isdir("./embeddings"))
        self.assertTrue(os.path.isdir("./indexes"))

    def test_generate_conversation_starter_openai(self):
        model_name = "flexudy/t5-small-wav2vec2-grammar-fixer"
        grammar_tokenizer = T5Tokenizer.from_pretrained(model_name)
        grammar_model = T5ForConditionalGeneration.from_pretrained(model_name).to(
            "cpu"
        )
        firestore_client = firestore.client()
        (
            conversation_starters,
            index,
            sentence_embeddings_model,
        ) = get_existing_conversation_starters(
            firestore_client,
            limit=200,
        )
        start = time.time()
        topics, new_conversation_starters = generate_conversation_starter(
            index=index,
            conversation_starter_examples=conversation_starters,
            topics=["philosophy"],
            sentence_embeddings_model=sentence_embeddings_model,
            fix_grammar=False,
            parallel_completions=3,
            grammar_tokenizer=grammar_tokenizer,
            grammar_model=grammar_model,
            api_completion_model="curie:ft-personal-2022-02-09-05-17-08"
        )
        elapsed_seconds = str(time.time() - start)
        print(f"Elapsed seconds: {elapsed_seconds}")
        print(new_conversation_starters)

    def test_generate_conversation_starter_openai_new_topic(self):
        firestore_client = firestore.client()
        conversation_starters, index, sentence_embeddings_model = get_existing_conversation_starters(
            firestore_client,
            limit=4000,
        )
        start = time.time()
        topics, new_conversation_starters = generate_conversation_starter(
            index=index,
            conversation_starter_examples=conversation_starters,
            topics=["monkey"],
            sentence_embeddings_model=sentence_embeddings_model,
            api_completion_model="curie:ft-personal-2022-02-09-05-17-08",
            prompt_rows=3,
        )
        elapsed_seconds = str(time.time() - start)
        print(f"Elapsed seconds: {elapsed_seconds}")
        print(new_conversation_starters)

    def test_generate_conversation_starter_openai_no_ft_versus_ft(self):
        firestore_client = firestore.client()
        conversation_starters, index, sentence_embeddings_model = get_existing_conversation_starters(
            firestore_client,
            limit=4000,
        )
        last_cs_model = get_last_model()["fine_tuned_model"]
        start = time.time()
        topics, new_conversation_starters = generate_conversation_starter(
            index=index,
            conversation_starter_examples=conversation_starters,
            topics=["monkey"],
            sentence_embeddings_model=sentence_embeddings_model,
            api_completion_model="text-davinci-002",
            prompt_rows=3,
        )
        elapsed_seconds = str(time.time() - start)
        start = time.time()
        topics, new_ft_conversation_starters = generate_conversation_starter(
            index=index,
            conversation_starter_examples=conversation_starters,
            topics=["monkey"],
            sentence_embeddings_model=sentence_embeddings_model,
            api_completion_model=last_cs_model,
            prompt_rows=1,
        )
        ft_elapsed_seconds = str(time.time() - start)
        print(f"Non-ft elapsed seconds: {elapsed_seconds}")
        print(f"Ft elapsed seconds: {ft_elapsed_seconds}")
        print(f"Non-ft: {new_conversation_starters}")
        print(f"Ft: {new_ft_conversation_starters}")

    def test_generate_conversation_starter_openai_with_new_embeddings(self):
        firestore_client = firestore.client()
        (
            conversation_starters,
            index,
            sentence_embeddings_model,
        ) = get_existing_conversation_starters(
            firestore_client,
            limit=200,
        )
        start = time.time()
        topics, new_conversation_starters = generate_conversation_starter(
            index=index,
            conversation_starter_examples=conversation_starters,
            topics=["monkey"],
            sentence_embeddings_model=sentence_embeddings_model,
        )
        elapsed_seconds = str(time.time() - start)
        print(f"Elapsed seconds: {elapsed_seconds}")
        print(new_conversation_starters)

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
        conversation_starters, index, sentence_embeddings_model = get_existing_conversation_starters(
            firestore_client,
            limit=4000,
        )
        start = time.time()

        topics, new_conversation_starters = generate_conversation_starter(
            index=index,
            conversation_starter_examples=conversation_starters,
            topics=["monkey"],
            sentence_embeddings_model=sentence_embeddings_model,
            completion_type=CompletionType.local,
            prompt_rows=5,
            model=model,
            tokenizer=tokenizer,
            use_gpu=use_gpu,
        )
        elapsed_seconds = str(time.time() - start)
        print(f"Elapsed seconds: {elapsed_seconds}")
        print(new_conversation_starters)

    def test_generate_conversation_starter_huggingface_api(self):
        firestore_client = firestore.client()
        conversation_starters, index, sentence_embeddings_model = get_existing_conversation_starters(
            firestore_client,
            limit=4000,
        )
        start = time.time()

        topics, new_conversation_starters = generate_conversation_starter(
            index=index,
            conversation_starter_examples=conversation_starters,
            topics=["monkey"],
            sentence_embeddings_model=sentence_embeddings_model,
            completion_type=CompletionType.huggingface_api,
            prompt_rows=20,
        )
        elapsed_seconds = str(time.time() - start)
        print(f"Elapsed seconds: {elapsed_seconds}")
        print(new_conversation_starters)

    def test_generate_conversation_starter_profane(self):
        firestore_client = firestore.client()
        conversation_starters, index, sentence_embeddings_model = get_existing_conversation_starters(
            firestore_client,
            limit=4000,
        )
        with self.assertRaises(ProfaneException):
            topics, conversation_starter = generate_conversation_starter(
                index=index,
                conversation_starter_examples=conversation_starters,
                topics=["god"],
                profanity_threshold=ProfanityThreshold.strict,
                sentence_embeddings_model=sentence_embeddings_model,
            )
            # Non deterministic tests, don't run in CI?
            self.assertEqual(conversation_starter, None)
        topics, conversation_starter = generate_conversation_starter(
            index=index,
            conversation_starter_examples=conversation_starters,
            topics=["god"],
            profanity_threshold=ProfanityThreshold.tolerant,
            sentence_embeddings_model=sentence_embeddings_model,
        )
        assert conversation_starter is not None
        topics, conversation_starter = generate_conversation_starter(
            index=index,
            conversation_starter_examples=conversation_starters,
            topics=["god"],
            profanity_threshold=ProfanityThreshold.open,
            sentence_embeddings_model=sentence_embeddings_model,
        )
        assert conversation_starter is not None

    def test_generate_conversation_starter_gooseai(self):
        firestore_client = firestore.client()
        (
            conversation_starters,
            index,
            sentence_embeddings_model,
        ) = get_existing_conversation_starters(
            firestore_client,
            limit=200,
        )
        start = time.time()
        topics, conversation_starters = generate_conversation_starter(
            index=index,
            conversation_starter_examples=conversation_starters,
            topics=["philosophy"],
            sentence_embeddings_model=sentence_embeddings_model,
            completion_type=CompletionType.openai_api,
            prompt_rows=5,
            api_completion_model="gpt-neo-1-3b",
        )
        elapsed_seconds = str(time.time() - start)
        print(f"Elapsed seconds: {elapsed_seconds}")
        print(conversation_starters)


    def test_generate_conversation_starter_grammar(self):
        firestore_client = firestore.client()
        conversation_starters, index, sentence_embeddings_model = get_existing_conversation_starters(
            firestore_client,
            limit=200,
        )
        topics, conversation_starter = generate_conversation_starter(
            index=index,
            conversation_starter_examples=conversation_starters,
            topics=["god"],
            profanity_threshold=ProfanityThreshold.tolerant,
            sentence_embeddings_model=sentence_embeddings_model,
            fix_grammar=True,
            prompt_rows=1,
            api_completion_model="curie:ft-personal-2022-02-09-05-17-08",
        )
        assert conversation_starter is not None
