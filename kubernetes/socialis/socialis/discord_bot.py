import os
from logging import Logger
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, AutoModelForCausalLM
import discord
import asyncio
from firebase_admin import firestore
from datetime import datetime
import torch
import re


class DiscordBot(discord.Client):
    """
    foo
    """

    def __init__(self, logger: Logger, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logger
        model = "facebook/blenderbot-400M-distill"
        model = "facebook/blenderbot_small-90M"
        model = "facebook/blenderbot-1B-distill"
        model = "microsoft/DialoGPT-small"
        model = "microsoft/DialoGPT-large"
        self.tokenizer = AutoTokenizer.from_pretrained(model)
        # self.model = AutoModelForSeq2SeqLM.from_pretrained(model)
        self.model = AutoModelForCausalLM.from_pretrained(model)
        # create the background task and run it in the background
        self.bg_task = self.loop.create_task(self.my_background_task())

    async def on_ready(self):
        self.logger.info(f"Logged in as {self.user.name}:{self.user.id}")

    async def on_reaction_add(self, reaction, user):
        self.logger.info(f"on_reaction_add {reaction}:{user}")

    async def on_message(self, message):
        """
        foo
        """
        self.logger.info(
            f"on_message {message.channel.name} {message.author.name} {message.content}"
        )

        if message.author == self.user:
            return

        channel = self.get_channel(message.channel.id)
        history = await channel.history().flatten()
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
            and "Langame" in lg_m.author.name
            and lg_m.author.bot
            # and "Topics:" in lg_m.content
            # and "**" in lg_m.content
            and len(message.content) > 1
        ):

            # add grin tongue reaction to the message
            await message.add_reaction("😛")
            # the user answered to a Langame conversation starter,
            # ask him a question related to his answer
            last_five_messages_before_lg_m = history[
                index_of_lg_m : index_of_lg_m + 2
            ]

            question = list(
                reversed([e.content for e in last_five_messages_before_lg_m])
            ) + [message.content]
            async with channel.typing():
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
                    gen[:, new_user_input_ids.shape[-1] :][0], skip_special_tokens=True
                )

                # upper case first char
                # response_decoded = response_decoded[0].upper() + response_decoded[1:]
                # remove question from response
                # response_decoded = response_decoded.replace(
                #     question, ""
                # ).strip()
                self.logger.info(f"on_message:output {response_decoded}")
                # if empty message return
                if not response_decoded:
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
