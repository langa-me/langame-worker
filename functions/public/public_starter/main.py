import os
import logging
from datetime import datetime
from typing import Any
from flask import request, jsonify
import logging
from third_party.common.services import request_starter_for_service
from firebase_admin import firestore, initialize_app
from google.cloud.firestore import Client

initialize_app()

GET_MEMES_URL = os.environ["GET_MEMES_URL"]
def public_starter(_):
    logger = logging.getLogger("public_starter")
    logging.basicConfig(level=logging.INFO)
    api_key = request.headers.get("X-Api-Key", None)
    # Check in Firestore if we have this API Key in our database
    db: Client = firestore.client()
    # TODO: firestore data bundle etc. optimise caching...
    docs = db.collection("api_keys").where("apiKey", "==", api_key).stream()
    for doc in docs:
        json_data = request.get_json()
        logger.info(f"{datetime.now()} - {json_data}")
        topics = json_data.get("topics", ["ice breaker"])
        quantity = json_data.get("limit", 1)
        translated = json_data.get("translated", False)
        conversation_starters, error = request_starter_for_service(
            url=GET_MEMES_URL,
            api_key_id=doc.id,
            logger=logger,
            topics=topics,
            quantity=quantity,
            translated=translated,
        )
        logger.info(
            f"Got conversation starter response: {conversation_starters} error: {error}"
        )
        if error:
            return (
                jsonify(
                    {
                        "error": {
                            "message": error["message"],
                            "status": error["status"],
                        },
                        "results": [],
                    }
                ),
                error["code"],
            )

        def build_response(meme: Any):
            return {
                # merge "content" (original english version) with "translated" (multi-language version)
                "conversation_starter": {
                    "en": meme["content"],
                    **meme.get("translated", {}),
                },
            }

        # TODO: return ID and let argument to say "I want different CS than these IDs" (semantically)
        return (
            jsonify(
                {
                    "topics": topics,
                    "limit": quantity,
                    "translated": translated,
                    "results": [build_response(e) for e in conversation_starters],
                }
            ),
            200,
        )
    logger.warning(f"Invalid API key {api_key}")
    return (
        jsonify(
            {
                "error": {
                    "message": "Invalid API key",
                    "status": "INVALID_ARGUMENT",
                },
                "results": [],
            }
        ),
        401,
    )
