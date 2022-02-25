import os
from logging import Logger
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import discord
import asyncio

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
        self.tokenizer = AutoTokenizer.from_pretrained(model)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model)
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
        self.logger.info(f"on_message {message}")

        if message.author == self.user:
            return

        channel = self.get_channel(message.channel.id)
        history = await channel.history().flatten()
        lg_m = history[1]
        self.logger.info(f"{lg_m.content}")
        if "Langame" in lg_m.author.name and lg_m.author.bot and "Topics:" in lg_m.content and "**" in lg_m.content:
            # add grin tongue reaction to the message
            await message.add_reaction("😛")
            # the user answered to a Langame conversation starter,
            # ask him a question related to his answer
            question = f"{lg_m.content}<\t>{message.content}"
            async with channel.typing():
                encoded = self.tokenizer([question], return_tensors="pt")
                self.logger.info(f"on_message:input {question}")

                response = self.model.generate(**encoded)
                response_decoded = self.tokenizer.batch_decode(response)[0]\
                    .replace("__start__ ", "")\
                    .replace(" __end__", "")\
                    .replace("</s>", "")\
                    .replace("<s> ", "")

                # upper case first char
                response_decoded = response_decoded[0].upper() + response_decoded[1:]
                self.logger.info(f"on_message:output {response_decoded}")
                await message.channel.send(response_decoded)



    async def my_background_task(self):
        await self.wait_until_ready()
        counter = 0
        # channel = self.get_channel(1234567) # channel ID goes here
        while not self.is_closed():
            counter += 1
            # await channel.send(counter)
            await asyncio.sleep(60) # task runs every 60 seconds