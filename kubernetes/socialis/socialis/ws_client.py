""" Stream data from the WebSocket and update the Beta posterior parameters online. """

from typing import Any, Callable, Optional
from grpc import Future
import tornado.ioloop
import tornado.websocket
from tornado.ioloop import IOLoop
from tornado.websocket import WebSocketClientConnection
import logging
import json


class WebSocketClient:
    def __init__(
        self,
        io_loop: IOLoop,
        url: str,
        on_message_callback: Callable[[str], None],
        sender_id: str,
        on_close: Optional[Callable[[], None]] = None,
    ):
        self.connection: Optional[WebSocketClientConnection] = None
        self.io_loop = io_loop
        self.logger = logging.getLogger(__name__)
        self.url = url
        self.on_message_callback = on_message_callback
        self.sender_id = sender_id
        self.on_close = on_close
        self.last_message = None

    def start(self):
        self.connect_and_read()

    def stop(self):
        self.io_loop.stop()

    def connect_and_read(self):
        self.logger.info("Connecting to websocket...")
        tornado.websocket.websocket_connect(
            url=self.url,
            callback=self.maybe_retry_connection,
            on_message_callback=self.on_message,
            ping_interval=10,
            ping_timeout=30,
        )

    def maybe_retry_connection(self, future: Future) -> None:
        try:
            self.connection = future.result()
        except Exception as e:
            self.logger.warning("Could not reconnect, retrying in 3 seconds, err: " + str(e))
            self.io_loop.call_later(3, self.connect_and_read)

    def on_close(self):
        self.on_close()

    def on_message(self, message):
        # print(message)
        if message is None:
            self.logger.info("Disconnected, reconnecting...")
            self.connect_and_read()
            return
        message = json.loads(message)
        if "Welcome to the Langame Ava overworld." in message.get("text", ""):
            self.connection.write_message(
                json.dumps(
                    {"mid": 0, "sender": {"id": self.sender_id}, "text": "begin",}
                )
            )
            return
        if "Welcome to Langame ava. Type [DONE]" in message.get("text", ""):
            if self.last_message:
                self.connection.write_message(self.last_message)
            return

        if "System: The conversation bot going" in message.get("text", ""):
            self.connection.write_message(
                json.dumps(
                    {
                        "mid": -1,
                        "sender": {"id": self.sender_id},
                        "text": "My master unplugged me from the world. I'm going to die. Praise the sun.",
                    }
                )
            )
            return

        # load json
        # message = json.loads(message)
        # if empty message return
        if not message or "text" not in message or len(message["text"]) < 2:
            return
        message = message["text"]

        self.on_message_callback(message)

    def send_message(self, message_id: str, message_content: str):
        self.last_message = json.dumps(
            {
                "mid": message_id,
                "sender": {"id": self.sender_id},
                "text": message_content,
            }
        )
        self.connection.write_message(self.last_message)

