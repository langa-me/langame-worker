from langame.prompts import build_prompt, extract_topics_from_personas
from langame.conversation_starters import get_existing_conversation_starters
from firebase_admin import credentials, firestore
import firebase_admin
import openai
import os
from unittest import IsolatedAsyncioTestCase

# disable pylint for docstring
# pylint: disable=C0116
# pylint: disable=C0115


class TestPrompts(IsolatedAsyncioTestCase):
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
            limit=1000,
        )
        topics = ["philosophy"]
        prompt = build_prompt(
            index,
            conversation_starters,
            topics=topics,
            sentence_embeddings_model=sentence_embeddings_model,
            prompt_rows=5,
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

    async def test_extract_topics_from_bio(self):
        personas = [
            "I am a biology student, I like to play basketball on my free time",
            "I am a computer science student, I like to play video games on my free time",
        ]
        topics = await extract_topics_from_personas(personas)
        assert topics is not None
        # should contains "biology" and "computer science" at least
        lower_cased_topics = [t.lower() for t in topics]
        assert "biology" in lower_cased_topics
        assert "computer science" in lower_cased_topics
