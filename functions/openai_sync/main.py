import logging
from logging import Logger
import openai
from google.cloud import firestore
import os
from datetime import datetime


# def should_drop(logger: Logger, ctx, event_max_age_ms: int = 60_000):
#     event_age_ms = (datetime.now() - datetime.fromtimestamp(ctx["timestamp"])).total_seconds() * 1000
#     if event_age_ms > event_max_age_ms:
#         logger.info(f"Dropping event {ctx['event_id']} with age[ms]: {event_age_ms}")
#         return True
#     return False


def openai_sync(_, ctx):
    """
    Periodically synchronize openai models with firestore.
    Args:
         event (dict):  The dictionary with data specific to this type of
                        event. The `@type` field maps to
                         `type.googleapis.com/google.pubsub.v1.PubsubMessage`.
                        The `data` field maps to the PubsubMessage data
                        in a base64-encoded string. The `attributes` field maps
                        to the PubsubMessage attributes if any is present.
         context (google.cloud.functions.Context): Metadata of triggering event
                        including `event_id` which maps to the PubsubMessage
                        messageId, `timestamp` which maps to the PubsubMessage
                        publishTime, `event_type` which maps to
                        `google.pubsub.topic.publish`, and `resource` which is
                        a dictionary that describes the service API endpoint
                        pubsub.googleapis.com, the triggering topic's name, and
                        the triggering event type
                        `type.googleapis.com/google.pubsub.v1.PubsubMessage`.
    Returns:
        None. The output is written to Cloud Logging.
    """
    logger = logging.getLogger("openai_sync")
    logging.basicConfig(level=logging.INFO)
    openai.api_key = os.environ["OPENAI_KEY"]
    openai.organization = os.environ["OPENAI_ORG"]
    assert openai.api_key is not None, "OPENAI_KEY not set"
    assert openai.organization is not None, "OPENAI_ORG not set"
    # if should_drop(logger, ctx, 60_000):
    #     return "Dropped", 200
    fine_tunes = openai.FineTune.list()["data"]
    firestore_client = firestore.Client()
    for fine_tune in fine_tunes:
        logger.info(f"Syncing {fine_tune['id']}")
        fine_tune_id = fine_tune["id"]
        fine_tune_doc = firestore_client.collection("fine_tunes").document(fine_tune_id)
        fine_tune_doc.set(fine_tune, merge=True)
    return "OK", 200
