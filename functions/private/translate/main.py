# import asyncio
import logging
from firebase_admin import firestore
from google.cloud.firestore import Client
from deep_translator import GoogleTranslator

client: Client = firestore.Client()

LANGUAGES = ["de", "es", "fr", "it", "ja", "ko", "pt", "ru", "zh-CN"]
# loop = asyncio.new_event_loop()
# asyncio.set_event_loop(loop)


def translate(data, context):
    """Triggered by a change to a Firestore document.
    Args:
        data (dict): The event payload.
        context (google.cloud.functions.Context): Metadata for the event.
    """
    logger = logging.getLogger("translate")
    logging.basicConfig(level=logging.INFO)

    path_parts = context.resource.split("/documents/")[1].split("/")
    collection_path = path_parts[0]
    document_path = "/".join(path_parts[1:])

    affected_doc = client.collection(collection_path).document(document_path)
    logger.info(f"Affected document: {affected_doc.id} data {data}")
    translated = {}

    if (
        "fields" in data["value"]
        and "content" in data["value"]["fields"]
        and "translated" not in data["value"]["fields"]
    ):
        content = data["value"]["fields"]["content"]["stringValue"]
        # async def add_translation(lang):
        #     translated[lang] = GoogleTranslator(source='en', target=lang).translate(content)
        # loop.run_until_complete(asyncio.gather(
        #     *[
        #         add_translation(lang)
        #         for lang in LANGUAGES
        #     ]
        # ))
        for lang in LANGUAGES:
            translated[lang] = GoogleTranslator(source="en", target=lang).translate(
                content
            )
        logger.info(f"Done translation {translated}")
        affected_doc.update({"translated": translated})
