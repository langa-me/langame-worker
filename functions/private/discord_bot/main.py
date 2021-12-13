import logging
from flask import request, jsonify
import os
from discord_interactions import (
    verify_key_decorator,
    InteractionType,
    InteractionResponseType,
)
from google.cloud import firestore

CLIENT_PUBLIC_KEY = os.getenv("CLIENT_PUBLIC_KEY")

from random import choice

# this is a list of funny messages to tell the user to wait a few seconds
funny_waiting_messages = [
    "Please wait, I'm thinking...",
    "I'm not a calculator, so give me a second...",
    "I have to do some heavy calculations first...",
    "Let me think about that for a second...",
    "I'll get back to you in a second!",
    "I'm calculating, so hold on a second...",
    "Please give me a second to think about that...",
    "Oops, almost dropped my calculator! Give me a second...",
    "Give me a moment... I'm slow at math!",
    "I'm not the fastest brain around, sorry. Give me a few seconds...",
    "I have to do some mental calculations first...",
    "Give me a second to think about that...",
    "Please wait... I'm not very good at calculations...",
    "I'm going to need a few seconds to figure that out.",
    "I'll need a moment to think about that.",
    "Let me take a look at that real quick...",
    "Give me a minute here, I need to figure that out.",
    "Hang on, I'll get back to you in a second.",
    "Oops, almost dropped my calculator. Give me a second...",
    "Please hold on for just a second!",
    "One minute please, I'm calculating...",
    "Give me a second to think about that...",
    "Let me take a look at that real quick...",
    "Hang on a minute... I'm playing catch up!",
    "Oops, almost dropped my calculator. Give me a second...",
    "I'll get back to you in a second.",
    "Please hold on for just a second!",
    "One minute please, I'm calculating...",
    "I'll get back to you in a second.",
    "Please hold on for just a second!",
    "One minute please, I'm calculating...",
]


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
        firestore_client.collection("social_interactions").add(
            {
                "topics": topics,
                "channel_id": channel_id,
                "interaction_token": interaction_token,
                "social_software": "discord",
                "created_at": firestore.SERVER_TIMESTAMP,
            }
        )
        return jsonify(
            {
                "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                "data": {
                    "content": f"{choice(funny_waiting_messages)}",
                },
            }
        )
