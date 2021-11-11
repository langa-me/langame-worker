import os
import confuse
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from google.cloud.firestore_v1.base_client import BaseClient
from langame.hugging_face_client import HuggingFaceClient
from google.cloud.firestore_v1.base_collection import BaseCollectionReference
from langame.openai_client import OpenAIClient
from algoliasearch.search_client import SearchClient


class LangameClient:
    def __init__(self):
        conf = confuse.Configuration('langame-worker', __name__)
        conf.set_file('./config.yaml')

        # AI APIs
        self._hf_client: HuggingFaceClient = HuggingFaceClient(
            conf["hugging_face"]["token"].get())
        self._openai_client: OpenAIClient = OpenAIClient(
            conf["openai"]["token"].get(),
            conf["openai"]["organization"].get(),
            conf["google"]["search_api"]["token"].get(),
            conf["google"]["search_api"]["id"].get(),
        )
        self._algolia_client = SearchClient.create(
            conf["algolia"]["application_id"].get(), 
            conf["algolia"]["admin_api_key"].get()
        )

        # Firestore
        cred = credentials.Certificate(
            f'{os.getcwd()}/{conf["google"]["service_account"]}')
        firebase_admin.initialize_app(cred)
        self._firestore_client: BaseClient = firestore.client()
        self._memes_ref: BaseCollectionReference = self._firestore_client.collection(
            u"memes")

        #self._is_dev = "prod" not in (conf["google"]["service_account"])

    def purge(self, collection, sub_collections = []):
        def delete_collection(coll_ref, batch_size=20):
            docs = coll_ref.limit(batch_size).stream()
            deleted = 0

            for doc in docs:
                for sub in sub_collections:
                    for e in doc.reference.collection(sub).stream():
                        e.reference.delete()
                doc.reference.delete()
                deleted = deleted + 1

            if deleted >= batch_size:
                print(f'Deleted a batch of {deleted} {coll_ref.parent}')
                return delete_collection(coll_ref, batch_size)
        delete_collection(self._firestore_client.collection(collection))

