import websocket
import json

def talk():
    ws = websocket.WebSocket()
    ws.connect("ws://localhost:8082")
    # if succeed, loop for user input to send to the websocket
    while True:
        message = input("Enter a message: ")
        ws.send(json.dumps({"text": message}))
        result = ws.recv()
        print(result)
    ws.close()

talk()
