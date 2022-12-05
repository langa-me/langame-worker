import os
import logging
from datetime import datetime
from typing import Optional
from flask import request, jsonify
from langame.functions.services import request_starter_for_service
from firebase_admin import firestore, initialize_app
from google.cloud.firestore import Client

initialize_app()
GET_MEMES_URL = os.environ.get("GET_MEMES_URL")
logger = logging.getLogger()
logging.basicConfig(level=logging.INFO)
db: Client = firestore.client()


def base():
    """TODO"""
    api_key = request.headers.get("X-Api-Key", None)
    # Check in Firestore if we have this API Key in our database
    # TODO: firestore data bundle etc. optimise caching...
    docs = db.collection("api_keys").where("apiKey", "==", api_key).stream()

    for api_key_doc in docs:
        owner = api_key_doc.to_dict().get("owner", None)
        org_doc = (
            db.collection("organizations").document(owner).get() if owner else None
        )
        if not org_doc:
            break

        org_members = org_doc.to_dict().get("members", [])

        # if multiple members, return not implemented yet for Discord servers
        if len(org_members) > 1:
            return (
                None,
                None,
                jsonify(
                    {
                        "error": {
                            "message": "Sorry, API collection management is not"
                            + " yet available for users authenticated through Discord servers",
                            "status": "NOT_IMPLEMENTED",
                        },
                        "results": [],
                    }
                ),
                501,
                {},
            )
        # if no members, return failure
        if len(org_members) == 0:
            return (
                None,
                None,
                jsonify(
                    {
                        "error": {
                            "message": "No organization members found",
                            "status": "NOT_FOUND",
                        },
                        "results": [],
                    }
                ),
                404,
                {},
            )
        member_id = org_members[0]

        return api_key_doc, org_doc, member_id, None

    logger.warning(f"Invalid API key {api_key}")
    return (
        None,
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
            {},
        ),
    )


async def create_starter():
    """
    foo
    """
    (
        api_key_doc,
        org_doc,
        _,
        error,
    ) = base()
    if error or not api_key_doc or not org_doc:
        return error
    json_data = request.get_json()
    topics = json_data.get("topics", [])
    limit = json_data.get("limit", 1)
    translated = json_data.get("translated", False)
    personas = json_data.get("personas", [])
    logging.info(f"Inputs:\n{json_data}")
    if len(personas) > 4:
        return (
            jsonify(
                {
                    "error": {
                        "message": "Too many personas, maximum is 4",
                        "status": "INVALID_ARGUMENT",
                    },
                    "results": [],
                }
            ),
            400,
            {},
        )
    if not personas and len(topics) > 5:
        return (
            jsonify(
                {
                    "error": {
                        "message": "Too many topics, maximum is 5",
                        "status": "INVALID_ARGUMENT",
                    },
                    "results": [],
                }
            ),
            400,
            {},
        )

    # limit max 20
    if limit > 20:
        return (
            jsonify(
                {
                    "error": {
                        "message": "You can only request up to 20 memes at a time",
                        "status": "INVALID_ARGUMENT",
                    },
                    "results": [],
                }
            ),
            400,
            {},
        )
    # https://cloud.google.com/run/docs/tips/general#avoid_background_activities_if_cpu_is_allocated_only_during_request_processing
    conversation_starters, error = await request_starter_for_service(
        api_key_doc=api_key_doc,
        org_doc=org_doc,
        topics=topics,
        limit=limit,
        translated=translated,
        fix_grammar=False,  # increase latency too much?
        profanity_threshold="open",
        personas=personas,
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
            {},
        )

    results = []
    topics = set()
    for conversation_starter in conversation_starters:
        d = conversation_starter.to_dict()
        results.append(
            {
                "id": conversation_starter.id,
                # merge "content" (original english version) with "translated" (multi-language version)
                "conversation_starter": {
                    "en": d.get("content", ""),
                    **(d.get("translated", {}) if translated else {}),
                },
            }
        )
        for topic in d.get("topics", []):
            topics.add(topic)
    # TODO: return ID and let argument to say "I want different CS than these IDs" (semantically)
    return (
        jsonify(
            {
                "topics": list(topics),
                "personas": personas,
                "limit": limit,
                "translated": translated,
                "results": results,
            }
        ),
        200,
        {},
    )


