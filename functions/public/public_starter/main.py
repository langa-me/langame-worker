import logging
from logging import Logger
from typing import Any
import os
from datetime import datetime
from third_party import get_starter
from flask import request, jsonify

def public_starter(_):
    logger = logging.getLogger("public_starter")
    logging.basicConfig(level=logging.INFO)
    json_data = request.get_json()
    logger.info(f"{datetime.now()} - {json_data}")
    topics = json_data.get("topics") if json_data is not None and "topics" in json_data else ["ice breaker"]
    response, error = get_starter(logger, topics)
    if error:
        logger.error("Error: %s", error)
        return {"error": error}
    else:
        logger.info("Got response: %s", response)
        return {"response": response}

# curl -X POST -H "Content-Type: application/json" -d '{"topics": ["ice breaker"]}' https://dapi.langa.me/starter
