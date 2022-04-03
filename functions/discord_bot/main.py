import re
import os
import requests
import logging
from logging import Logger
from typing import Optional, Tuple
from flask import request, jsonify, Response
from random import choice
from discord_interactions import (
    verify_key_decorator,
    InteractionType,
    InteractionResponseType,
)
from firebase_admin import firestore
from third_party.common.messages import WAITING_MESSAGES, FAILING_MESSAGES

DISCORD_CLIENT_PUBLIC_KEY = os.getenv("DISCORD_CLIENT_PUBLIC_KEY")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")


def check_langamer(
    logger: Logger,
    json_request: dict,
    refusal_message: str,
) -> Tuple[Optional[str], Optional[str], Optional[Response]]:
    """
    foo
    """
    guild_id = None
    if "guild_id" in json_request:
        guild_id = json_request["guild_id"]
    channel_id = None
    if "channel_id" in json_request:
        channel_id = json_request["channel_id"]
    if not guild_id or not channel_id:
        return (
            None,
            None,
            jsonify(
                {
                    "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                    "data": {
                        "content": "You need to send this command to a channel",
                    },
                }
            ),
        )
    # find role with "name" equal to "Langamer" in Discord API
    url = f"https://discord.com/api/v8/guilds/{guild_id}/roles"
    r = requests.get(
        url,
        headers={"Authorization": f"Bot {DISCORD_BOT_TOKEN}"},
    )
    if r.status_code != 200:
        logger.error(f"Error while getting roles: {r.status_code} {r.text}")
        return (
            None,
            None,
            jsonify(
                {
                    "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                    "data": {
                        "content": choice(FAILING_MESSAGES),
                    },
                }
            ),
        )
    r = r.json()
    # if the "Langamer" role does not exist, ask the user to create it
    langamer_role = None
    for role in r:
        if role["name"] == "Langamer":
            langamer_role = role
            break
    if not langamer_role:
        return (
            None,
            None,
            jsonify(
                {
                    "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                    "data": {
                        "content": refusal_message,
                    },
                }
            ),
        )
    return guild_id, channel_id, None


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


