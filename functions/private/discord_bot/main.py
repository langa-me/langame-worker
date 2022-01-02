import os
import logging
from datetime import datetime, timedelta
from typing import Optional
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


def get_discord_interaction_option_value(
    json_request: dict, option_name: str, default_value: Optional[str] = None
) -> Optional[str]:
    """
    Try to get the value of a specific option from the request.
    https://discord.com/developers/docs/interactions/application-commands#slash-commands-example-interaction
    :param json_request: The request in JSON format.
    :param option_name: The name of the option to get the value of.
    :param default_value: The default value to return if the option is not found.
    :return: The value of the option or None if it does not exist.
    """
    if (
        "data" in json_request
        and "options" in json_request["data"]
        and len(json_request["data"]["options"]) > 0
        # There is an options with property "name" equal to option_name
        and any(
            option["name"] == option_name for option in json_request["data"]["options"]
        )
        # There is an options with property "value" different of None
        and any(
            option["value"] is not None for option in json_request["data"]["options"]
        )
    ):
        return next(
            option["value"]
            for option in json_request["data"]["options"]
            if option["name"] == option_name
        )
    return default_value


@verify_key_decorator(CLIENT_PUBLIC_KEY)
def discord_bot(_):
    logger = logging.getLogger("discord_bot")
    logging.basicConfig(level=logging.INFO)
    json_request = request.get_json()
    if json_request["type"] == InteractionType.APPLICATION_COMMAND:
        logger.info("Application command received")
        logger.info(json_request)
        topics = get_discord_interaction_option_value(
            json_request, "topics", "ice breaker"
        )
        # If the user has not selected any topic, the default value is "ice breaker"
        topics = topics.split(",")
        players = get_discord_interaction_option_value(json_request, "players")
        players = [] if not players else players.split(",")
        channel_id = None
        interaction_token = json_request["token"]
        username = json_request["member"]["user"]["username"]
        if "channel_id" in json_request:
            channel_id = json_request["channel_id"]
        if not channel_id:
            return jsonify(
                {
                    "response_type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                    "text": "You need to send this command to a channel",
                }
            )
        logger.info(f"Requesting conversation starter with topics: {topics} and players: {players}")
        firestore_client = firestore.Client()

        firestore_client.collection("social_interactions").add(
            {
                "topics": topics,
                "channel_id": channel_id,
                "interaction_token": interaction_token,
                "username": username,
                "players": players,
                "social_software": "discord",
                "created_at": firestore.SERVER_TIMESTAMP,
                "state": "to-process",
            }
        )
        # https://discord.com/developers/docs/resources/webhook#execute-webhook
        # requests.post(
        #     f"https://discord.com/api/v8/channels/{channel_id}/typing",
        # )
        # merge players into a comma separated string and ensure that each
        # players starts with @ to notify the user
        players_string = ""
        if players:
            players_string = "\nPlayers: " + ",".join(players) + "."
        return jsonify(
            {
                "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                "data": {
                    "content": f"Topics: {','.join(topics)}{players_string}\n{choice(WAITING_MESSAGES)}",
                },
            }
        )
