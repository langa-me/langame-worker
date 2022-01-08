import logging
from datetime import datetime
from flask import request, jsonify
import logging
from third_party.common.services import request_starter
from firebase_admin import firestore, initialize_app
from google.cloud.firestore import Client

initialize_app()

def public_starter(_):
    logger = logging.getLogger("public_starter")
    logging.basicConfig(level=logging.INFO)
    api_key = request.headers.get("X-Api-Key", None)
    # Check in Firestore if we have this API Key in our database
    db: Client = firestore.client()
    # TODO: firestore data bundle etc. optimise caching...
    doc = db.collection("api_keys").where("api_key", "==", api_key).stream()
    for _ in doc:   
        json_data = request.get_json()
        logger.info(f"{datetime.now()} - {json_data}")
        topics = (
            json_data.get("topics")
            if json_data is not None and "topics" in json_data
            else ["ice breaker"]
        )
        client = firestore.Client()
        conversation_starter, user_message = request_starter(logger, client, topics)
        logger.info(f"{datetime.now()} - {conversation_starter} - {user_message}")
        if conversation_starter is None:
            return jsonify({"error": user_message}), 400
        return jsonify({"topics": topics, "starter": conversation_starter}), 200
    logger.warning(f"Invalid API key {api_key}")
    return jsonify({"error": "Invalid API key"}), 401