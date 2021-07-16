import os
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
import time
import confuse
import json
import random
import re


class LangameClient:
    def __init__(self):
        conf = confuse.Configuration('langame-worker', __name__)
        conf.set_file('./config.yaml')

        self._hf_client: HuggingFaceClient = HuggingFaceClient(
            conf["hugging_face"]["token"].get())
        self._openai_client: OpenAIClient = OpenAIClient(
            conf["openai"]["token"].get(),
            conf["google"]["search_api"]["token"].get(),
            conf["google"]["search_api"]["id"].get(),
        )

        # Use the application default credentials
        cred = credentials.Certificate(
            f'{os.getcwd()}/{conf["google"]["service_account"]}')
        firebase_admin.initialize_app(cred)
        self._firestore_client: BaseClient = firestore.client()
        self._memes_ref: BaseCollectionReference = self._firestore_client.collection(
            u"memes")

    def save(self, memes: List[Meme]) -> List[Tuple[Timestamp, DocumentReference]]:
        """
        Save a list of memes to firestore
        :param memes:
        :return:
        """

        ret: List[Tuple[Timestamp, DocumentReference]] = []
        for q in memes:
            prot = MessageToDict(q)
            prot.created_at = firestore.SERVER_TIMESTAMP
            ret.append(self._memes_ref.add(prot))
        return ret

    def prompt_to_meme(self,
                       topic_with_emoji: Tuple[str, Optional[str]],
                       ) -> Tuple[Timestamp, DocumentReference]:
        """
        :param topics_with_emojis:
        :return:
        """
        prompts = []
        for e in self._firestore_client.collection("prompts")\
                .where("type", "==", "TopicGeneralist")\
                .limit(5)\
                .stream():
            t = None
            # Just a hack to find the tags of parameters
            for tag in e.reference.collection("tags").where("engine.parameters.maxTokens", ">=", 0).stream():
                t = tag
                break
            prompts.append({
                "id": e.id,
                "prompt": e.to_dict()["template"].replace("[TOPIC]", topic_with_emoji[0]),
                "parameters": t.to_dict()["engine"]["parameters"]
            })
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
        topic_tag.topic.content = topic_with_emoji[0]
        if topic_with_emoji[1]:
            # Split emojis
            for e in list(topic_with_emoji[1]):
                topic_tag.topic.emojis.append(e)
        tag_as_dict = MessageToDict(topic_tag)
        tag_as_dict["createdAt"] = firestore.SERVER_TIMESTAMP
        self._memes_ref.document(meme_add[1].id).collection(
            "tags").add(tag_as_dict)
        return meme_add

    def list_memes(self, topics: List[str] = []) -> List[Meme]:
        """
        List memes
        :return:
        """
        # TODO broken
        if topics:
            tags = self._firestore_client.collection_group(
                u"tags").where(u"topic.content", u"in", topics).stream()
            for t in tags:
                yield ParseDict(t.reference.parent.parent.get().to_dict(), Meme())
        else:
            for q in self._memes_ref.stream():
                yield ParseDict(q.to_dict(), Meme())

    def purge(self):
        def delete_collection(coll_ref, batch_size=20):
            docs = coll_ref.limit(batch_size).stream()
            deleted = 0

            for doc in docs:
                doc.reference.delete()
                deleted = deleted + 1

            if deleted >= batch_size:
                print(f'Deleted a batch of {deleted} {coll_ref.parent}')
                return delete_collection(coll_ref, batch_size)
        delete_collection(self._memes_ref)