def _get_col(member_id: str, collection_id: str):
    """TODO"""
    pref = db.collection("preferences").document(member_id).get()
    pref_data = pref.to_dict()
    if not pref_data:
        return (
            None,
            None,
            (
                jsonify(
                    {
                        "error": {
                            "message": "No preferences found",
                            "status": "NOT_FOUND",
                        },
                        "results": [],
                    }
                ),
                404,
                {},
            ),
        )
    # https://api.langa.me/v1/conversation/collection/{collectionId}
    col = next(
        iter(
            [
                e
                for e in pref_data.get("collections", [])
                if e.get("id", "") == collection_id
            ]
        ),
        None,
    )
    if not col:
        return (
            None,
            None,
            (
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
                {},
            ),
        )
    # get conversation starters from playlists with this collection id
    # in order to get the list of topics
    conversation_starter_docs = (
        db.collection("playlists").where("collection", "==", collection_id)
    ).get()
    topics = []
    conversation_starters = []
    for c_s in conversation_starter_docs:
        c_s_data = c_s.to_dict()
        if not c_s_data:
            continue
        conversation_starters.append(
            {
                "conversation_starter": {
                    "en": c_s_data.get("content", ""),
                },
                "id": c_s.id,
                "updated_at": c_s_data.get("updatedAt", ""),
                "original_id": c_s_data.get("memeId", ""),
                "topics": c_s_data.get("topics", []),
            }
        )
        for topic in c_s_data.get("topics", []):
            if topic not in topics:
                topics.append(topic)
    col["topics"] = topics
    return col, conversation_starters, None


def list_collections():
    """TODO"""
    (
        _,
        _,
        member_id,
        error,
    ) = base()
    if error:
        return error

    pref = db.collection("preferences").document(member_id).get()
    pref_data = pref.to_dict()
    if not pref_data:
        return (
            jsonify(
                {
                    "error": {
                        "message": "No preferences found",
                        "status": "NOT_FOUND",
                    },
                    "results": [],
                }
            ),
            404,
            {},
        )

    cols = []
    for c in pref_data.get("collections", []):
        col, _, error = _get_col(member_id, c.get("id", ""))
        if error:
            return error
        cols.append(col)
    return (
        jsonify(
            {
                "results": cols,
            }
        ),
        200,
        {},
    )


def get_collection(
    collection_id: str,
):
    """TODO"""
    (
        _,
        _,
        member_id,
        error,
    ) = base()
    if error:
        return error

    col, _, error = _get_col(member_id, collection_id)
    if error:
        return error

    return (
        jsonify(
            {
                "results": [col],
            }
        ),
        200,
        {},
    )


def get_collection_starter(
    collection_id: str,
):
    """TODO"""
    (
        _,
        _,
        member_id,
        error,
    ) = base()
    if error:
        return error

    _, conversation_starters, error = _get_col(member_id, collection_id)
    if error:
        return error

    return (
        jsonify(
            {
                "results": [conversation_starters],
            }
        ),
        200,
        {},
    )


def add_to_collection(
    collection_id: Optional[str],
    starter_id: Optional[str],
):
    """TODO"""
    (
        _,
        _,
        member_id,
        error,
    ) = base()
    if error:
        return error

    col, _, error = _get_col(member_id, collection_id)
    if error:
        return error
    meme = db.collection("memes").document(starter_id).get()
    meme_data = meme.to_dict()
    if not meme_data:
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
            {},
        )
    col = db.collection("playlists")
    # TODO: check not already in the collection?

    updated_at = datetime.now().isoformat()
    _, ref = col.add(
        {
            "collection": collection_id,
            "content": meme_data.get("content", ""),
            "memeId": starter_id,
            "topics": meme_data.get("topics", []),
            "like": True,
            "updatedAt": updated_at,
            "disabled": False,
            "confirmed": True,
            "uid": member_id,
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
                        "updated_at": updated_at,
                        "original_id": meme_data.get("memeId", ""),
                        "topics": meme_data.get("topics", []),
                    }
                ],
            }
        ),
        200,
        {},
    )


