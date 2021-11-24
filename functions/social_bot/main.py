import os
import grpc
from api.api_pb2 import ConversationStarterRequest
from api.api_pb2_grpc import ConversationStarterServiceStub
import json
import requests
import logging

# For more channel options, please see https://grpc.io/grpc/core/group__grpc__arg__keys.html
CHANNEL_OPTIONS = [
    ("grpc.lb_policy_name", "pick_first"),
    ("grpc.enable_retries", 0),
    ("grpc.keepalive_timeout_ms", 10000),
]

APPLICATION_ID = os.getenv("APPLICATION_ID")


def social_bot(message, context):
    """Background Cloud Function to be triggered by Pub/Sub.
    Args:
         event (dict):  The dictionary with data specific to this type of
                        event. The `@type` field maps to
                         `type.googleapis.com/google.pubsub.v1.PubsubMessage`.
                        The `data` field maps to the PubsubMessage data
                        in a base64-encoded string. The `attributes` field maps
                        to the PubsubMessage attributes if any is present.
         context (google.cloud.functions.Context): Metadata of triggering event
                        including `event_id` which maps to the PubsubMessage
                        messageId, `timestamp` which maps to the PubsubMessage
                        publishTime, `event_type` which maps to
                        `google.pubsub.topic.publish`, and `resource` which is
                        a dictionary that describes the service API endpoint
                        pubsub.googleapis.com, the triggering topic's name, and
                        the triggering event type
                        `type.googleapis.com/google.pubsub.v1.PubsubMessage`.
    Returns:
        None. The output is written to Cloud Logging.
    """
    import base64
    logging.basicConfig(level=logging.INFO)

    if "data" in message:
        data = base64.b64decode(message["data"])
        topics = data.decode("utf-8")
    if not data:
        logging.error(f"No data in message: {message}")
        return
    with grpc.secure_channel(
        "conversation-starter-garupdicsa-uc.a.run.app:443",
        grpc.ssl_channel_credentials(),
    ) as channel:
        stub = ConversationStarterServiceStub(channel)
        cs_request = ConversationStarterRequest()
        cs_request.topics.extend(topics)
        response = stub.GetConversationStarter(cs_request)

        if message.attributes["social_software"] == "slack":
            requests.post(
                message.attributes["response_url"],
                data=json.dumps(
                    {"text": response.conversation_starter, "username": "Langame"}
                ),
            )
        elif message.attributes["social_software"] == "discord":
            # https://discord.com/developers/docs/resources/webhook#execute-webhook
            requests.post(
                f"https://discord.com/api/v8/webhooks/{APPLICATION_ID}/{message.attributes['interaction_token']}",
                data=json.dumps(
                    {
                        "content": response.conversation_starter,
                    }
                ),
            )
        message.ack()  # TODO: should actually check if everything went well
