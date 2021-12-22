import logging
from datetime import datetime
from flask import request, jsonify
import logging
from third_party.common.services import request_starter
from firebase_admin import firestore
def public_starter(_):
    logger = logging.getLogger("public_starter")
    logging.basicConfig(level=logging.INFO)
    api_key = request.headers.get("X-Api-Key", None)
    if api_key != "fooBarBaz":
        logger.warning(f"Invalid API key {api_key}")
        return jsonify({"error": "Invalid API key"}), 401
    json_data = request.get_json()
    logger.info(f"{datetime.now()} - {json_data}")
    topics = json_data.get("topics") if json_data is not None and "topics" in json_data else ["ice breaker"]
    client = firestore.Client()
    conversation_starter, user_message = request_starter(logger, client, topics)
    logger.info(f"{datetime.now()} - {conversation_starter} - {user_message}")
    if conversation_starter is None:
        return jsonify({"error": user_message}), 400
    return jsonify({"starter": conversation_starter}), 200


# curl -X POST -H "Content-Type: application/json" -H "X-Api-Key: fooBarBaz" -d '{"topics": ["ice breaker"]}' https://dapi.langa.me/starter
