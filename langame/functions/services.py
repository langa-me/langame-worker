from multiprocessing import Pool

import time
from typing import List, Optional, Tuple, Any
from langame.messages import (
    UNIMPLEMENTED_TOPICS_MESSAGES,
    FAILING_MESSAGES,
    PROFANITY_MESSAGES,
)
import pytz
from random import choice
from firebase_admin import firestore, initialize_app
from google.cloud.firestore import DocumentSnapshot, Client
from sentry_sdk import capture_exception
import logging
import datetime

utc = pytz.UTC
poll_interval = 0.1


def _generate(
    i: int,
    api_key_doc_id: str,
    logger: logging.Logger,
    topics: List[str],
    fix_grammar: bool,
    parallel_completions: int,
    personas: Optional[List[str]],
    profanity_threshold: str,
    translated: bool,
) -> Tuple[Optional[dict], Optional[dict], Optional[dict]]:
    try:
        initialize_app()
    # pylint: disable=W0703
    except: pass
    db: Client = firestore.client()
    timeout = 60
    start_time = time.time()
    # format to human readable date time
    logger.info(f"[{i}] Generating starter at {datetime.datetime.now(utc)}")
    _, ref = db.collection("memes").add(
        {
            "state": "to-process",
            "topics": topics,
            "createdAt": firestore.SERVER_TIMESTAMP,
            "disabled": True,
            "tweet": False,
            "shard": 0,  # TODO: math.floor(math.random() * 1),
            "fixGrammar": fix_grammar,
            "parallelCompletions": parallel_completions,
            "personas": personas if personas else [],
            "profanityThreshold": profanity_threshold,
        }
    )

    # poll until it's in state "processed" or "error", timeout after 1 minute
    while True:
        prompt_doc = db.collection("memes").document(ref.id).get()
        data = prompt_doc.to_dict()
        if data.get("state") == "processed" and data.get("content", None):
            if translated and not data.get("translated", None):
                continue
            logger.info(f"[{i}] Generated starter in {time.time() - start_time}s")
            return (
                {
                    "id": ref.id,
                    **data,
                },
                {
                    "id": ref.id,
                    "createdAt": datetime.datetime.now(utc),
                },
                None,
            )
        if data.get("state") == "error":
            logger.error(f"Failed to request starter for {api_key_doc_id}", exc_info=1)
            error = data.get("error", "unknown error")
            if error == "no-topics":
                user_message = choice(UNIMPLEMENTED_TOPICS_MESSAGES)
            elif error == "profane":
                user_message = choice(PROFANITY_MESSAGES)
                user_message = user_message.replace(
                    "[TOPICS]", f"\"{','.join(topics)}\""
                )
            else:
                user_message = choice(FAILING_MESSAGES)
            capture_exception(Exception(str(error)))
            return (
                None,
                None,
                {
                    "message": error,
                    "code": 500,
                    "status": "ERROR",
                    "user_message": "error while generating conversation starter",
                },
            )
        if time.time() - start_time > (
            # increase timeout in case of post processing stuff
            timeout * 2
            if fix_grammar or translated
            else timeout * 1
        ):
            capture_exception(Exception("timeout"))
            return (
                None,
                None,
                {
                    "message": "timeout",
                    "code": 500,
                    "status": "ERROR",
                    "user_message": "error while generating conversation starter",
                },
            )
        time.sleep(poll_interval)


def request_starter_for_service(
    api_key_doc: DocumentSnapshot,
    org_doc: DocumentSnapshot,
    topics: List[str],
    limit: int = 1,
    translated: bool = False,
    fix_grammar: bool = False,
    parallel_completions: int = 3,
    profanity_threshold: str = "tolerant",
    personas: Optional[List[str]] = None,
) -> Tuple[Optional[dict], Optional[Any]]:
    """
    Request a conversation starter from the API.
    Args:
        logger: Logger object.
        firestore_client: Firestore client.
        topics: List of topics to request a starter for.
        limit: The number of conversation starters to request.
        translated: Whether to request translated conversation starters.
        fix_grammar: Whether to fix grammar.
        parallel_completions: The number of parallel completion to use.
        profanity_threshold: The profanity threshold.
        personas: The list of personas.
    Returns:
        Tuple of (starter, user message).
    """
    logger = logging.getLogger(__name__)
    if org_doc.to_dict().get("credits", -1) <= 0:
        message = (
            "you do not have enough credits, "
            + "please buy more on https://langa.me or contact us at contact@langa.me"
        )
        logger.warning(message)
        return None, {
            "message": message,
            "code": 402,
            "status": "INSUFFICIENT_CREDITS",
            "user_message": message,
        }

    db: Client = Client()

    conversation_starters_history_docs = (
        db.collection("history").document(org_doc.id).get()
    )
    conversation_starters_history_list = (
        conversation_starters_history_docs.to_dict().get("conversation_starters", [])
        if conversation_starters_history_docs.exists
        else []
    )

    # generate in parallel for "limit"
    with Pool(processes=limit) as pool:

        responses = pool.starmap(
            _generate,
            [
                (
                    i,
                    api_key_doc.id,
                    logger,
                    topics,
                    fix_grammar,
                    parallel_completions,
                    personas,
                    profanity_threshold,
                    translated,
                )
                for i in range(limit)
            ],
        )
    # turn [(starter, history, error), ...] into starters, history, erros,
    conversation_starters, new_history, errors = zip(*responses)
    print(conversation_starters, new_history, errors)
    # if any are errors, return the first error
    if any(errors):
        return None, [e for e in errors if e][0]
    one_week_ago = datetime.datetime.now(utc) - datetime.timedelta(days=7)

    # Filter out memes already seen X time ago
    conversation_starters_history = (
        list(
            filter(
                lambda x: x.get("createdAt", datetime.datetime.now(utc)) < one_week_ago,
                conversation_starters_history_list,
            )
        )
        + list(new_history)
    )
    org_doc.reference.update(
        {
            "credits": firestore.Increment(-1),
            "lastSpent": firestore.SERVER_TIMESTAMP,
        }
    )
    conversation_starters_history_docs.reference.set(
        {"conversation_starters": conversation_starters_history}, merge=True
    )

    # Return the conversation starters
    return list(conversation_starters), None
