from concurrent.futures import ThreadPoolExecutor
import logging
import threading
import time
from typing import Iterable

from google.protobuf.json_format import MessageToJson
import grpc

import api_pb2
import api_pb2_grpc


def create_state_response(
        call_state: api_pb2.CallState.State) -> api_pb2.StreamCallResponse:
    response = api_pb2.StreamCallResponse()
    response.call_state.state = call_state
    return response


class Phone(api_pb2_grpc.PhoneServicer):

    def __init__(self):
        self._id_counter = 0
        self._lock = threading.RLock()

    def _create_call_session(self) -> api_pb2.CallInfo:
        call_info = api_pb2.CallInfo()
        with self._lock:
            call_info.session_id = str(self._id_counter)
            self._id_counter += 1
        call_info.media = "https://link.to.audio.resources"
        logging.info("Created a call session [%s]", MessageToJson(call_info))
        return call_info

    def _clean_call_session(self, call_info: api_pb2.CallInfo) -> None:
        logging.info("Call session cleaned [%s]", MessageToJson(call_info))

    def StreamCall(
        self, request_iterator: Iterable[api_pb2.StreamCallRequest],
        context: grpc.ServicerContext
    ) -> Iterable[api_pb2.StreamCallResponse]:
        try:
            request = next(request_iterator)
            logging.info("Received a phone call request for number [%s]",
                         request.phone_number)
        except StopIteration:
            raise RuntimeError("Failed to receive call request")
        # Simulate the acceptance of call request
        time.sleep(1)
        yield create_state_response(api_pb2.CallState.NEW)
        # Simulate the start of the call session
        time.sleep(1)
        call_info = self._create_call_session()
        context.add_callback(lambda: self._clean_call_session(call_info))
        response = api_pb2.StreamCallResponse()
        response.call_info.session_id = call_info.session_id
        response.call_info.media = call_info.media
        yield response
        yield create_state_response(api_pb2.CallState.ACTIVE)
        # Simulate the end of the call
        time.sleep(2)
        yield create_state_response(api_pb2.CallState.ENDED)
        logging.info("Call finished [%s]", request.phone_number)


def serve(address: str) -> None:
    server = grpc.server(ThreadPoolExecutor())
    api_pb2_grpc.add_PhoneServicer_to_server(Phone(), server)
    server.add_insecure_port(address)
    server.start()
    logging.info("Server serving at %s", address)
    server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    serve("[::]:50051")