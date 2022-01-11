import asyncio
import logging
from firebase_admin import firestore
from google.cloud.firestore import Client
from deep_translator import GoogleTranslator

client: Client = firestore.Client()

LANGUAGES = ["de", "es", "fr", "it", "ja", "ko", "pt", "ru", "zh-CN"]

async def add_translation(translated, content, lang):
    translated[lang] = GoogleTranslator(source='en', target=lang).translate(content)

async def execute(translated, content):
    await asyncio.gather(
            *[
                add_translation(translated, content, lang)
                for lang in LANGUAGES
            ]
        )
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
        # or content changed
        or (
            "updateMask" in data
            and "fieldPaths" in data["updateMask"]
            and "content" in data["updateMask"]["fieldPaths"]
        )
    ):
        content = data["value"]["fields"]["content"]["stringValue"]
        asyncio.run(execute(translated, content))
        logger.info(f"Done translation {translated}")
        affected_doc.update({"translated": translated})
