from flask import request
from firebase_admin import firestore
import logging
from random import choice
from langame.functions.messages import WAITING_MESSAGES

def slack_bot(_):
    logger = logging.getLogger("slack_bot")
    logging.basicConfig(level=logging.INFO)
    response_url = request.form.get("response_url")
    text = request.form.get("text")
    topics = ["ice breaker"]
    if text and len(text.split(",")) > 0:
        topics = text.split(",")
    logger.info(f"Requesting conversation starter with topics: {topics}")
    firestore_client = firestore.Client()
    firestore_client.collection("social_interactions").add(
        {
            "social_software": "slack",
            "topics": topics,
            "response_url": response_url,
            "created_at": firestore.SERVER_TIMESTAMP,
            "state": "to-process",
        }
    )
    return {"response_type": "in_channel", "text": f"Topics: {','.join(topics)}\n{choice(WAITING_MESSAGES)}"}
