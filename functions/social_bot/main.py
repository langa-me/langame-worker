import os
import json
import requests
import logging
from firebase_admin import firestore
from google.cloud.firestore import Client
from random import choice
from datetime import datetime, timedelta
from third_party.common.messages import (
    RATE_LIMIT_MESSAGES,
)
from third_party.common.services import request_starter

DISCORD_APPLICATION_ID = os.getenv("DISCORD_APPLICATION_ID")
client: Client = firestore.Client()


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
    topics_as_string = ""
    players_as_string = ""
    if "state" in data["value"]["fields"]:
        state = data["value"]["fields"]["state"]["stringValue"]
    if state == "delivered":
        logger.info("Message already delivered. Skipping.")
        return
    if "topics" in data["value"]["fields"]:
        topics = [
            e["stringValue"]
            for e in data["value"]["fields"]["topics"]["arrayValue"]["values"]
        ]
        topics_as_string = ",".join(topics)
    if (
        "players" in data["value"]["fields"]
        and "arrayValue" in data["value"]["fields"]["players"]
        and "values" in data["value"]["fields"]["players"]["arrayValue"]
    ):
        players = [
            e["stringValue"]
            for e in data["value"]["fields"]["players"]["arrayValue"]["values"]
        ]
        players_as_string = "\nPlayers: " + ",".join(players) + "."
    if "social_software" in data["value"]["fields"]:
        social_software = data["value"]["fields"]["social_software"]["stringValue"]
    if "username" in data["value"]["fields"]:
        username = data["value"]["fields"]["username"]["stringValue"]

    if not username:
        logger.error("No username in document. Skipping.")
        return
    rate_limit_doc = client.collection("rate_limits").document(username).get()
    user_message = ""

    # check if last query happenned less than a minute ago
    if (
        rate_limit_doc.exists
        and "last_query" in rate_limit_doc.to_dict()
        and datetime.now()
        < datetime.fromtimestamp(rate_limit_doc.get("last_query").timestamp())
        + timedelta(seconds=10)
    ):
        logger.warning(f"Rate limit for {username} expired")
        user_message = choice(RATE_LIMIT_MESSAGES)
    else:
        rate_limit_doc.reference.set({"last_query": firestore.SERVER_TIMESTAMP})

    if not user_message:
        conversation_starter, user_message = request_starter(logger, client, topics)
        if conversation_starter:
            user_message = conversation_starter

    if social_software == "slack":
        logger.info(f"Sending message to slack {user_message}")
        requests.post(
            data["value"]["fields"]["response_url"]["stringValue"],
            data=json.dumps(
                {
                    "text": f"Topics: {topics_as_string}\n\n**{user_message}**",
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
                    "content": f"Topics: {topics_as_string}.{players_as_string}\n\n**{user_message}**",
                }
            ),
        )
    logger.info(f"Done sending message to {social_software}:{user_message}")
    affected_doc.update({"state": "delivered", "user_message": user_message})
