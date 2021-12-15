import os
import logging
import requests
from datetime import datetime, timedelta
from flask import request, jsonify
from random import choice
from discord_interactions import (
    verify_key_decorator,
    InteractionType,
    InteractionResponseType,
)
from firebase_admin import firestore
from third_party.common.messages import WAITING_MESSAGES
CLIENT_PUBLIC_KEY = os.getenv("CLIENT_PUBLIC_KEY")

@verify_key_decorator(CLIENT_PUBLIC_KEY)
def discord_bot(_):
    logger = logging.getLogger("discord_bot")
    logging.basicConfig(level=logging.INFO)
    json_request = request.get_json()
    if json_request["type"] == InteractionType.APPLICATION_COMMAND:
        logger.info("Application command received")
        logger.info(json_request)
        topics = ["ice breaker"]
        channel_id = None
        interaction_token = json_request["token"]
        username = json_request["member"]["user"]["username"]
        # TODO: rate limit user
        if (
            "data" in json_request
            and "options" in json_request["data"]
            and len(json_request["data"]["options"]) > 0
            and "value" in json_request["data"]["options"][0]
            and len(json_request["data"]["options"][0]["value"].split(",")) > 0
        ):
            topics = json_request["data"]["options"][0]["value"].split(",")
        if "channel_id" in json_request:
            channel_id = json_request["channel_id"]
        if not channel_id:
            return jsonify(
                {
                    "response_type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                    "text": "You need to send this command to a channel",
                }
            )
        logger.info(f"Requesting conversation starter with topics: {topics}")
        firestore_client = firestore.Client()
        rate_limit_doc = firestore_client.collection("rate_limits").document(username).get()
        # check if last query happenned less than a minute ago
        if rate_limit_doc.exists and "last_query" in rate_limit_doc.to_dict() and \
            datetime.now() > datetime.fromtimestamp(rate_limit_doc.get("last_query").timestamp()) + timedelta(seconds=30):
            # TODO: funny messages
            return jsonify(
                {
                    "response_type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                    "text": "You have been rate limited. Please wait a few minutes before using this command again.",
                }
            )

        firestore_client.collection("social_interactions").add(
            {
                "topics": topics,
                "channel_id": channel_id,
                "interaction_token": interaction_token,
                "username": username,
                "social_software": "discord",
                "created_at": firestore.SERVER_TIMESTAMP,
                "state": "to-process",
            }
        )
        # https://discord.com/developers/docs/resources/webhook#execute-webhook
        # requests.post(
        #     f"https://discord.com/api/v8/channels/{channel_id}/typing",
        # )
        return jsonify(
            {
                "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                "data": {
                    "content": f"Topics: {','.join(topics)}\n{choice(WAITING_MESSAGES)}",
                },
            }
        )
