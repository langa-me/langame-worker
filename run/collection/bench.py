import os

# disable pylint for docstring
# pylint: disable=C0116
# pylint: disable=C0115
import requests
import random
from pyinstrument import Profiler

IS_LOCAL = os.environ.get("IS_TESTING", "false") == "true"
URL = "http://127.0.0.1:8080" if IS_LOCAL else "https://api.langa.me"

fun_topics = [
    "fun",
    "dating",
    "big talk",
    "sex",
    "romance",
    "travel",
    "cooking",
    "science",
]


def request():
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



profiler = Profiler()
REPEAT = 3

for i in range(REPEAT):
    profiler.start()
    request()
    profiler.stop()
    profiler.print()
