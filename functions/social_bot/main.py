import os
import grpc
from api.api_pb2 import ConversationStarterRequest
from api.api_pb2_grpc import ConversationStarterServiceStub
import json
import requests
import logging
from google.cloud import firestore
from random import choice
# For more channel options, please see https://grpc.io/grpc/core/group__grpc__arg__keys.html
CHANNEL_OPTIONS = [
    ("grpc.lb_policy_name", "pick_first"),
    ("grpc.enable_retries", 0),
    ("grpc.keepalive_timeout_ms", 10000),
]

DISCORD_APPLICATION_ID = os.getenv("DISCORD_APPLICATION_ID")

client = firestore.Client()

# This is a list of funny messages that the bot will pick from to answer to the user
# in case the API couldn't generate a conversation starter for the
# given topics, suggesting known topics.
UNIMPLEMENTED_TOPICS_MESSAGES = [
    "I'm sorry, I haven't learned anything about that yet. ",
    "I don't know what's on your mind right now. ",
    "I'm sorry, I lack an opinion regarding that at the moment. ",
    "I'm sorry, I don't know anything about that topic yet. ",
    "I'm sorry, I'm not familiar with that topic. ",
    "I'm sorry, I can't talk about that yet. ",
    "I'm sorry, I should conceptualize this topic sometime soon. ",
    "This is a tough topic, I don't know much about...",
    "This feels very unfamiliar, I'm finding my way around this topic...",
    "I'm sorry, I don't know anything about it... yet!",
    "This topic is new to me, I'm not sure what to say. ",
    "I haven't really learned much about this topic... ",
    "I'm sorry, I should learn about this topic sooner. ",
    "I can't think of anything interesting to say about this topic. ",
    "How about we talk about something else? Try 'ice breaker,philosophy,travel,physic,ecology,artificial intelligence'",
    "Please ask me something else, I have nothing to talk about this.",
]
# TODO: generate online messages

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

    if "topics" in data["value"]["fields"]:
        topics = [
            e["stringValue"]
            for e in data["value"]["fields"]["topics"]["arrayValue"]["values"]
        ]
    if not topics:
        logger.error(f"No topics in message: {data}")
        return
    with grpc.secure_channel(
        "conversation-starter-garupdicsa-uc.a.run.app:443",
        grpc.ssl_channel_credentials(),
    ) as channel:
        stub = ConversationStarterServiceStub(channel)
        cs_request = ConversationStarterRequest()
        cs_request.topics.extend(topics)
        logger.info("Requesting conversation starter with topics: %s", topics)
        response = None
        error = None
        try:
            response = stub.GetConversationStarter(cs_request)
            logger.info(f"Response from conversation starter: {response}")
        except grpc.RpcError as e:
            logger.warn(f"Error from conversation starter: {e}")
            error = e

        if data["value"]["fields"]["social_software"]["stringValue"] == "slack":
            logger.info("Sending message to slack")
            requests.post(
                data["value"]["fields"]["response_url"]["stringValue"],
                data=json.dumps(
                    {
                        "text": response.conversation_starter if response else choice(UNIMPLEMENTED_TOPICS_MESSAGES),
                        "username": "Langame",
                        "response_type": "in_channel",
                    }
                ),
            )
        elif data["value"]["fields"]["social_software"]["stringValue"] == "discord":
            logger.info("Sending message to discord")
            interaction_token = data["value"]["fields"]["interaction_token"][
                "stringValue"
            ]
            # https://discord.com/developers/docs/resources/webhook#execute-webhook
            requests.post(
                f"https://discord.com/api/v8/webhooks/{DISCORD_APPLICATION_ID}/{interaction_token}",
                headers={"Content-Type": "application/json"},
                data=json.dumps(
                    {
                        "content": response.conversation_starter if response else choice(UNIMPLEMENTED_TOPICS_MESSAGES),
                    }
                ),
            )
        if response:
            affected_doc.update({"conversation_starter": response.conversation_starter})
        else:
            affected_doc.update({"errors": firestore.ArrayUnion([error])})
