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

GET_MEMES_URL = os.environ.get("GET_MEMES_URL", None)
logger = logging.getLogger("public_starter")
logging.basicConfig(level=logging.INFO)
db: Client = firestore.client()


def base():
    # Set CORS headers for the preflight request
    if request.method == "OPTIONS":
        # Allows GET requests from any origin with the Content-Type
        # header and caches preflight response for an 3600s
        headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET",
            "Access-Control-Allow-Headers": ["Content-Type", "X-Api-Key"],
            "Access-Control-Max-Age": "3600",
        }

        return (
            False,
            headers,
            None,
            None,
            (
                jsonify(
                    {
                        "error": {
                            "message": "This is a preflight request.",
                            "status": "preflight",
                        },
                        "results": [],
                    }
                ),
                204,
                headers,
            ),
        )

    # Set CORS headers for the main request
    headers = {"Access-Control-Allow-Origin": "*"}

    api_key = request.headers.get("X-Api-Key", None)
    # Check in Firestore if we have this API Key in our database
    # TODO: firestore data bundle etc. optimise caching...
    docs = db.collection("api_keys").where("apiKey", "==", api_key).stream()

    for api_key_doc in docs:
        json_data = request.get_json()
        logger.info(f"{datetime.now()} - {json_data}")
        owner = api_key_doc.to_dict().get("owner", None)
        org_doc = (
            db.collection("organizations").document(owner).get() if owner else None
        )
        if not org_doc:
            break

        return True, headers, api_key_doc, org_doc, json_data

    logger.warning(f"Invalid API key {api_key}")
    return (
        False,
        headers,
        None,
        None,
        (
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
            headers,
        ),
    )


def public_starter(_):
    """
    foo
    """
    result, headers, api_key_doc, org_doc, json_data = base()
    if not result:
        return json_data
    topics = json_data.get("topics", ["ice breaker"])
    quantity = json_data.get("limit", 1)
    translated = json_data.get("translated", False)
    conversation_starters, error = request_starter_for_service(
        url=GET_MEMES_URL,
        api_key_id=api_key_doc.id,
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
            headers,
        )

    def build_response(meme: Any):
        return {
            "id": meme["id"],
            # merge "content" (original english version) with "translated" (multi-language version)
            "conversation_starter": {
                "en": meme["content"],
                **(meme.get("translated", {}) if translated else {}),
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
        headers,
    )


def list_playlists(_):
    """
    foo
    """
    result, headers, api_key_doc, org_doc, json_data = base()
    path_params = request.view_args
    print(f"path_params: {path_params}")
    if not result:
        return json_data
    topics = json_data.get("topics", None)
    if topics is not None and len(topics) > 9:
        return (
            jsonify(
                {
                    "error": {
                        "message": "Too many topics",
                        "status": "INVALID_ARGUMENT",
                    },
                    "results": [],
                }
            ),
            400,
            headers,
        )
    quantity = json_data.get("limit", 5)
    translated = json_data.get("translated", False)
    # get the user playlists
    playlists = []
    query = db.collection("playlists")
    path = path_params.get("path", "").split("/")
    doc_id = path[-1]
    # check it's an ID
    if doc_id and doc_id != "playlists":
        playlist_id = doc_id
        docs = [query.document(doc_id).get()]
    if not playlist_id:
        query = query.where(
            "uid",
            "==",
            org_doc.to_dict()["members"][0],
        ).where("like", "==", True)
    if topics:
        query = query.where("topics", "array_contains_any", topics)
    if quantity:
        query = query.limit(quantity)
    if not playlist_id:
        docs = query.stream()
    for p in docs:
        d = p.to_dict()
        playlists.append(
            {
                "id": p.id,
                "conversation_starter": {
                    "en": d["content"],
                },
                "collection": d["collection"],
                "updated_at": d["updatedAt"],
                **p.to_dict(),
            }
        )

    return (
        jsonify(
            {
                "topics": topics,
                "limit": quantity,
                "translated": translated,
                "results": playlists,
            }
        ),
        200,
        headers,
    )
