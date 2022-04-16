import logging
from logging import Logger
from typing import Any, List
import discord
import asyncio
from firebase_admin import firestore
from datetime import datetime
import threading
from google.cloud.firestore import Client, DocumentSnapshot
from socialis.ws_client import WebSocketClient
from deep_translator import GoogleTranslator
from discord import Message
import tornado.ioloop
import tornado.websocket


def is_message_author_langame(message) -> bool:
    return (
        "Langame" == message.author.name
        or "Langame-alpha" == message.author.name
        and message.author.bot
    )


def is_conversation_starter(message) -> bool:
    return is_message_author_langame(message) and "Topics" in message.content


class DiscordBot(discord.Client):
    """
    foo
    """

    def __init__(
        self,
        logger: Logger,
        firestore_client: Client,
        parlai_websocket_url: str,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.logger = logger
        self.firestore_client = firestore_client
        self.parlai_websocket_url = parlai_websocket_url
        self.parlai_websockets: dict[str, WebSocketClient] = {}
        self.discord_configs = {}

        # Create an Event for notifying main thread.
        self.callback_done = threading.Event()
        doc_ref = self.firestore_client.collection("configs").where(
            "type", "==", "discord"
        )
        self.doc_watch = doc_ref.on_snapshot(self.on_snapshot)

        # create the background task and run it in the background
        self.bg_task = self.loop.create_task(self.my_background_task())

    def on_snapshot(self, doc_snapshot: List[DocumentSnapshot], changes, read_time):
        """
        ZZ.
        :param doc_snapshot:
        :param changes:
        :param read_time:
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        for doc in doc_snapshot:
            data_dict = doc.to_dict()
            self.logger.info(
                f"Received document snapshot: id: {doc.id},"
                + f" data: {data_dict}, changes: {changes}, read_time: {read_time}"
            )
            self.discord_configs[data_dict["guild_id"]] = data_dict
        self.logger.info(f"Updated Discord guild configs: {self.discord_configs}")

    async def on_ready(self):
        self.logger.info(f"Logged in as {self.user.name}:{self.user.id}")

    async def on_reaction_add(self, reaction, user):
        self.logger.info(f"on_reaction_add {reaction}:{user}")

    async def on_message(self, message):
        """
        foo
        """
        self.logger.info(
            f"on_message {message.guild.name} {message.channel.name} {message.author.name} {message.content}"
        )

        if message.author == self.user:
            return

        socket_id = hash(message.channel.id + message.guild.id)
        if socket_id not in self.parlai_websockets:
            # Create an event loop (what Tornado calls an IOLoop).
            io_loop = tornado.ioloop.IOLoop.current()

            def on_websocket_message(response: str):
                # need translation?
                if translation != "en":
                    response = GoogleTranslator(target=translation).translate(response)
                    self.logger.info(f"on_message:output:translation {response}")
                # TODO async?
                self.logger.info(f"on_message:sending to discord {response}")
                io_loop.add_callback(lambda: message.channel.send(response))

            def on_close():
                del self.parlai_websockets[socket_id]

            self.parlai_websockets[socket_id] = WebSocketClient(
                io_loop,
                self.parlai_websocket_url,
                on_websocket_message,
                socket_id,
                on_close,
            )
            io_loop.add_callback(self.parlai_websockets[socket_id].start)

        channel = self.get_channel(message.channel.id)
        guild_id = channel.guild.id
        config = self.discord_configs.get(
            str(guild_id), {"loquacity": "1", "translation": "en", "save": False,},
        )
        db = firestore.Client()
        now = datetime.now()
        self.logger.info(f"config: {config}")
        loquacity = config.get("loquacity", None)
        if not loquacity:
            # if no global config found, try to get channel config by name
            loquacity = (
                config.get("channels", {}).get(channel.name, {}).get("loquacity", "1")
            )
        if loquacity == "0":
            self.logger.info(f"Loquacity is 0 for {channel.name}")
            return
        translation = config.get("translation", None)
        if not translation:
            # if no global config found, try to get channel config by name
            translation = (
                config.get("channels", {})
                .get(channel.name, {})
                .get("translation", "en")
            )
        save = config.get("save", None)
        if not save:
            # if no global config found, try to get channel config by name
            save = config.get("channels", {}).get(channel.name, {}).get("save", False)
        self.logger.info(
            f"loquacity: {loquacity} translation: {translation} save: {save}"
        )
        history = await channel.history().flatten()
        hundred_history = history[-20:]
        # count messages from langame in history
        langame_messages_lately = len(
            [m for m in hundred_history if is_message_author_langame(m)]
        )
        lg_m = history[1]
        index_of_lg_m = 1
        referenced_message = [
            e
            for e in history
            if message.reference and e.id == message.reference.message_id
        ]
        if referenced_message:
            self.logger.info(
                f"on_message using referenced_message {referenced_message}"
            )
            lg_m = referenced_message[0]
            index_of_lg_m = history.index(lg_m)

        # if this channel answers to Langame are to be saved
        # and this is an answer to a conversation starter, save
        if save and is_conversation_starter(lg_m) and len(message.content) > 1:
            self.logger.info(
                f"on_message saving {message.content} to {guild_id}/{channel.name}"
            )
            d = {
                "createdAt": now,
                "guildId": str(guild_id),
                "guildName": channel.guild.name,
                "channelId": str(channel.id),
                "channelName": channel.name,
                "conversation": [
                    {
                        "author": message.author.name,
                        "bot": message.author.bot,
                        "content": message.content,
                        "createdAt": message.created_at,
                        "editedAt": message.edited_at,
                    },
                    {
                        "author": "Langame",
                        "bot": True,
                        "content": lg_m.content,
                        "createdAt": lg_m.created_at,
                        "editedAt": lg_m.edited_at,
                    },
                ],
            }
            self.logger.info(f"on_message: saving to firestore document {d}")
            _, doc_ref = db.collection("saved_conversations").add(d)
            firestore_url = (
                "https://console.cloud.google.com/firestore/data/"
                + f"saved_conversations/{doc_ref.id}?project={self.firestore_client.project}"
            )
            self.logger.info(f"on_message saved {firestore_url}")
            self.logger.info(f"data: {doc_ref.get().to_dict()}")

        if loquacity == "1":
            # more than 10% of messages, ignore
            if langame_messages_lately > round(len(hundred_history) * 0.1):
                self.logger.info(
                    f"Loquacity is 1 and Langame sent {langame_messages_lately}"
                    + " messages recently,"
                    + f" that's above 10% of {len(hundred_history)} messages"
                )
                return
        elif loquacity == "2":
            if langame_messages_lately > round(len(hundred_history) * 0.3):
                self.logger.info(
                    f"Loquacity is 2 and Langame sent {langame_messages_lately}"
                    + " messages recently,"
                    + f" that's above 30% of {len(hundred_history)} messages"
                )
                return
        elif loquacity == "3":
            if langame_messages_lately > 200:  # round(len(hundred_history) * 0.7):
                self.logger.info(
                    f"Loquacity is 3 and Langame sent {langame_messages_lately}"
                    + " messages recently,"
                    + f" that's above 40% of {len(hundred_history)} messages"
                )
                return

        if (
            message.content
            and is_message_author_langame(lg_m)
            and len(message.content) > 1
        ):

            # add grin tongue reaction to the message
            await message.add_reaction("😛")
            # the user answered to a Langame conversation starter,
            # ask him a question related to his answer
            last_five_messages_before_lg_m = history[index_of_lg_m : index_of_lg_m + 2]

            question = list(
                reversed(
                    [
                        ("Me: " if is_message_author_langame(e) else "You: ")
                        + e.content
                        for e in last_five_messages_before_lg_m
                        # TODO better hack
                        if len(e.content) > 2 and "https" not in e.content
                    ]
                )
            ) + [message.content]
            if len(question) == 0:
                self.logger.info(
                    f"No text found in last five messages {last_five_messages_before_lg_m}"
                )
                return
            async with channel.typing():
                if "shut up" in message.content.lower():
                    await channel.send(
                        "If you wish to reduce my loquacity, please try /setup"
                    )
                    return

                self.logger.info(f"on_message:input {message.content}")

                message_content = GoogleTranslator(target="en").translate(
                    message.content
                )

                self.parlai_websockets[socket_id].send_message(
                    message.id, message_content
                )

    async def my_background_task(self):
        await self.wait_until_ready()
        counter = 0
        # channel = self.get_channel(1234567) # channel ID goes here
        while not self.is_closed():
            counter += 1
            # await channel.send(counter)
            await asyncio.sleep(60)  # task runs every 60 seconds
