from unittest import IsolatedAsyncioTestCase
import os
import time

# disable pylint for docstring
# pylint: disable=C0116
# pylint: disable=C0115
import requests
import random

IS_LOCAL = os.environ.get("IS_TESTING", "false") == "true"
URL = "http://127.0.0.1:8080" if IS_LOCAL else "https://api.langa.me"

fun_topics = [
    "fun",
    "dating",
    "big talk",
    "sex",
]

# make run/collection/local
class TestAll(IsolatedAsyncioTestCase):
    def test_create_starter(self):
        url = f"{URL}/v1/conversation/starter"
        data = {
            # pick 2 random topic
            "topics": random.sample(fun_topics, 2),
            "limit": 3,
        }
        print("querying with topics: ", data["topics"])
        r = requests.post(
            url,
            headers={"X-Api-Key": os.environ["LANGAME_API_KEY"]},
            json=data,
            timeout=10000,
        )
        assert r.status_code == 200
        data = r.json()
        print("OUTPUT:", data["results"][0]["conversation_starter"]["en"])

    def test_create_starter_scaled(self):
        start_time = time.time()
        url = f"{URL}/v1/conversation/starter"
        data = {
            "topics": [
                "dating",
                "romance",
                "love",
            ],
            "limit": 10,
        }
        r = requests.post(
            url,
            headers={"X-Api-Key": os.environ["LANGAME_API_KEY"]},
            json=data,
            timeout=10000,
        )
        assert r.status_code == 200
        data = r.json()
        end_time = time.time()
        print("Time taken: ", end_time - start_time)
        assert len(data["results"]) == 10

    def test_create_collection(self):
        url = f"{URL}/v1/conversation/collection"
        data = {
            "name": "brainy",
        }
        r = requests.post(
            url,
            headers={"X-Api-Key": os.environ["LANGAME_API_KEY"]},
            json=data,
            timeout=10000,
        )
        assert r.status_code == 200
        data = r.json()
        print("OUTPUT:", data)
# TODO test with personas
# "personas": [
#     "I am a biology student, I like to play basketball on my free time",
#     "I am a computer science student, I like to play video games on my free time. I like topics such as philosophy",
# ],