import os
import json
import requests
import logging
from firebase_admin import firestore
from google.cloud.firestore import Client
from third_party.common.services import request_starter_for_service

DISCORD_APPLICATION_ID = os.getenv("DISCORD_APPLICATION_ID")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
client: Client = firestore.Client()
GET_MEMES_URL = os.getenv("GET_MEMES_URL")


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

    if "guild_id" in data["value"]["fields"]:
        guild_id = data["value"]["fields"]["guild_id"]["stringValue"]

    if "channel_id" in data["value"]["fields"]:
        channel_id = data["value"]["fields"]["channel_id"]["stringValue"]
        url = f"https://discord.com/api/v8/channels/{channel_id}"
        r = requests.get(
            url,
            headers={"Authorization": f"Bot {DISCORD_BOT_TOKEN}"},
        )
        if r.status_code != 200:
            logger.error(f"Error while getting channel: {r.status_code} {r.text}")
            return
        r = r.json()

        docs = client.collection("configs").where("guild_id", "==", guild_id).stream()
        doc = next(docs, None)

        logger.info(f"config: {doc}")
        translation = doc.to_dict().get("translation", None) if doc else None
        if not translation and doc:
            # if no global config found, try to get channel config by name
            translation = (
                doc.to_dict()
                .get("channels", {})
                .get(r["name"], {})
                .get("translation", None)
            )

    if not username:
        logger.error("No username in document. Skipping.")
        return
    user_message = ""

    if not user_message:
        docs = client.collection("api_keys").where("owner", "==", guild_id).stream()
        key = next(docs, None)
        if not key:
            user_message = (
                "😥 It seems your Langame bot was not properly configured."
                + " Please, as an admin of the Discord server, reinstall the bot"
                + " from https://discord.me/langame or authenticate with Discord at"
                + " https://langa.me/signin."
            )
        else:
            conversation_starter, um = request_starter_for_service(
                url=GET_MEMES_URL,
                api_key_id=key.id,
                logger=logger,
                topics=topics,
                fix_grammar=False,  # TODO: too slow / low quality
                parallel_completions=3,
                translated=translation,
            )
            user_message = (
                um["user_message"] if um and "user_message" in um else user_message
            )
            if conversation_starter:
                user_message = (
                    conversation_starter[0]["content"]
                    if not translation or translation == "en"
                    else conversation_starter[0]["translated"][translation]
                )

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
