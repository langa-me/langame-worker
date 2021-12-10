import logging
from logging import Logger
from google.cloud import firestore
import os
from datetime import datetime


# def should_drop(logger: Logger, ctx, event_max_age_ms: int = 60_000):
#     event_age_ms = (datetime.now() - datetime.fromtimestamp(ctx["timestamp"])).total_seconds() * 1000
#     if event_age_ms > event_max_age_ms:
#         logger.info(f"Dropping event {ctx['event_id']} with age[ms]: {event_age_ms}")
#         return True
#     return False


def public_starter(_):
    logger = logging.getLogger("public_starter")
    logging.basicConfig(level=logging.INFO)
    firestore_client = firestore.Client()
    return "OK", 200
