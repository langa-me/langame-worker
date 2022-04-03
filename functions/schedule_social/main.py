import os
import json
import requests
import logging
from datetime import datetime
from random import sample, randint
from firebase_admin import firestore
from google.cloud.firestore import Client
from third_party.common.discord import get_most_talkative_players_from_channel
from third_party.common.services import request_starter_for_service
import time
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GET_MEMES_URL = os.getenv("GET_MEMES_URL")

# TODO: on failure, DM the admin
# TODO: wrap into try except, send error to GCP etc.?


def schedule_social(_, ctx):
    """
    Send regular Langames
    """
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
        data = schedule.to_dict()
        guild_id = data.get("guild_id")
        if not guild_id:
            logger.warning("No guild_id for schedule: %s", schedule.id)
            continue
        channel_id = data.get("channel_id")
        if not channel_id:
            logger.warning("No channel_id for schedule: %s", schedule.id)
            continue

        url = f"https://discord.com/api/v8/channels/{channel_id}"
        channel_response = requests.get(
            url,
            headers={"Authorization": f"Bot {DISCORD_BOT_TOKEN}"},
        )
        if channel_response.status_code != 200:
            logger.warning(f"Error while getting channel: {channel_response.status_code} {channel_response.text}")
            # maybe private channel :)
            continue
        channel_response = channel_response.json()

        docs = (
            firestore_client.collection("configs")
            .where("guild_id", "==", guild_id)
            .stream()
        )
        doc = next(docs, None)

        logger.info(f"config: {doc}")
        translation = doc.to_dict().get("translation", None) if doc else None
        if not translation and doc:
            # if no global config found, try to get channel config by name
            translation = (
                doc.to_dict()
                .get("channels", {})
                .get(channel_response["name"], {})
                .get("translation", None)
            )
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
        now = datetime.now()
        if frequency is None:
            logger.warning(f"No frequency set for schedule {schedule.id}. Skipping.")
            continue
        # if there are no last langame or the difference between now and last langame
        # is superior to the frequency, send a new Langame
        if last_langame is None:
            # i.e. first schedule properly start after frequency
            last_langame = data.get("created_at")
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
            # players is either "random_server" (random players on the server)
            # "random_channel" (random players on the channel)
            # "talkative_channel" (most talkative on the channel)
            players = data.get("players")
            if players == "random_channel":
                raise NotImplementedError("random_channel not implemented yet")
            elif players == "talkative_channel":
                most_talkative_players = get_most_talkative_players_from_channel(
                    channel_id
                )
                if len(most_talkative_players) == 0:
                    break
                # sample from most talkative players
                players = sample(
                    most_talkative_players,
                    k=randint(2, 3)
                    if len(most_talkative_players) > 2
                    else len(most_talkative_players),
                )
                # turn players into a list of ids
                players = [player.get("id") for player in players]
            else:
                # (default to random_server)
                members = requests.get(
                    # https://discord.com/developers/docs/resources/guild#list-guild-members
                    f"https://discord.com/api/v8/guilds/{guild_id}/members?limit=1000",  # TODO: paginate
                    headers={"Authorization": f"Bot {DISCORD_BOT_TOKEN}"},
                )
                # gettings roles, to filter bots
                roles = requests.get(
                    f"https://discord.com/api/v8/guilds/{guild_id}/roles",  # TODO: paginate
                    headers={"Authorization": f"Bot {DISCORD_BOT_TOKEN}"},
                )
                if members.status_code != 200 or roles.status_code != 200:
                    logger.error(
                        f"Failed to get the list of players for guild {guild_id}. Skipping. {members.text}",
                    )
                    continue
                members = members.json()
                roles = roles.json()
                logger.info(f"Got the list of players for guild {guild_id}: {members}")
                # find any role named "Bot"
                bot_role = next(
                    (role for role in roles if role.get("name") == "Bot"),
                    None,
                )
                players = []
                for member in members:
                    # filter out bots (role "Bot") or ["user"]["bot"]=True
                    if member.get("user", {}).get("bot", False) or (
                        bot_role and bot_role.get("id") in member.get("roles")
                    ):
                        continue
                    member_id = member.get("user", {}).get("id", None)
                    if member_id:
                        players.append(member_id)
                players = sample(
                    players,
                    k=randint(2, 3) if len(players) > 2 else len(players),
                )
            if not players:
                logger.warning(f"No players set for schedule {schedule.id}. Skipping.")
                continue
            # turn into <@id>
            players = [f"<@{player}>" for player in players]
            logger.info(f"Players selected: {players}")
            user_message = ""
            docs = (
                firestore_client.collection("api_keys")
                .where("owner", "==", guild_id)
                .stream()
            )
            key = next(docs, None)
            if not key:
                user_message = (
                    "😥 It seems your Langame bot was not properly configured."
                    + " Please, as an admin of the Discord server, reinstall the bot"
                    + " from https://discord.me/langame or authenticate with Discord at"
                    + " https://langa.me/signin."
                )
            else:
                starter, um = request_starter_for_service(
                    url=GET_MEMES_URL,
                    api_key_id=key.id,
                    logger=logger,
                    topics=topics,
                    fix_grammar=False,  # TODO: too slow / low quality
                    parallel_completions=3,
                    translated=translation,
                )
                if starter:
                    user_message = (
                        starter[0]["content"]
                        if not translation or translation == "en"
                        else starter[0]["translated"][translation]
                    )
                else:
                    # we only send errors of configuration to channel, otherwise
                    # just continue next schedule
                    logger.warning(
                        f"No starter found for schedule {schedule.id}. Skipping. {um}"
                    )
                    continue
            logger.info(
                f"Will send the Langame to {channel_id}. Starter: {user_message}"
            )
            message_response = requests.post(
                f"https://discord.com/api/v8/channels/{channel_id}/messages",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
                },
                data=json.dumps(
                    {
                        "content": f"Topics: {','.join(topics)}."
                        + f"\nPlayers: {','.join(players)}."
                        + f"\n\n**{user_message}**",
                        "allowed_mentions": {
                            "parse": ["users"],
                        },
                    }
                ),
            )
            if message_response.status_code != 200:
                logger.error(
                    f"Failed to send the Langame to channel {channel_id}. Skipping. {channel_response.text}"
                )
                continue
            # update the last langame
            schedule.reference.set(
                {
                    "lastLangame": firestore.SERVER_TIMESTAMP,
                    "lastSampledPlayers": players,
                },
                merge=True,
            )
            # add a social_interactions entry
            firestore_client.collection("social_interactions").add(
                {
                    "guild_id": guild_id,
                    "channel_id": channel_id,
                    "created_at": firestore.SERVER_TIMESTAMP,
                    "schedule_id": schedule.id,
                    "state": "delivered",
                    "social_software": "discord",
                    "topics": topics,
                    "players": players,
                    "user_message": user_message,
                }
            )
            # rate limit AI APIs
            time.sleep(20)
        else:
            logger.info(
                f"No Langame to send for schedule {schedule.id} because"
                + f" the last one was sent less than {frequency_seconds} seconds ago."
            )
