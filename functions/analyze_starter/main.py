import os
import requests
import logging
import asyncio
from firebase_admin import firestore
from google.cloud.firestore import Client

client: Client = firestore.Client()
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
assert HUGGINGFACE_API_KEY is not None, "HUGGINGFACE_API_KEY not set"
API_URL = "https://api-inference.huggingface.co/models/Langame/distilgpt2-starter-classification"
headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}

def query(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()
async def add_ai_topics(conversation_starters: dict, i: int):
    """
    Compute AI topics for each conversation starter.
    """
    # not computing bad starters
    if int(conversation_starters[i]["classification"]) == 0:
        return
    output = query({
        "inputs": conversation_starters[i]["conversation_starter"],
        "parameters": {
            "max_length": 50,
            "num_return_sequences": 1,
            "return_text": False,
            "return_full_text": False,
            "do_sample": True,
            "top_k": 50,
            "top_p": 0.95,
            "end_sequence": "\n",
        },
        "options": {
            "wait_for_model": True,
            "use_cache": True,
        },
    })
    topics = output[0]["generated_text"].strip().split(",")
    topics = list(set(topics))
    topics = [t.replace ("###", "").strip() for t in topics]
    conversation_starters[i]["aiTopics"] = topics

async def execute(conversation_starters):
    await asyncio.gather(
            *[
                add_ai_topics(conversation_starters, i)
                for i, v in enumerate(conversation_starters)
            ]
        )
def analyze_starter(data, context):
    """Triggered by a change to a Firestore document.
    Args:
        data (dict): The event payload.
        context (google.cloud.functions.Context): Metadata for the event.
    """
    logger = logging.getLogger("analyze_starter")
    logging.basicConfig(level=logging.INFO)

    path_parts = context.resource.split("/documents/")[1].split("/")
    collection_path = path_parts[0]
    document_path = "/".join(path_parts[1:])

    affected_doc = client.collection(collection_path).document(document_path)
    logger.info(f"Affected document: {affected_doc.id} data {data}")

    if (
        "fields" in data["value"]
        and "conversationStarters" in data["value"]["fields"]
        # or conversationStarters changed
        or (
            "updateMask" in data
            and "fieldPaths" in data["updateMask"]
            and "conversationStarters" in data["updateMask"]["fieldPaths"]
        )
    ):
        conversation_starters = data["value"]["fields"]["conversationStarters"]["arrayValue"]["values"]
        conversation_starters = [{
            "conversation_starter": e["mapValue"]["fields"]["conversation_starter"]["stringValue"],
            "classification": e["mapValue"]["fields"]["classification"]["stringValue"]
        } for e in conversation_starters]

        asyncio.run(execute(conversation_starters))
        affected_doc.update({"conversationStarters": conversation_starters})
