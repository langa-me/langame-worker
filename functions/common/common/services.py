from time import sleep
from logging import Logger
from typing import List, Optional, Tuple
from firebase_admin import firestore
from google.cloud.firestore import DocumentSnapshot, DocumentReference, Client
from third_party.common.messages import (
    UNIMPLEMENTED_TOPICS_MESSAGES,
    FAILING_MESSAGES,
    PROFANITY_MESSAGES,
)
from random import choice
def request_starter(logger: Logger, firestore_client: Client, topics: List[str]
) -> Tuple[Optional[str], Optional[str]]:
    """
    Request a conversation starter from the API.
    Args:
        logger: Logger object.
        firestore_client: Firestore client.
        topics: List of topics to request a starter for.
    Returns:
        Tuple of (starter, user message).
    """
    conversation_starter, user_message = None, None
    new_meme_ref: DocumentReference = firestore_client.collection("memes").add({
            "topics": topics,
            "createdAt": firestore.SERVER_TIMESTAMP,
            "disabled": True,
            "tweet": False,
            "state": "to-process",
        })[1]
    # Poll until a conversation starter is generated
    new_meme_doc: DocumentSnapshot = None
    for i in range(3):
        logger.info(f"Polling for conversation starter n°{i}/5")
        sleep((i/2)**3)
        new_meme_doc = new_meme_ref.get()
        conversation_starter = new_meme_doc.to_dict().get("content")
        if conversation_starter and len(conversation_starter) > 0:
            break
    if not conversation_starter:
        error = new_meme_doc.to_dict().get("error", None)
        if error == "no-topics":
            user_message = choice(UNIMPLEMENTED_TOPICS_MESSAGES)
        elif error == "profane":
            user_message = choice(PROFANITY_MESSAGES)
            user_message = user_message.replace("[TOPICS]", f"\"{','.join(topics)}\"")
        else:
            user_message = choice(FAILING_MESSAGES)
        logger.warning("Failed to generate conversation starter")
    return conversation_starter, user_message