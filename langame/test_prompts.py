from langame.prompts import build_prompt
from langame.conversation_starters import get_existing_conversation_starters
from firebase_admin import credentials, firestore
import firebase_admin
import unittest
import openai
import os


class TestPrompts(unittest.TestCase):
    def setUp(self) -> None:
        openai.api_key = os.environ["OPENAI_KEY"]
        openai.organization = os.environ["OPENAI_ORG"]
        cred = credentials.Certificate("./svc.dev.json")
        firebase_admin.initialize_app(cred)
        return super().setUp()

    def test_build_prompt(self):
        firestore_client = firestore.client()
        (
            conversation_starters,
            index,
            sentence_embeddings_model,
        ) = get_existing_conversation_starters(
            firestore_client,
            embeddings=True,
            limit=1000,
            rebuild_embeddings=True,
        )
        topics = ["philosophy"]
        prompt = build_prompt(
            index,
            conversation_starters,
            topics,
            sentence_embeddings_model=sentence_embeddings_model,
        )
        assert prompt is not None
        # Check that prompt end with "\nphilosophy ###"
        assert prompt.endswith("\nThis is a conversation starter about philosophy ###")

        # Now with unknown topics
        topics = ["foo", "bar"]
        prompt = build_prompt(
            index,
            conversation_starters,
            topics,
            sentence_embeddings_model=sentence_embeddings_model,
        )
        assert prompt is not None
        # Check that prompt end with "\nfoo,bar ###"
        assert prompt.endswith("\nnThis is a conversation starter about foo,bar ###")
