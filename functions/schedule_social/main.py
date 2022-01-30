import os
import json
import requests
import logging
from datetime import datetime
from random import choices, randint
from firebase_admin import firestore
from google.cloud.firestore import Client
from third_party.common.services import request_starter

DISCORD_APPLICATION_ID = os.getenv("DISCORD_APPLICATION_ID")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# TODO: on failure, DM the admin


def schedule_social(_, ctx):
    logger = logging.getLogger("schedule_social")
    logging.basicConfig(level=logging.INFO)
    # for each document in "schedules" collection, check the last Langame sent,
    # check if the different with the requested frequency requires a new Langame
    # if so, send a new Langame

    firestore_client: Client = firestore.Client()
    for schedule in (
        firestore_client.collection("schedules")
        .where("social_software", "==", "discord")
        .stream()
    ):
        guild_id = schedule.id
        data = schedule.to_dict()
        # frequency is either in minutes (30m, 120m...),
        # in hours (3h, 12h...),
        # or in days (2d, 5d...)
        frequency = data.get("frequency")
        # convert frequency to seconds
        frequency_seconds = 0
        if frequency.endswith("m"):
            frequency_seconds = int(frequency[:-1]) * 60
        elif frequency.endswith("h"):
            frequency_seconds = int(frequency[:-1]) * 60 * 60
        elif frequency.endswith("d"):
            frequency_seconds = int(frequency[:-1]) * 60 * 60 * 24
        else:
            logger.warning("Frequency not recognized: %s", frequency)
            continue
        last_langame = data.get("lastLangame")
        channel_id = data.get("channel_id")
        if not channel_id:
            logger.warning("No channel_id for schedule: %s", schedule.id)
            continue
        now = datetime.now()
        if frequency is None:
            logger.warning(f"No frequency set for schedule {schedule.id}. Skipping.")
            continue
        # if there are no last langame or the difference between now and last langame
        # is superior to the frequency, send a new Langame
        if (
            last_langame is None
            or (now - datetime.fromtimestamp(last_langame.timestamp())).total_seconds()
            > frequency_seconds
        ):
            # send a new Langame
            logger.info(f"Sending a new Langame for schedule {schedule.id}.")
            # get the list of topics
            topics = data.get("topics")
            if topics is None:
                logger.warning(f"No topics set for schedule {schedule.id}. Skipping.")
                continue
            # get the list of players
            players = data.get("players")
            if not players:
                r = requests.get(
                    # https://discord.com/developers/docs/resources/guild#list-guild-members
                    f"https://discord.com/api/v8/guilds/{guild_id}/members?limit=1000",  # TODO: paginate
                    headers={"Authorization": f"Bot {DISCORD_BOT_TOKEN}"},
                )
                if r.status_code != 200:
                    logger.error(
                        f"Failed to get the list of players for guild {guild_id}. Skipping. {r.text}",
                    )
                    continue
                r = r.json()
                logger.info(f"Got the list of players for guild {guild_id}: {r}")
                players = choices(
                    list(set([player.get("user", {}).get("id") for player in r])),
                    k=randint(2, 3),
                )
                logger.info(f"Players selected: {players}")
                # turn into <@id>
                players = [f"<@{player}>" for player in players]
            if not players:
                logger.warning(f"No players set for schedule {schedule.id}. Skipping.")
                continue
            # send the message
            starter, user_message = request_starter(
                logger,
                firestore_client,
                topics,
            )
            if starter is None:
                logger.warning(
                    f"No starter found for schedule {schedule.id}. Skipping. {user_message}"
                )
                continue
            logger.info(f"Will send the Langame to {channel_id}. Starter: {starter}")
            r = requests.post(
                f"https://discord.com/api/v8/channels/{channel_id}/messages",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
                },
                data=json.dumps(
                    {
                        "content": f"Topics: {','.join(topics)}."
                        + f"\nPlayers: {','.join(players)}."
                        + f"\n\n**{starter}**",
                        "allowed_mentions": {
                            "parse": ["users"],
                        },
                    }
                ),
            )
            if r.status_code != 200:
                logger.error(
                    f"Failed to send the Langame to channel {channel_id}. Skipping. {r.text}"
                )
                continue
            # update the last langame
            schedule.reference.set(
                {
                    "lastLangame": firestore.SERVER_TIMESTAMP,
                    "lastSampledPlayers": players,
                }, merge=True,
            )
        else:
            logger.info(
                f"No Langame to send for schedule {schedule.id} because"
                + f" the last one was sent less than {frequency_seconds} seconds ago."
            )
