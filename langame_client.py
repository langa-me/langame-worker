import os
import time
import confuse
import json
import random
import re
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from google.cloud.firestore_v1.base_client import BaseClient, BaseTransaction
from hugging_face_client import HuggingFaceClient
from google.cloud.firestore_v1.base_collection import BaseCollectionReference
from typing import List, Tuple, Optional
from google.cloud.firestore_v1.document import DocumentReference
from google.protobuf.timestamp_pb2 import Timestamp
from google.protobuf.json_format import MessageToDict, ParseDict
from langame.protobuf.langame_pb2 import Meme, Tag
from openai_client import OpenAIClient
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


    def prompt_to_meme(self,
                       topic,
                       model="TopicGeneralistFineTuned2",
                       ) -> Tuple[Timestamp, DocumentReference]:
        """
        :param topic:
        :param model:
        :return:
        """
        prompts = []
        for e in self._firestore_client.collection("prompts")\
                .where("type", "==", model)\
                .limit(5)\
                .stream():
            t = None
            # Just a hack to find the tags of parameters
            for tag in e.reference.collection("tags").where("engine.parameters.maxTokens", ">=", 0).stream():
                t = tag
                break
            prompts.append({
                "id": e.id,
                "prompt": e.to_dict()["template"].replace("[TOPIC]", topic),
                "parameters": t.to_dict()["engine"]["parameters"]
            })
        if not prompts:
            print("could not get any prompt")
            return None
        random.shuffle(prompts)
        prompt = prompts.pop()

        print(f"calling openai with {prompt}")
        meme: Optional[str] = self._openai_client.call_completion(
            prompt["prompt"],
            prompt["parameters"],
        )
        if not meme:
            print("could not find any meme")
            return

        # TODO: transaction
        meme_add = self._memes_ref.add({
            "content": meme,
            "createdAt": firestore.SERVER_TIMESTAMP,
            "promptId": prompt["id"],
            "topics": [topic],
        })

        # Add a topic tag
        topic_tag: Tag = Tag()
        topic_tag.topic.content = topic
        tag_as_dict = MessageToDict(topic_tag)
        tag_as_dict["createdAt"] = firestore.SERVER_TIMESTAMP
        self._memes_ref.document(meme_add[1].id).collection(
            "tags").add(tag_as_dict)
        return meme_add

    def prompt_to_meme_ice_breaker(self) -> Tuple[Timestamp, DocumentReference]:
        """
        :return:
        """
        prompts = []
        for e in self._firestore_client.collection("prompts")\
                .where("type", "==", "IceBreakerGeneralist")\
                .limit(5)\
                .stream():
            t = None
            # Just a hack to find the tags of parameters
            for tag in e.reference.collection("tags").where("engine.parameters.maxTokens", ">=", 0).stream():
                t = tag
                break
            prompts.append({
                "id": e.id,
                "prompt": e.to_dict()["template"],
                "parameters": t.to_dict()["engine"]["parameters"]
            })
        if not prompts:
            return None
        random.shuffle(prompts)
        prompt = prompts.pop()

        print(f"calling openai with {prompt}")
        meme: Optional[str] = self._openai_client.call_completion(
            prompt["prompt"],
            prompt["parameters"],
        )
        if not meme:
            return

        # TODO: transaction
        meme_add = self._memes_ref.add({
            "content": meme,
            "createdAt": firestore.SERVER_TIMESTAMP,
            "promptId": prompt["id"]
        })

        # Add a topic tag
        topic_tag: Tag = Tag()
        topic_tag.topic.content = "ice breaker"
        for e in ["🤔","😜","💭"]:
            topic_tag.topic.emojis.append(e)
        tag_as_dict = MessageToDict(topic_tag)
        tag_as_dict["createdAt"] = firestore.SERVER_TIMESTAMP
        self._memes_ref.document(meme_add[1].id).collection(
            "tags").add(tag_as_dict)
        return meme_add

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