@verify_key_decorator(DISCORD_CLIENT_PUBLIC_KEY)
def discord_bot(_):
    """
    Answer to Discord interactions.
    """
    logger = logging.getLogger("discord_bot")
    logging.basicConfig(level=logging.INFO)
    json_request = request.get_json()

    if json_request["type"] == InteractionType.APPLICATION_COMMAND:
        logger.info("Application command received")
        logger.info(json_request)
        firestore_client = firestore.Client()

        if "data" not in json_request or "name" not in json_request["data"]:
            return jsonify(
                {
                    "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                    "data": {
                        "content": choice(FAILING_MESSAGES),
                    },
                }
            )
        if json_request["data"]["name"] == "starter":
            topics = get_discord_interaction_option_value(
                json_request, "topics", "ice breaker"
            )
            # If the user has not selected any topic, the default value is "ice breaker"
            topics = topics.split(",")
            players = get_discord_interaction_option_value(json_request, "players")
            players = [] if not players else players.split(",")
            channel_id = None
            guild_id = None
            interaction_token = json_request["token"]
            username = json_request["member"]["user"]["username"]
            if "channel_id" in json_request:
                channel_id = json_request["channel_id"]
            if "guild_id" in json_request:
                guild_id = json_request["guild_id"]
            if not channel_id:
                return jsonify(
                    {
                        "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                        "data": {
                            "content": "You need to send this command to a channel",
                        },
                    }
                )
            logger.info(
                f"Requesting conversation starter with topics: {topics} and players: {players}"
            )

            firestore_client.collection("social_interactions").add(
                {
                    "topics": topics,
                    "channel_id": channel_id,
                    "guild_id": guild_id,
                    "interaction_token": interaction_token,
                    "username": username,
                    "players": players,
                    "social_software": "discord",
                    "created_at": firestore.SERVER_TIMESTAMP,
                    "state": "to-process",
                }
            )
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
        elif json_request["data"]["name"] == "about":
            starter_description = "Send this command to a channel:\n```\n/starter topics:ice breaker,travel,whatever topic you like\n```\nYou can also add players to the **Langame** by adding the following option:\n```\n/starter players:@user1,@user2,@user3\n``` it will send you a conversation starter here 😛!"
            sub_description = (
                "Send this command to a channel:\n```\n/sub topics:ice breaker,travel,whatever topic you like\n```\n, you will receive conversation starters frequently 😛! You can also customise players to the **Langame** and the frequency",
            )
            return jsonify(
                {
                    "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                    "data": {
                        "embeds": [
                            {
                                "title": "Langame",
                                "description": "Have AI-augmented conversations with your friends.",
                                "url": "https://langa.me",
                                "color": 0x00FF00,
                                "fields": [
                                    {
                                        "name": "Get some conversation starters now!",
                                        "value": f"{starter_description}\n",
                                        "inline": False,
                                    },
                                    # {
                                    #     "name": "Get some conversation starters regularly!",
                                    #     "value": f"{sub_description}\n",
                                    #     "inline": False,
                                    # },
                                    {
                                        "name": "What is Langame?",
                                        "value": "**https://langa.me**. **Augmented conversations**.",
                                        "inline": False,
                                    },
                                ],
                            }
                        ],
                    },
                }
            )
        elif json_request["data"]["name"] == "sub":
            guild_id, channel_id, is_langamer_response = check_langamer(
                logger,
                json_request,
                'Only users with the role "Langamer" can subscribe'
                + ' to Langames. Ask your server admin to add the role "Langamer" now 😛.',
            )
            if is_langamer_response:
                return is_langamer_response

            topics = get_discord_interaction_option_value(
                json_request, "topics", "ice breaker"
            )
            topics = topics.split(",")
            players = get_discord_interaction_option_value(json_request, "players")
            # players is either "random_server" (random players on the server)
            # "random_channel" (random players on the channel)
            # "talkative_channel" (most talkative on the channel)
            frequency = get_discord_interaction_option_value(
                json_request, "frequency", "3h"
            )
            # frequency is either in minutes (30m, 120m...),
            # in hours (3h, 12h...),
            # or in days (2d, 5d...)
            # if it does not match the proper format, send an error message
            if not re.match(r"^[0-9]+[mhd]$", frequency):
                return jsonify(
                    {
                        "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                        "data": {
                            "content": "Frequency must be in minutes (30m, 120m...),"
                            + " hours (3h, 12h...), or days (2d, 5d...)",
                        },
                    }
                )

            channel_id = None
            interaction_token = json_request["token"]
            username = json_request["member"]["user"]["username"]
            if "channel_id" in json_request:
                channel_id = json_request["channel_id"]

            if not channel_id:
                return jsonify(
                    {
                        "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                        "data": {
                            "content": "You need to send this command to a channel",
                        },
                    }
                )
            logger.info(
                f"Requesting frequent conversation subscription with topics: {topics}"
                + f" and players mode: {players} at frequency: {frequency}"
            )
            existing_doc = (
                firestore_client.collection("schedules").document(channel_id).get()
            )
            message = "Understood." + (
                " Updating the current schedule." if existing_doc.exists else ""
            )
            firestore_client.collection("schedules").document(channel_id).set(
                {
                    "topics": topics,
                    "channel_id": channel_id,
                    "guild_id": guild_id,
                    "interaction_token": interaction_token,
                    "username": username,
                    "players": players,
                    "social_software": "discord",
                    "created_at": firestore.SERVER_TIMESTAMP,
                    "frequency": frequency,
                }
            )

            players_message = ""

            if players == "random_channel":
                players_message = "Will pick random players on the channel 😛"
            elif players == "talkative_channel":
                players_message = "Will try my best to pick the most talkative players on the channel 😛"
            else:
                # default random_server
                players_message = "Will pick random players on the server 😛"
            return jsonify(
                {
                    "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                    "data": {
                        "content": message
                        + f"\n\nFrequency: {frequency}."
                        + f"\nTopics: {','.join(topics)}."
                        + f"\nPlayers: {players_message}.",
                    },
                }
            )
        elif json_request["data"]["name"] == "unsub":
            guild_id, channel_id, is_langamer_response = check_langamer(
                logger,
                json_request,
                'Only users with the role "Langamer" can unsubscribe'
                + ' to Langames. Ask your server admin to add the role "Langamer" now 😛.',
            )
            if is_langamer_response:
                return is_langamer_response
            # unsubscribing from the whole guild?
            all = get_discord_interaction_option_value(json_request, "all", "False")
            # parse string "all" to boolean
            if all.lower() == "true":
                all = True
            else:
                all = False
            cta_starter_message = "\nYou can still use `/starter` to get some conversation starters manually 😛!."
            if all:
                for s in (
                    firestore_client.collection("schedules")
                    .where("guild_id", "==", guild_id)
                    .stream()
                ):
                    s.reference.delete()
                    logger.info(
                        f"Unsubscribing guild: {guild_id}, channel: {channel_id}"
                    )
                return jsonify(
                    {
                        "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                        "data": {
                            "content": f"Unsubscribed from all Langames in this server 😭.{cta_starter_message}",
                        },
                    }
                )

            logger.info(f"Unsubscribing guild: {guild_id}, channel: {channel_id}")
            firestore_client.collection("schedules").document(channel_id).delete()
            return jsonify(
                {
                    "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                    "data": {
                        "content": f"Understood. I will no longer send Langame messages to this channel 😭.{cta_starter_message}",
                    },
                }
            )
        elif json_request["data"]["name"] == "setup":
            logger.info("Setting up the bot")
            guild_id, channel_id, is_langamer_response = check_langamer(
                logger,
                json_request,
                'Only users with the role "Langamer" can setup'
                + ' Langame bot. Ask your server admin to add the role "Langamer" now 😛.',
            )
            if is_langamer_response:
                return is_langamer_response
            loquacity = get_discord_interaction_option_value(
                json_request, "loquacity", None  # Extrovert
            )
            specific_channel = get_discord_interaction_option_value(
                json_request, "channel", None
            )
            save = get_discord_interaction_option_value(json_request, "save", None)
            translation = get_discord_interaction_option_value(
                json_request, "translation", None
            )
            data = {
                "type": "discord",
                "guild_id": guild_id,
            }
            if loquacity:
                data["loquacity"] = loquacity
            if save:
                data["save"] = bool(save)
            if translation:
                data["translation"] = translation

            docs = (
                firestore_client.collection("configs")
                .where("guild_id", "==", guild_id)
                .stream()
            )
            doc = next(docs, None)

            if doc:
                if specific_channel:
                    per_channel = {}
                    if loquacity:
                        per_channel["loquacity"] = loquacity
                    if save:
                        per_channel["save"] = bool(save)
                    if translation:
                        per_channel["translation"] = translation
                    data["channels"] = {
                        **doc.to_dict().get("channels", {}),
                        specific_channel: {
                            **per_channel,
                        },
                    }
                    # remove global loquacity
                    if loquacity:
                        data["loquacity"] = firestore.DELETE_FIELD
                    # remove global save
                    if save:
                        data["save"] = firestore.DELETE_FIELD
                    # remove global translation
                    if translation:
                        data["translation"] = firestore.DELETE_FIELD
                firestore_client.collection("configs").document(doc.id).set(
                    {
                        **data,
                        "updated_at": firestore.SERVER_TIMESTAMP,
                    },
                    merge=True,
                )
            else:
                if specific_channel:
                    per_channel = {}
                    if loquacity:
                        per_channel["loquacity"] = loquacity
                    if save:
                        per_channel["save"] = bool(save)
                    if translation:
                        per_channel["translation"] = translation
                    data["channels"] = {
                        **doc.to_dict().get("channels", {}),
                        specific_channel: {
                            **per_channel,
                        },
                    }
                    # remove global loquacity
                    if loquacity:
                        del data["loquacity"]
                    # remove global save
                    if save:
                        del data["save"]
                    # remove global translation
                    if translation:
                        del data["translation"]
                firestore_client.collection("configs").add(
                    {
                        **data,
                        "created_at": firestore.SERVER_TIMESTAMP,
                    }
                )
            message_content = (
                "⚠️ Experimental ⚠️. Understood. "
                + (f"\nLoquacity set to {loquacity}" if loquacity else "")
                + (f"\nSave set to {save}" if save else "")
                + (f"\nLanguage set to {translation}" if translation else "")
                + (f" for channel {specific_channel}." if specific_channel else ".")
            )
            return jsonify(
                {
                    "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                    "data": {
                        "content": message_content,
                    },
                }
            )

        else:
            return jsonify(
                {
                    "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                    "data": {
                        "content": f"{choice(FAILING_MESSAGES)}. Try `/starter` instead.",
                    },
                }
            )
