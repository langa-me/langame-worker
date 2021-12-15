import os
import json
import requests
import logging
from firebase_admin import firestore
from random import choice
from third_party.common.messages import (
    UNIMPLEMENTED_TOPICS_MESSAGES,
    FAILING_MESSAGES,
    PROFANITY_MESSAGES,
)

DISCORD_APPLICATION_ID = os.getenv("DISCORD_APPLICATION_ID")
client = firestore.Client()

def social_bot(data, context):
    """Triggered by a change to a Firestore document.
    Args:
        data (dict): The event payload.
        context (google.cloud.functions.Context): Metadata for the event.
    """
    logger = logging.getLogger("social_bot")
    logging.basicConfig(level=logging.INFO)

    path_parts = context.resource.split("/documents/")[1].split("/")
    collection_path = path_parts[0]
    document_path = "/".join(path_parts[1:])

    affected_doc = client.collection(collection_path).document(document_path)

    if "state" in data["value"]["fields"]:
        state = data["value"]["fields"]["state"]["stringValue"]
    if state == "delivered":
        logger.info(f"Message already delivered. Skipping.")
        return
    if "topics" in data["value"]["fields"]:
        topics = [
            e["stringValue"]
            for e in data["value"]["fields"]["topics"]["arrayValue"]["values"]
        ]
        topics_as_string = ",".join(topics)
    if "social_software" in data["value"]["fields"]:
        social_software = data["value"]["fields"]["social_software"]["stringValue"]
    if "conversation_starter" in data["value"]["fields"]:
        conversation_starter = data["value"]["fields"]["conversation_starter"][
            "stringValue"
        ]
    if "username" in data["value"]["fields"]:
        username = data["value"]["fields"]["username"]["stringValue"]
    if not state or not topics:
        logger.error(f"No state or topics found in {data}")
        return
    if state in ["to-process", "processing"]:
        logger.info(f"Request being processed: {state}, aborting.")
        return
    user_message = ""
    if state == "error":
        user_message = data["value"]["fields"]["user_message"]["stringValue"]
    elif state == "processed":
        user_message = conversation_starter
    if social_software == "slack":
        logger.info(f"Sending message to slack {user_message}")
        requests.post(
            data["value"]["fields"]["response_url"]["stringValue"],
            data=json.dumps(
                {
                    "text": f"Topics: {topics_as_string}\n{user_message}",
                    "username": "Langame",
                    "response_type": "in_channel",
                }
            ),
        )
    elif social_software == "discord":
        logger.info(f"Sending message to discord {user_message}")
        interaction_token = data["value"]["fields"]["interaction_token"]["stringValue"]
        # https://discord.com/developers/docs/resources/webhook#execute-webhook
        requests.patch(
            f"https://discord.com/api/v8/webhooks/{DISCORD_APPLICATION_ID}/{interaction_token}/messages/@original",
            headers={"Content-Type": "application/json"},
            data=json.dumps(
                {
                    "content": f"Topics: {topics_as_string}.\n{user_message}",
                }
            ),
        )
    logger.info(f"Done sending message to {social_software}")
    affected_doc.update({"state": "delivered"})
