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
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from flask_cors import CORS

sentry_sdk.init(
    dsn="https://89b0a4a5cf3747ff9989710804f50dbb@o404046.ingest.sentry.io/6346831",
    integrations=[
        FlaskIntegration(),
    ],
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=1.0,
    _experiments={
        "profiles_sample_rate": 1.0,
    },
)

BASE = "/v1/conversation/collection"
app = Flask(__name__)  # TODO move base to config
app.url_map.strict_slashes = False
CORS(app)


@app.before_request
def before_request():
    print(f"Request path: {request.path}")


@app.route("/v1/conversation/starter", methods=["POST"])
async def path_create_starter():
    return await create_starter()


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