def remove_from_collection(
    collection_id: Optional[str],
    starter_id: Optional[str],
):
    """Remove a conversation starter from a collection"""
    (
        _,
        _,
        _,
        error,
    ) = base()
    if error:
        return error
    # get the collection_conversation_starter
    c_c_s = db.collection("playlists").document(starter_id).get()
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
            {},
        )
    # delete the collection_conversation_starter
    c_c_s.reference.delete()
    c_c_s_data = c_c_s.to_dict()

    return (
        jsonify(
            {
                "results": [
                    {
                        "id": starter_id,
                        "updated_at": c_c_s_data.get("updatedAt", ""),
                        "original_id": c_c_s_data.get("memeId", ""),
                        "topics": c_c_s_data.get("topics", []),
                    }
                ],
            }
        ),
        200,
        {},
    )


# def update_collection(
#     _: bool,
#     headers: dict,
#     # pylint: disable=invalid-name
#     __: Optional[DocumentSnapshot],
#     # pylint: disable=invalid-name
#     ___: Optional[DocumentSnapshot],
#     json_data: Optional[dict],
#     collection_id: Optional[str],
#     collection_conversation_starter_id: Optional[str],
# ):
#     """Update a collection"""
#     # get the collection_conversation_starter
#     c_c_s = db.collection("playlists").where("collection", "==", collection_id).get()
#     if not c_c_s:
#         return (
#             jsonify(
#                 {
#                     "error": {
#                         "message": "Conversation starter not found",
#                         "status": "INVALID_ARGUMENT",
#                     },
#                     "results": [],
#                 }
#             ),
#             400,
#             headers,
#         )
#     # update the collection_conversation_starter
#     c_c_s.reference.update(
#         {
#             "content": json_data["conversation_starter"]["en"],
#             "memeId": json_data["original_id"],
#             "topics": json_data["topics"],
#             "updatedAt": datetime.now(),
#         }
#     )
#     return (
#         jsonify(
#             {
#                 "results": {
#                     "id": collection_conversation_starter_id,
#                     "conversation_starter": {
#                         "en": json_data["conversation_starter"]["en"],
#                     },
#                     "collection": collection_conversation_starter_id,
#                     "updated_at": datetime.now(),
#                     "original_id": json_data["original_id"],
#                     "topics": json_data["topics"],
#                 }
#             }
#         ),
#         200,
#         headers,
#     )


# def create_collection(
#     result: bool,
#     headers: dict,
#     api_key_doc: Optional[DocumentSnapshot],
#     org_doc: Optional[DocumentSnapshot],
#     json_data: Optional[dict],
#     collection_id: Optional[str],
#     collection_conversation_starter_id: Optional[str],
# ):
#     """Create a collection"""

#     id = hash(json_data["name"] + datetime.now().isoformat())
#     # create collection in preferences
#     db.collection("preferences").document(org_doc.id).update(
#         {
#             "collections": firestore.ArrayUnion(
#                 [
#                     {
#                         "id": id,
#                         "name": json_data["name"],
#                     },
#                 ],
#             ),
#         }
#     )

#     return (
#         jsonify(
#             {
#                 "results": {
#                     "id": id,
#                     "name": json_data["name"],
#                 }
#             }
#         ),
#         200,
#         headers,
#     )


# def delete_collection(
#     _: bool,
#     headers: dict,
#     # pylint: disable=invalid-name
#     __: Optional[DocumentSnapshot],
#     org_doc: Optional[DocumentSnapshot],
#     # pylint: disable=invalid-name
#     ___: Optional[dict],
#     collection_id: Optional[str],
#     # pylint: disable=invalid-name
#     ____: Optional[str],
# ):
#     """Delete a collection"""

#     # delete collection in preferences
#     preferences_doc = db.collection("preferences").document(org_doc.id).get()
#     if not preferences_doc:
#         return (
#             jsonify(
#                 {
#                     "error": {
#                         "message": "Preferences not found",
#                         "status": "INVALID_ARGUMENT",
#                     },
#                     "results": [],
#                 }
#             ),
#             400,
#             headers,
#         )
#     collections = preferences_doc.to_dict()["collections"]
#     for collection in collections:
#         if collection["id"] == collection_id:
#             collections.remove(collection)
#             break
#     db.collection("preferences").document(org_doc.id).update(
#         {
#             "collections": collections,
#         },
#     )
#     return (
#         jsonify(
#             {
#                 "results": {
#                     "id": collection_id,
#                 }
#             }
#         ),
#         200,
#         headers,
#     )
