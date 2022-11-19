import os
import logging
from datetime import datetime
from typing import Any, Tuple, Optional
from flask import request, jsonify
import logging

from third_party.common.services import request_starter_for_service
from firebase_admin import firestore, initialize_app
from google.cloud.firestore import Client, DocumentSnapshot
import sentry_sdk
from sentry_sdk.integrations.gcp import GcpIntegration

sentry_sdk.init(
    dsn="https://89b0a4a5cf3747ff9989710804f50dbb@sentry.io/6346831",
    integrations=[GcpIntegration()],
    traces_sample_rate=1.0,  # adjust the sample rate in production as needed
)
initialize_app()

GET_MEMES_URL = os.environ.get("GET_MEMES_URL", None)
logger = logging.getLogger("public_starter")
logging.basicConfig(level=logging.INFO)
db: Client = firestore.client()


def base() -> Tuple[
    bool, dict, Optional[DocumentSnapshot], Optional[DocumentSnapshot], Optional[dict]
]:
    """TODO"""
    # Set CORS headers for the preflight request
    if request.method == "OPTIONS":
        # Allows GET requests from any origin with the Content-Type
        # header and caches preflight response for an 3600s
        headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": ["GET", "POST"],
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
    result, headers, api_key_doc, _, json_data = base()
    if not result:
        return json_data
    topics = json_data.get("topics", ["ice breaker"])
    if len(topics) == 0:
        topics = ["ice breaker"]
    quantity = json_data.get("limit", 1)
    translated = json_data.get("translated", False)
    conversation_starters, error = request_starter_for_service(
        url=GET_MEMES_URL,
        api_key_id=api_key_doc.id,
        logger=logger,
        topics=topics,
        quantity=quantity,
        translated=translated,
        fix_grammar=True,
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


def base_collection_conversation_starter() -> Tuple[
    bool,
    dict,
    Optional[DocumentSnapshot],
    Optional[DocumentSnapshot],
    Optional[dict],
    Optional[str],
    Optional[str],
]:
    """TODO"""
    result, headers, api_key_doc, org_doc, json_data = base()
    path_params = request.view_args
    # get collection ID and collection conversation starter ID from path
    path = path_params.get("path", "").split("/")
    collection_id = None
    collection_conversation_starter_id = None
    # /v1/collection/:collection_id/starter/:collection_conversation_starter_id
    if len(path) == 4:
        collection_id = path[1]
        collection_conversation_starter_id = path[3]
    # /v1/collection/:collection_id
    elif len(path) == 2:
        collection_id = path[1]
    print(f"path_params: {path_params}")
    return (
        result,
        headers,
        api_key_doc,
        org_doc,
        json_data,
        collection_id,
        collection_conversation_starter_id,
    )


def collection_conversation_starter(_):
    """TODO"""
    (
        result,
        headers,
        api_key_doc,
        org_doc,
        json_data,
        collection_id,
        collection_conversation_starter_id,
    ) = base_collection_conversation_starter()

    if not result:
        return json_data

    # /v1/conversation/collections/* GET -> get collection
    # /v1/conversation/collections GET -> get all collections
    # TODO: /v1/conversation/collections/*/starter/* GET -> get collection starter
    if request.method == "GET" and not collection_conversation_starter_id:
        get_collection(
            result,
            headers,
            api_key_doc,
            org_doc,
            json_data,
            collection_id,
            collection_conversation_starter_id,
        )
    # /v1/conversation/collections/*/starter/* POST -> add to collection
    elif (
        request.method == "POST"
        and collection_id
        and collection_conversation_starter_id
    ):
        add_to_collection(
            result,
            headers,
            api_key_doc,
            org_doc,
            json_data,
            collection_id,
            collection_conversation_starter_id,
        )
    # /v1/conversation/collections/*/starter/* DELETE -> remove from collection
    elif (
        request.method == "DELETE"
        and collection_id
        and collection_conversation_starter_id
    ):
        remove_from_collection(
            result,
            headers,
            api_key_doc,
            org_doc,
            json_data,
            collection_id,
            collection_conversation_starter_id,
        )
    # /v1/conversation/collections/*/* PUT -> full update collection conversation starter
    # /v1/conversation/collections/*/* PATCH -> partial update collection conversation starter
    # elif (
    # request.method == "PUT" or request.method == "PATCH"
    # ) and collection_conversation_starter_id:
    # update_collection(
    #     result,
    #     headers,
    #     api_key_doc,
    #     org_doc,
    #     json_data,
    #     collection_id,
    #     collection_conversation_starter_id,
    # )
    # pass
    # /v1/conversation/collections POST -> create collection
    # elif request.method == "POST" and not collection_conversation_starter_id:
    # create_collection(
    #     result,
    #     headers,
    #     api_key_doc,
    #     org_doc,
    #     json_data,
    #     collection_id,
    #     collection_conversation_starter_id,
    # )
    # pass
    # /v1/conversation/collections/* DELETE -> delete collection
    # elif request.method == "DELETE" and not collection_conversation_starter_id:
    # delete_collection(
    #     result,
    #     headers,
    #     api_key_doc,
    #     org_doc,
    #     json_data,
    #     collection_id,
    #     collection_conversation_starter_id,
    # )
    # pass
    else:
        return (
            jsonify(
                {
                    "error": {
                        "message": "Invalid request method",
                        "status": "INVALID_ARGUMENT",
                    },
                    "results": [],
                }
            ),
            400,
            headers,
        )


def get_collection_name(org_id: str, collection_id: str) -> str:
    """TODO"""
    pref = db.collection("preferences").document(org_id).get()
    pref_data = pref.to_dict()
    collection_name = next(
        [
            e.get("name", None)
            for e in pref_data.get("collections", [])
            if e.get("id", "") == collection_id
        ],
        None,
    )
    return collection_name


def get_collection(
    _: bool,
    headers: dict,
    # ignore pylint invalid name arg
    # pylint: disable=invalid-name
    __: Optional[DocumentSnapshot],
    org_doc: Optional[DocumentSnapshot],
    # pylint: disable=invalid-name
    ___: Optional[dict],
    collection_id: Optional[str],
    # pylint: disable=invalid-name
    ____: Optional[str],
):
    """TODO"""
    pref = db.collection("preferences").document(org_doc.id).get()
    pref_data = pref.to_dict()
    # https://api.langa.me/v1/conversation/collection/{collectionId}
    if collection_id:
        col = next(
            [
                e
                for e in pref_data.get("collections", [])
                if e.get("id", "") == collection_id
            ],
            None,
        )
        if not col:
            return (
                jsonify(
                    {
                        "error": {
                            "message": "No collections found",
                            "status": "NOT_FOUND",
                        },
                        "results": [],
                    }
                ),
                404,
                headers,
            )
        return (
            jsonify(
                {
                    "error": None,
                    "results": [col],
                }
            ),
            200,
            headers,
        )
    # https://api.langa.me/v1/conversation/collections
    else:
        return (
            jsonify(
                {
                    "error": None,
                    "results": pref_data.get("collections", []),
                }
            ),
            200,
            headers,
        )


def add_to_collection(
    _: bool,
    headers: dict,
    # pylint: disable=invalid-name
    __: Optional[DocumentSnapshot],
    org_doc: Optional[DocumentSnapshot],
    json_data: Optional[dict],
    collection_id: Optional[str],
    collection_conversation_starter_id: Optional[str],
):
    """TODO"""
    pref = db.collection("preferences").document(org_doc.id).get()
    pref_data = pref.to_dict()
    col = next(
        [
            e
            for e in pref_data.get("collections", [])
            if e.get("id", "") == collection_id
        ],
        None,
    )
    if not col:
        return (
            jsonify(
                {
                    "error": {
                        "message": "Collection not found",
                        "status": "NOT_FOUND",
                    },
                    "results": [],
                }
            ),
            404,
            headers,
        )
    meme = db.collection("memes").document(collection_conversation_starter_id).get()
    meme_data = meme.to_dict()
    if not meme.exists or not meme_data:
        return (
            jsonify(
                {
                    "error": {
                        "message": "Conversation starter not found",
                        "status": "NOT_FOUND",
                    },
                    "results": [],
                }
            ),
            404,
            headers,
        )
    col = db.collection("playlists")
    # TODO: check not already in the collection?

    _, ref = col.add(
        {
            "collection": collection_id,
            "content": meme_data.get("content", ""),
            "memeId": collection_conversation_starter_id,
            "topics": meme_data.get("topics", []),
            "like": True,
            "updatedAt": datetime.now(),
            "disabled": False,
            "confirmed": True,
            "uid": org_doc.id,
        }
    )
    return (
        jsonify(
            {
                "topics": meme_data.get("topics", []),
                "results": [
                    {
                        "id": ref.id,
                        "conversation_starter": {
                            "en": meme_data.get("content", ""),
                        },
                        "updated_at": datetime.now(),
                        "original_id": json_data["original_id"],
                        "topics": json_data["topics"],
                    }
                ],
            }
        ),
        200,
        headers,
    )


def remove_from_collection(
    _: bool,
    headers: dict,
    # pylint: disable=invalid-name
    __: Optional[DocumentSnapshot],
    # pylint: disable=invalid-name
    ___: Optional[DocumentSnapshot],
    # pylint: disable=invalid-name
    ____: Optional[dict],
    collection_id: Optional[str],
    collection_conversation_starter_id: Optional[str],
):
    """Remove a conversation starter from a collection"""
    # get the collection_conversation_starter
    c_c_s = (
        db.collection("playlists")
        .where("collection", "==", collection_id)
        .where("id", "==", collection_conversation_starter_id)
    )
    if not c_c_s:
        return (
            jsonify(
                {
                    "error": {
                        "message": "Conversation starter not found",
                        "status": "INVALID_ARGUMENT",
                    },
                    "results": [],
                }
            ),
            400,
            headers,
        )
    # delete the collection_conversation_starter
    c_c_s.reference.delete()
    return (
        jsonify(
            {
                "results": [
                    {
                        "id": collection_conversation_starter_id,
                        "updated_at": c_c_s.to_dict().get("updatedAt", ""),
                        "original_id": c_c_s.to_dict().get("memeId", ""),
                        "topics": c_c_s.to_dict().get("topics", []),
                    },
                ],
            }
        ),
        200,
        headers,
    )


def update_collection(
    _: bool,
    headers: dict,
    # pylint: disable=invalid-name
    __: Optional[DocumentSnapshot],
    # pylint: disable=invalid-name
    ___: Optional[DocumentSnapshot],
    json_data: Optional[dict],
    collection_id: Optional[str],
    collection_conversation_starter_id: Optional[str],
):
    """Update a collection"""
    # get the collection_conversation_starter
    c_c_s = db.collection("playlists").where("collection", "==", collection_id).get()
    if not c_c_s:
        return (
            jsonify(
                {
                    "error": {
                        "message": "Conversation starter not found",
                        "status": "INVALID_ARGUMENT",
                    },
                    "results": [],
                }
            ),
            400,
            headers,
        )
    # update the collection_conversation_starter
    c_c_s.reference.update(
        {
            "content": json_data["conversation_starter"]["en"],
            "memeId": json_data["original_id"],
            "topics": json_data["topics"],
            "updatedAt": datetime.now(),
        }
    )
    return (
        jsonify(
            {
                "results": {
                    "id": collection_conversation_starter_id,
                    "conversation_starter": {
                        "en": json_data["conversation_starter"]["en"],
                    },
                    "collection": collection_conversation_starter_id,
                    "updated_at": datetime.now(),
                    "original_id": json_data["original_id"],
                    "topics": json_data["topics"],
                }
            }
        ),
        200,
        headers,
    )


def create_collection(
    result: bool,
    headers: dict,
    api_key_doc: Optional[DocumentSnapshot],
    org_doc: Optional[DocumentSnapshot],
    json_data: Optional[dict],
    collection_id: Optional[str],
    collection_conversation_starter_id: Optional[str],
):
    """Create a collection"""

    id = hash(json_data["name"] + datetime.now().isoformat())
    # create collection in preferences
    db.collection("preferences").document(org_doc.id).update(
        {
            "collections": firestore.ArrayUnion(
                [
                    {
                        "id": id,
                        "name": json_data["name"],
                    },
                ],
            ),
        }
    )

    return (
        jsonify(
            {
                "results": {
                    "id": id,
                    "name": json_data["name"],
                }
            }
        ),
        200,
        headers,
    )


def delete_collection(
    _: bool,
    headers: dict,
    # pylint: disable=invalid-name
    __: Optional[DocumentSnapshot],
    org_doc: Optional[DocumentSnapshot],
    # pylint: disable=invalid-name
    ___: Optional[dict],
    collection_id: Optional[str],
    # pylint: disable=invalid-name
    ____: Optional[str],
):
    """Delete a collection"""

    # delete collection in preferences
    preferences_doc = db.collection("preferences").document(org_doc.id).get()
    if not preferences_doc:
        return (
            jsonify(
                {
                    "error": {
                        "message": "Preferences not found",
                        "status": "INVALID_ARGUMENT",
                    },
                    "results": [],
                }
            ),
            400,
            headers,
        )
    collections = preferences_doc.to_dict()["collections"]
    for collection in collections:
        if collection["id"] == collection_id:
            collections.remove(collection)
            break
    db.collection("preferences").document(org_doc.id).update(
        {
            "collections": collections,
        },
    )
    return (
        jsonify(
            {
                "results": {
                    "id": collection_id,
                }
            }
        ),
        200,
        headers,
    )
