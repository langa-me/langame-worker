import os
from concurrent import futures
import logging
import fire
import grpc
import api_pb2
import api_pb2_grpc
from auth import RequestHeaderValidatorInterceptor
from log import RequestLoggerInterceptor
from discord_bot import DiscordBot
import signal
from firebase_admin import initialize_app, credentials, firestore
from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC
import torch
import json
import numpy as np
import traceback

def speech_to_text(data):
    # load model and tokenizer
    model_name = "facebook/wav2vec2-base-960h"
    processor = Wav2Vec2Processor.from_pretrained(model_name)
    model = Wav2Vec2ForCTC.from_pretrained(model_name)
    # tokenize
    data = np.frombuffer(data, dtype=np.uint8).astype(np.float32)
    # data_16hz = librosa.resample(data.astype(np.float32),sr,16000)
    input_values = processor(
        data,
        return_tensors="pt",
        padding="longest",
        sampling_rate=16000,
    ).input_values
    # retrieve logits
    logits = model(input_values).logits

    # take argmax and decode
    predicted_ids = torch.argmax(logits, dim=-1)
    transcription = processor.batch_decode(predicted_ids)
    return transcription


def find_names_in_sentence(inputs: str, hf_token: str):
    """
    [
        {
            "entity_group": "PER",
            "score": 0.9999847412109375,
            "word": "Wolfgang",
            "start": 11,
            "end": 19
        },
        {
            "entity_group": "LOC",
            "score": 0.9999942779541016,
            "word": "Berlin",
            "start": 34,
            "end": 40
        }
    ]
    """

    import requests

    API_URL = "https://api-inference.huggingface.co/models/xlm-roberta-large-finetuned-conll03-english"
    headers = {"Authorization": f"Bearer {hf_token}"}

    def query(payload):
        response = requests.post(API_URL, headers=headers, json=payload)
        return response.json()

    output = query({"inputs": inputs})
    # return found names in sentence
    return [e["word"] for e in output if e["entity_group"] == "PER"]


class Socialiser(api_pb2_grpc.SocialisServicer):
    """
    TODO
    """

    def __init__(self, logger, huggingface_token):
        self.logger = logger
        self.state = api_pb2.PLAYER_ADD
        self.huggingface_token = huggingface_token

    def AddPlayers(self, request: api_pb2.AddPlayersRequest, context):
        if request.text:
            self.logger.info(f"AddPlayers: {request.text}")
            players_name = ", ".join(
                find_names_in_sentence(request.text, self.huggingface_token)
            )
            return api_pb2.Game(
                text=f"The players are, {players_name}, correct?",
                state=api_pb2.PLAYER_VALIDATE,
            )
        elif request.speech:
            raise NotImplementedError
            self.logger.info(f"AddPlayers, transcripting speech")
            players_transcription = speech_to_text(request.players)[0].split(" ")
            self.logger.info(f"AddPlayers, transcription: {players_transcription}")
            return api_pb2.Game(
                text=f"Hello, the players are {players_transcription}, right?"
            )
        else:
            return api_pb2.Game(
                text="The datacenter is in trouble",
                state=api_pb2.PLAYER_ADD,
            )

    def ValidatePlayers(self, request: api_pb2.ValidatePlayersRequest, context):
        self.logger.info(f"ValidatePlayers: {request.valid}")
        if request.valid:
            return api_pb2.Game(
                text="Great, let's start the game",
                state=api_pb2.PLAYER_VALIDATE,  # TODO
            )
        else:
            return api_pb2.Game(text="Sorry, try again", state=api_pb2.PLAYER_ADD)


class SocialisServer:
    """
    TODO:
    """

    def __init__(
        self,
        huggingface_token: str,
        logger: logging.Logger = None,
    ):
        self.logger = logger
        self.logger.info("initializing...")
        self.stopped = False
        header_validator = RequestHeaderValidatorInterceptor(
            "authorization",
            "42",
            grpc.StatusCode.UNAUTHENTICATED,
            "Access denied!",
            self.logger,
        )
        logger_interceptor = RequestLoggerInterceptor(self.logger)
        self.server = grpc.server(
            futures.ThreadPoolExecutor(max_workers=10),
            interceptors=(
                header_validator,
                # logger_interceptor,
            ),
        )
        api_pb2_grpc.add_SocialisServicer_to_server(
            Socialiser(
                self.logger,
                huggingface_token,
            ),
            self.server,
        )
        self.server.add_insecure_port("[::]:50051")

    def run(self):
        """
        Run in a loop.
        """
        self.logger.info("Starting server")
        self.server.start()
        # Setup signal handler
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)
        self.server.wait_for_termination()

    def shutdown(self, _, __):
        """
        Stop the ava service.
        """
        print("\b\b\r")
        self.logger.info("Ctrl+C pressed. Stopping server...")
        self.stopped = True
        self.server.stop(0)


def serve(discord_bot_token: str, svc_path: str, parlai_websocket_url: str):
    """
    TODO
    """
    logger = logging.getLogger("socialis")
    # start socialis and the discord bot in different thread
    # import threading

    # socialis_thread = threading.Thread(target=SocialisServer(logger).run)
    # SocialisServer(logger=logger).run()
    # def d():
    #     DiscordBot(logger).run()
    # discord_thread = threading.Thread(target=d)
    # discord_thread.start()
    # socialis_thread.start()
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = svc_path
    initialize_app(
        credentials.Certificate(
            svc_path,
        )
    )
    firestore_client = firestore.Client()
    logger.info(f"initialized Firebase with project {firestore_client.project}")
    DiscordBot(logger, firestore_client, parlai_websocket_url).run(discord_bot_token)


def main():
    """
    Starts socialis.
    """
    logging.basicConfig(level=logging.INFO)

    fire.Fire(serve)


if __name__ == "__main__":
    main()
