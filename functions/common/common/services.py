import json
import requests
from logging import Logger
from typing import List, Optional, Tuple, Any
from third_party.common.messages import (
    UNIMPLEMENTED_TOPICS_MESSAGES,
    FAILING_MESSAGES,
    PROFANITY_MESSAGES,
)
from random import choice


def request_starter_for_service(
    url: str,
    api_key_id: str,
    logger: Optional[Logger],
    topics: List[str],
    quantity: int = 1,
    translated: bool = False,
    fix_grammar: bool = False,
    parallel_completions: int = 2,
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
    }
    response = requests.post(url, headers=headers, data=json.dumps({"data": data}))
    response_data = response.json()
    error = response_data.get("error", None)
    if error or "result" not in response_data:
        if logger:
            logger.warning(f"Failed to request starter for {api_key_id}")
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
