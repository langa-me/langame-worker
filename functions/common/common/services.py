import json
import requests
from time import sleep
from logging import Logger
from typing import List, Optional, Tuple, Any
from firebase_admin import firestore
from google.cloud.firestore import DocumentSnapshot, DocumentReference, Client
from third_party.common.messages import (
    UNIMPLEMENTED_TOPICS_MESSAGES,
    FAILING_MESSAGES,
    PROFANITY_MESSAGES,
)
from random import choice


def request_starter(
    logger: Logger, firestore_client: Client, topics: List[str]
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
    new_meme_ref: DocumentReference = firestore_client.collection("memes").add(
        {
            "topics": topics,
            "createdAt": firestore.SERVER_TIMESTAMP,
            "disabled": True,
            "tweet": False,
            "state": "to-process",
            "shard": 0,
        }
    )[1]
    # Poll until a conversation starter is generated
    new_meme_doc: DocumentSnapshot = None
    max_tries = 10
    for i in range(max_tries):
        logger.info(f"Polling for conversation starter n°{i}/{max_tries}")
        sleep((i / 2) ** 3)
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


def request_starter_for_service(
    url: str,
    api_key_id: str,
    logger: Optional[Logger],
    topics: List[str],
    quantity: int = 1,
    translated: bool = False,
) -> List[Any]:
    """
    Request a conversation starter from the API.
    Args:
        logger: Logger object.
        firestore_client: Firestore client.
        topics: List of topics to request a starter for.
    Returns:
        Tuple of (starter, user message).
    """
    headers = {
        "Content-Type": "application/json",
    }
    data = {
        "appId": api_key_id,
        "topics": topics,
        "quantity": quantity,
        "translated": translated,
    }
    response = requests.post(url, headers=headers, data=json.dumps({"data": data}))
    response_data = response.json()
    if response_data.get("error", None) or "result" not in response_data:
        if logger:
            logger.warning(f"Failed to request starter for {api_key_id}")
        return None, {
            "message": response_data.get("error", {}).get("message", "Unknown error"),
            "code": response.status_code,
            "status": response_data.get("error", {}).get("status", "INTERNAL_ERROR"),
        }

    return response_data["result"]["memes"], None
