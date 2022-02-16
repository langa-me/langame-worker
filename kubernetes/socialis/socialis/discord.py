import os
import logging
from flask import Flask, request, jsonify
from firebase_admin import firestore
import discord
from discord.ext import commands
import random

app = Flask(__name__)
DISCORD_CLIENT_PUBLIC_KEY = os.getenv("DISCORD_CLIENT_PUBLIC_KEY")


@app.route("/health")
def health():
    return "OK"


description = """An example bot to showcase the discord.ext.commands extension
module.
There are a number of utility commands being showcased here."""


client = discord.Client()


@client.event
async def on_ready():
    print("Logged in as")
    print(client.user.name)
    print(client.user.id)
    print("------")


@client.event
async def on_reaction_add(reaction, user):
    print("on_reaction_add")
    print(reaction)
    print(user)
    print("------")


@client.event
async def on_message(message):
    print(message)
    if message.author == client.user:
        return

    if message.content.startswith("$hello"):
        await message.channel.send("Hello!")


if __name__ == "__main__":
    client.run("OTIwNjEyNjkzODY0NDkzMDY2.Ybm5Yg.5T-8DRdJAcGYJkj0KmYAINxOR2s")
    # app.run(debug=True, host="0.0.0.0")
