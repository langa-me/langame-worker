import os
import logging
from firebase_admin import firestore
from google.cloud.firestore import Client
import openai

client: Client = firestore.Client()
openai.api_key = os.getenv("OPENAI_KEY")
openai.organization = os.getenv("OPENAI_ORG")

assert openai.api_key is not None, "OPENAI_KEY not set"
assert openai.organization is not None, "OPENAI_ORG not set"


def build_embeddings(data, context):
    """Triggered by a change to a Firestore document.
    Args:
        data (dict): The event payload.
        context (google.cloud.functions.Context): Metadata for the event.
    """
    logger = logging.getLogger("build_embeddings")
    logging.basicConfig(level=logging.INFO)

    path_parts = context.resource.split("/documents/")[1].split("/")
    collection_path = path_parts[0]
    document_path = "/".join(path_parts[1:])

    affected_doc = client.collection(collection_path).document(document_path)
    logger.info(f"Affected document: {affected_doc.id} data {data}")
    if (
        "fields" in data["value"]
        and "content" in data["value"]["fields"]
        and "embedding" not in data["value"]["fields"]
    ):
        content = data["value"]["fields"]["content"]["stringValue"]
        response = openai.Engine(id="ada-similarity").embeddings(input=content)
        embedding = response["data"][0]["embedding"]
        logger.info(f"Done embedding {content}")
        affected_doc.update({"embedding": embedding})
