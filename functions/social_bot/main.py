import os
import grpc
from api.api_pb2 import ConversationStarterRequest
from api.api_pb2_grpc import ConversationStarterServiceStub
import json
import requests
import logging
from google.cloud import firestore
from random import choice
from utils.messages import UNIMPLEMENTED_TOPICS_MESSAGES, FAILING_MESSAGES, PROFANITY_MESSAGES
# For more channel options, please see https://grpc.io/grpc/core/group__grpc__arg__keys.html
CHANNEL_OPTIONS = [
    ("grpc.lb_policy_name", "pick_first"),
    ("grpc.enable_retries", 0),
    ("grpc.keepalive_timeout_ms", 10000),
]

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
            # TODO?
            # if data["value"]["fields"]["social_software"]["stringValue"] == "discord":
            #     # POST/channels/{channel.id}/typing
            #     logger.info(f"Sending typing indicator to discord")
            #     channel_id = data["value"]["fields"]["channel_id"][
            #         "stringValue"
            #     ]
            #     # https://discord.com/developers/docs/resources/webhook#execute-webhook
            #     requests.post(
            #         f"https://discord.com/api/v8/channels/{channel_id}/typing",
            #     )

            response = stub.GetConversationStarter(cs_request)
            logger.info(f"Response from conversation starter: {response}")
        except Exception as e:
            logger.warn(f"Error from conversation starter: {e}")
            error = e
        user_facing_message = ""
        if response:
            user_facing_message = response.conversation_starter
        elif "profane" in str(error):
            user_facing_message = choice(PROFANITY_MESSAGES)
            user_facing_message = user_facing_message.replace("[TOPICS]", f"\"{','.join(topics)}\"")
        elif "not-found" in str(error):
            user_facing_message = choice(UNIMPLEMENTED_TOPICS_MESSAGES)
        else:
            user_facing_message = choice(FAILING_MESSAGES)
        if data["value"]["fields"]["social_software"]["stringValue"] == "slack":
            logger.info(f"Sending message to slack {user_facing_message}")
            requests.post(
                data["value"]["fields"]["response_url"]["stringValue"],
                data=json.dumps(
                    {
                        "text": user_facing_message,
                        "username": "Langame",
                        "response_type": "in_channel",
                    }
                ),
            )
        elif data["value"]["fields"]["social_software"]["stringValue"] == "discord":
            logger.info(f"Sending message to discord {user_facing_message}")
            interaction_token = data["value"]["fields"]["interaction_token"][
                "stringValue"
            ]
            # https://discord.com/developers/docs/resources/webhook#execute-webhook
            requests.post(
                f"https://discord.com/api/v8/webhooks/{DISCORD_APPLICATION_ID}/{interaction_token}",
                headers={"Content-Type": "application/json"},
                data=json.dumps(
                    {
                        "content": user_facing_message,
                    }
                ),
            )
        if response:
            affected_doc.update({"conversation_starter": response.conversation_starter})
        else:
            affected_doc.update({"errors": firestore.ArrayUnion([error])})
