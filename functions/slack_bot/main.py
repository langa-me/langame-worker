from flask import request
from google.cloud import firestore
import logging
from random import choice

# this is a list of funny messages to tell the user to wait a few seconds
funny_waiting_messages = [
    "Please wait, I'm thinking...",
    "I'm not a calculator, so give me a second...",
    "I have to do some heavy calculations first...",
    "Let me think about that for a second...",
    "I'll get back to you in a second!",
    "I'm calculating, so hold on a second...",
    "Please give me a second to think about that...",
    "Oops, almost dropped my calculator! Give me a second...",
    "Give me a moment... I'm slow at math!",
    "I'm not the fastest brain around, sorry. Give me a few seconds...",
    "I have to do some mental calculations first...",
    "Give me a second to think about that...",
    "Please wait... I'm not very good at calculations...",
    "I'm going to need a few seconds to figure that out.",
    "I'll need a moment to think about that.",
    "Let me take a look at that real quick...",
    "Give me a minute here, I need to figure that out.",
    "Hang on, I'll get back to you in a second.",
    "Oops, almost dropped my calculator. Give me a second...",
    "Please hold on for just a second!",
    "One minute please, I'm calculating...",
    "Give me a second to think about that...",
    "Let me take a look at that real quick...",
    "Hang on a minute... I'm playing catch up!",
    "Oops, almost dropped my calculator. Give me a second...",
    "I'll get back to you in a second.",
    "Please hold on for just a second!",
    "One minute please, I'm calculating...",
    "I'll get back to you in a second.",
    "Please hold on for just a second!",
    "One minute please, I'm calculating...",
]


def slack_bot(_):
    logger = logging.getLogger("slack_bot")
    logging.basicConfig(level=logging.INFO)
    response_url = request.form.get("response_url")
    text = request.form.get("text")
    topics = ["ice breaker"]
    if text and len(text.split(",")) > 0:
        topics = text.split(",")
    logger.info(f"Requesting conversation starter with topics: {topics}")
    firestore_client = firestore.Client()
    firestore_client.collection("social_interactions").add(
        {
            "social_software": "slack",
            "topics": topics,
            "response_url": response_url,
            "created_at": firestore.SERVER_TIMESTAMP,
        }
    )
    return {"response_type": "in_channel", "text": f"{choice(funny_waiting_messages)}"}
