import os
from typing import List, Optional, Tuple
import grpc
from .api.api_pb2 import ConversationStarterRequest
from .api.api_pb2_grpc import ConversationStarterServiceStub
from logging import Logger
from random import choice
from .utils.messages import UNIMPLEMENTED_TOPICS_MESSAGES, FAILING_MESSAGES, PROFANITY_MESSAGES
# For more channel options, please see https://grpc.io/grpc/core/group__grpc__arg__keys.html
CHANNEL_OPTIONS = [
    ("grpc.lb_policy_name", "pick_first"),
    ("grpc.enable_retries", 0),
    ("grpc.keepalive_timeout_ms", 10000),
]

AVA_URL = os.getenv("AVA_URL")

def get_starter(logger: Optional[Logger], topics: List[str]) -> Tuple[Optional[str], Optional[Exception]]:
    if not topics:
        error_message = "No topics provided"
        if logger: logger.error(error_message)
        return None, Exception(error_message)
    with grpc.secure_channel(
        f"{AVA_URL}:443",
        grpc.ssl_channel_credentials(),
    ) as channel:
        stub = ConversationStarterServiceStub(channel)
        cs_request = ConversationStarterRequest()
        cs_request.topics.extend(topics)
        if logger: logger.info("Requesting conversation starter with topics: %s", topics)
        response = None
        error = None
        try:
            response = stub.GetConversationStarter(cs_request)
            if logger: logger.info(f"Response from conversation starter: {response}")
        except Exception as e:
            if logger: logger.warn(f"Error from conversation starter: {e}")
            error = e
        user_facing_message = ""
        if response:
            user_facing_message = response.conversation_starter
        elif "profane" in str(error):
            user_facing_message = choice(PROFANITY_MESSAGES)
            user_facing_message = user_facing_message.replace("[TOPICS]", f"\"{','.join(topics)}\"")
        elif "not-found" in str(error):
            user_facing_message = choice(UNIMPLEMENTED_TOPICS_MESSAGES)
        else:
            user_facing_message = choice(FAILING_MESSAGES)
        return user_facing_message, error