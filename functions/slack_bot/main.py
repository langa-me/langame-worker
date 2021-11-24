from flask import request
from google.cloud import pubsub_v1
import logging

def slack_bot(_):
    logging.basicConfig(level=logging.INFO)
    json_data = request.get_json()
    response_url = request.form.get("response_url")
    topics = ["ice breaker"]
    if json_data and "text" in json_data and len(json_data["text"].split(",")) > 0:
        topics = json_data["text"]
    logging.info(f"Requesting conversation starter with topics: {topics}")
    publisher = pubsub_v1.PublisherClient()
    publish_future = publisher.publish(
        "social_bot", str.encode(topics), social_software="slack", response_url=response_url
    )
    publish_future.result()
    return f"Will provide you a conversation starter about {','.join(topics)}"
