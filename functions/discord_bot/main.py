import logging
from flask import request, jsonify
import os
from discord_interactions import (
    verify_key_decorator,
    InteractionType,
    InteractionResponseType,
)
from google.cloud import pubsub_v1

CLIENT_PUBLIC_KEY = os.getenv("CLIENT_PUBLIC_KEY")

@verify_key_decorator(CLIENT_PUBLIC_KEY)
def discord_bot(_):
    logging.basicConfig(level=logging.INFO)
    if request.json["type"] == InteractionType.APPLICATION_COMMAND:

        topics = ["ice breaker"]
        channel_id = None
        interaction_token = request.json["token"]
        if (
            "data" in request.json
            and len(request.json["data"]) > 0
            and "value" in request.json["data"][0]
            and len(request.json["data"][0]["value"].split(",")) > 0
        ):
            topics = request.json["data"][0]["value"].split(",")
        if "channel_id" in request.json:
            channel_id = request.json["channel_id"]
        if not channel_id:
            return jsonify(
                {
                    "response_type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                    "text": "You need to send this command to a channel",
                }
            )
        logging.info(f"Requesting conversation starter with topics: {topics}")
        publisher = pubsub_v1.PublisherClient()
        publish_future = publisher.publish(
            "social_bot",
            str.encode(topics),
            social_software="discord",
            channel_id=channel_id,
            interaction_token=interaction_token,
        )
        publish_future.result()
        return jsonify(
            {
                "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                "data": {
                    "content": f"Will provide you a conversation starter about {','.join(topics)}"
                },
            }
        )
