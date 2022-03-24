import os
from logging import Logger
from typing import List
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, AutoModelForCausalLM
import discord
import asyncio
from firebase_admin import firestore
from datetime import datetime
import torch
import re
import threading
from google.cloud.firestore import Client, DocumentSnapshot


def is_message_author_langame(message) -> bool:
    return "Langame" in message.author.name and message.author.bot


class DiscordBot(discord.Client):
    """
    foo
    """

    def __init__(self, logger: Logger, firestore_client: Client, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logger
        self.firestore_client = firestore_client
        self.discord_configs = {}
        model = "facebook/blenderbot-400M-distill"
        model = "facebook/blenderbot_small-90M"
        model = "facebook/blenderbot-1B-distill"
        # model = "microsoft/DialoGPT-small"
        # model = "microsoft/DialoGPT-large"
        self.tokenizer = AutoTokenizer.from_pretrained(model)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model)
        # self.model = AutoModelForCausalLM.from_pretrained(model)

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
            f"on_message {message.guild.id} {message.channel.name} {message.author.name} {message.content}"
        )

        if message.author == self.user:
            return

        config = self.discord_configs.get(
            str(message.guild.id),
            {
                "loquacity": "1",
            },
        )
        self.logger.info(f"config: {config}")
        channel = self.get_channel(message.channel.id)
        loquacity = config.get("loquacity", None)
        if not loquacity:
            # if no global config found, try to get channel config by name
            loquacity = config.get("channels", {}).get(channel.name, {}).get("loquacity", "1")
        self.logger.info(f"loquacity: {loquacity}")
        if loquacity == "0":
            self.logger.info(f"Loquacity is 0 for {channel.name}")
            return
        history = await channel.history().flatten()
        # count messages from langame in history
        langame_messages_lately = len(
            [m for m in history if is_message_author_langame(m)]
        )
        if loquacity == "1":
            if langame_messages_lately > 5:
                self.logger.info(
                    f"Loquacity is 1 and Langame sent {langame_messages_lately}"
                    + " messages recently, aborting"
                )
                return
        elif loquacity == "2":
            if langame_messages_lately > 10:
                self.logger.info(
                    f"Loquacity is 2 and Langame sent {langame_messages_lately}"
                    + " messages recently, aborting"
                )
                return
        elif loquacity == "3":
            if langame_messages_lately > 15:
                self.logger.info(
                    f"Loquacity is 3 and Langame sent {langame_messages_lately}"
                    + " messages recently, aborting"
                )
                return
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
                        e.content
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

                question_with_eos = (self.tokenizer.eos_token + "").join(question)
                new_user_input_ids = self.tokenizer.encode(
                    question_with_eos + self.tokenizer.eos_token, return_tensors="pt"
                )
                self.logger.info(f"on_message:input {question}")

                # gen = self.model.generate(**new_user_input_ids)

                gen = self.model.generate(
                    new_user_input_ids,
                    max_length=1000,
                    pad_token_id=self.tokenizer.eos_token_id,
                )

                # response_decoded = (
                #     self.tokenizer.batch_decode(gen)[0]
                #     .replace("__start__ ", "")
                #     .replace(" __end__", "")
                #     .replace("</s>", "")
                #     .replace("<s> ", "")
                #     .replace("<|endoftext|>", "\n")
                # )
                response_decoded = self.tokenizer.decode(
                    gen[0], skip_special_tokens=True
                )

                # upper case first char
                # response_decoded = response_decoded[0].upper() + response_decoded[1:]
                # remove question from response
                # response_decoded = response_decoded.replace(
                #     question, ""
                # ).strip()
                self.logger.info(f"on_message:output {response_decoded}")
                # if empty message return
                if not response_decoded or len(response_decoded) < 2:
                    return
                await message.channel.send(response_decoded)
            # insert conversation in firestore
            db = firestore.Client()
            now = datetime.now()
            local_now = now.astimezone()
            _, doc_ref = db.collection("conversations").add(
                {
                    "confirmed": False,
                    "createdAt": now,
                    "updatedAt": now,
                    "origin": "discord",
                    "conversation": [
                        {
                            "author": e.author.name,
                            "bot": e.author.bot,
                            "content": e.content,
                            "createdAt": e.created_at,
                            "editedAt": e.edited_at,
                        }
                        for e in reversed(last_five_messages_before_lg_m)
                    ]
                    + [
                        {
                            "author": message.author.name,
                            "bot": message.author.bot,
                            "content": message.content,
                            "createdAt": message.created_at,
                            "editedAt": message.edited_at,
                            # "reactions": message.reactions,
                        },
                        {
                            "author": "Langame",
                            "bot": True,
                            "content": response_decoded,
                            "createdAt": local_now,
                            "editedAt": local_now,
                            # "reactions": [],
                        },
                    ],
                }
            )
            self.logger.info(f"on_message:firestore:conversations {doc_ref.id}")

    async def my_background_task(self):
        await self.wait_until_ready()
        counter = 0
        # channel = self.get_channel(1234567) # channel ID goes here
        while not self.is_closed():
            counter += 1
            # await channel.send(counter)
            await asyncio.sleep(60)  # task runs every 60 seconds
