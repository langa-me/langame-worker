import os

from flask import Flask, request
from logic import (
    list_collections,
    get_collection,
    get_collection_starter,
    add_to_collection,
    remove_from_collection,
    create_starter,
)

BASE = "/v1/conversation/collection"

app = Flask(__name__)  # TODO move base to config
app.url_map.strict_slashes = False


@app.before_request
def before_request():
    print(f"Request path: {request.path}")


@app.route("/v1/conversation/beta/starter", methods=["POST"])
def path_create_starter():
    return create_starter()


@app.route(BASE, methods=["GET"])
def path_list_collections():
    return list_collections()


@app.route(f"{BASE}/<collection_id>", methods=["GET"])
def path_get_collection(collection_id: str):
    return get_collection(collection_id)


@app.route(f"{BASE}/<collection_id>/starter", methods=["GET"])
def path_get_collection_starter(collection_id: str):
    return get_collection_starter(collection_id)


@app.route(f"{BASE}/<collection_id>/starter/<starter_id>", methods=["POST"])
def path_add_to_collection(collection_id: str, starter_id: str):
    return add_to_collection(collection_id, starter_id)


@app.route(f"{BASE}/<collection_id>/starter/<starter_id>", methods=["DELETE"])
def path_remove_from_collection(collection_id: str, starter_id: str):
    return remove_from_collection(collection_id, starter_id)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
