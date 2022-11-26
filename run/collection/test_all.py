from logic import create_starter
from unittest import IsolatedAsyncioTestCase
from flask import request, Flask
import os
# disable pylint for docstring
# pylint: disable=C0116
# pylint: disable=C0115


class TestAll(IsolatedAsyncioTestCase):
    async def test_create_starter(self):
        app = Flask(__name__)
        # set X-Api-Key in header
        # with app.test_request_context():
        #     request.head
        #     request.headers["X-Api-Key"] = os.environ["LANGAME_API_KEY"]
        #     starter = create_starter()
        pass