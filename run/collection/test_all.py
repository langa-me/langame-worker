from unittest import IsolatedAsyncioTestCase
import os

# disable pylint for docstring
# pylint: disable=C0116
# pylint: disable=C0115
import requests

# make run/collection/local
class TestAll(IsolatedAsyncioTestCase):
    async def test_create_starter(self):

        url = "http://127.0.0.1:8080/v1/conversation/starter"
        data = {
            "personas": [
                "I am a biology student, I like to play basketball on my free time",
                "I am a computer science student, I like to play video games on my free time. I like topics such as philosophy",
            ]
        }
        r = requests.post(
            url,
            headers={"X-Api-Key": os.environ["LANGAME_API_KEY"]},
            json=data,
            timeout=10000,
        )
        assert r.status_code == 200
