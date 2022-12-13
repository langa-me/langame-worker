from .services import request_starter_for_service
import os
from firebase_admin import firestore, initialize_app
from google.cloud.firestore import Client
from unittest import IsolatedAsyncioTestCase
import time

# disable pylint for docstring
# pylint: disable=C0116
# pylint: disable=C0115

def k(api_key: str):
    db: Client = firestore.client()
    docs = db.collection("api_keys").where("apiKey", "==", api_key).stream()

    for api_key_doc in docs:
        owner = api_key_doc.to_dict().get("owner", None)
        org_doc = (
            db.collection("organizations").document(owner).get() if owner else None
        )
        if not org_doc:
            break

        org_members = org_doc.to_dict().get("members", [])
        member_id = org_members[0]

        return api_key_doc, org_doc, member_id, None
    return None, None, None, None

class TestServices(IsolatedAsyncioTestCase):
    def setUp(self):
        initialize_app()
    async def test_request_starter_for_service(self):
        api_key_doc, org_doc, _, error = k(os.environ["LANGAME_API_KEY"])
        assert error is None, error
        buckets = [1, 3, 5, 7]
        for limit in buckets:
            start_time = time.time()
            conversation_starters, error = request_starter_for_service(
                api_key_doc=api_key_doc,
                org_doc=org_doc,
                topics=["biology", "symbiosis", "love"],
                limit=limit,
                fix_grammar=False,
                profanity_threshold="open",
            )
            end_time = time.time()
            print(conversation_starters)
            print(end_time - start_time)
            assert error is None, error
            assert conversation_starters is not None, conversation_starters
                