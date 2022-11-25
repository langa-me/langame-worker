import time
import json
import requests
from logging import Logger
from typing import List, Optional, Tuple, Any
from langame.messages import (
    UNIMPLEMENTED_TOPICS_MESSAGES,
    FAILING_MESSAGES,
    PROFANITY_MESSAGES,
)
from random import choice

from sentry_sdk import capture_exception
from .errors import init_errors

init_errors(env="production")


def request_starter_for_service(
    url: str,
    api_key_id: str,
    logger: Optional[Logger],
    topics: List[str],
    quantity: int = 1,
    translated: bool = False,
    fix_grammar: bool = True,
    parallel_completions: int = 3,
    max_tries: int = 3,
    profanity_threshold: str = "tolerant",
) -> Tuple[Optional[Any], Optional[Any]]:
    """
    Request a conversation starter from the API.
    Args:
        logger: Logger object.
        firestore_client: Firestore client.
        topics: List of topics to request a starter for.
        quantity: The number of conversation starters to request.
        translated: Whether to request translated conversation starters.
        fix_grammar: Whether to fix grammar.
        parallel_completions: The number of parallel completion to use.
        max_tries: The maximum number of tries to request a conversation starter.
        profanity_threshold: The profanity threshold.
    Returns:
        Tuple of (starter, user message).
    """
    headers = {
        "Content-Type": "application/json",
    }
    data = {
        "appId": api_key_id,
        "topics": topics,
        "quantity": quantity,
        "translated": translated,
        "fixGrammar": fix_grammar,
        "parallelCompletions": parallel_completions,
        "profanityThreshold": profanity_threshold,
    }
    tries = 0
    error = "something"
    while error and tries < max_tries:
        response = requests.post(
            url,
            headers=headers,
            data=json.dumps({"data": data}),
        )
        response_data = response.json()
        error = response_data.get("error", None)
        tries += 1
        time.sleep(1)
    if error or "result" not in response_data:
        capture_exception(Exception(str(error)))
        if logger:
            logger.error(f"Failed to request starter for {api_key_id}", exc_info=1)
        if error == "no-topics":
            user_message = choice(UNIMPLEMENTED_TOPICS_MESSAGES)
        elif error == "profane":
            user_message = choice(PROFANITY_MESSAGES)
            user_message = user_message.replace("[TOPICS]", f"\"{','.join(topics)}\"")
        else:
            user_message = choice(FAILING_MESSAGES)
        return None, {
            "message": response_data.get("error", {}).get("message", "Unknown error"),
            "code": response.status_code,
            "status": response_data.get("error", {}).get("status", "INTERNAL_ERROR"),
            "user_message": user_message,
        }

    return response_data["result"]["memes"], None
