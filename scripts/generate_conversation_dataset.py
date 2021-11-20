"""
This is a basic websocket Python client that connects to a websocket server.
"""

import fire
import websocket
import json

def talk():
    """
    Connect to a websocket server and send a message.
    """
    ws = websocket.WebSocket()
    ws.connect("ws://localhost:8080")
    # if succeed, loop for user input to send to the websocket
    while True:
        message = input("Enter a message: ")
        ws.send(json.dumps({"text": message}))
        result = ws.recv()
        print(result)
    ws.close()


if __name__ == "__main__":
    fire.Fire(talk)
