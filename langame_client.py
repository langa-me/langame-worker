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
                "prompt": e.to_dict()["template"].replace("[TOPIC]", topic_with_emoji[0]),
                "parameters": t.to_dict()["engine"]["parameters"]
            })
        random.shuffle(prompts)
        prompt = prompts.pop()

        meme: Optional[str] = self._openai_client.call_completion(
            prompt["prompt"],
            prompt["parameters"]
        )
        if not meme:
            return

        meme_add = self._memes_ref.add({
            "content": meme,
            "createdAt": firestore.SERVER_TIMESTAMP
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

        # Add a origin tag
        origin_tag: Tag = Tag()
        origin_tag.origin.openai.version = 1
        tag_as_dict = MessageToDict(origin_tag)
        tag_as_dict["createdAt"] = firestore.SERVER_TIMESTAMP
        self._memes_ref.document(meme_add[1].id).collection(
            "tags").add(tag_as_dict)

        return meme_add

    def generate_save_memes_general(self,
                                    topics_with_emojis: Tuple[str, Optional[str]],
                                    memes_per_topic: int = 1,
                                    memes_per_meme: int = 5,
                                    wikipedia_description: bool = True,
                                    openai_description: bool = True,
                                    anti_rate_limit_delay: float = 0.1,
                                    ) -> List[Tuple[Timestamp, DocumentReference]]:
        """
        Generate a bunch of memes given topics and save them with deterministic tags
        it is a possibility that it fail to generate a question (model related)
        :param wikipedia_description: add a Wikipedia context description?
        :param openai_description: add a OpenAI context description?
        :param anti_rate_limit_delay: add a delay between questions generation to prevent rate limit from google
        :param memes_per_meme: memes per meme
        :param memes_per_topic: memes per topic
        :param topics:
        :return:
        """
        res: List[Tuple[Timestamp, DocumentReference]] = []
        for t_e in topics_with_emojis:
            for _ in range(memes_per_topic):
                prompt = f"""This is a list of big talk conversation starters. \
The objective is to propose good conversation starters that create interesting insights between people. \
Today, the conversation topic is {t_e[0]}, this is a list of starters to ask to other persons:
1."""
                meme: Optional[str] = self._openai_client.call_completion(
                    prompt, max_tokens=500, stop=[f"{memes_per_meme+1}."])
                if not meme:
                    continue
                new = []
                for e in [e for e in meme.split("\n")]:
                    cleaned = re.sub("^[0-9]*\.", "", e, 1)
                    new.append(cleaned.strip() if cleaned else e)

                for n in new:
                    meme_add = self._memes_ref.add({
                        "content": n,
                        "createdAt": firestore.SERVER_TIMESTAMP
                    })
                    res.append(meme_add)

                    # Add a topic tag
                    topic_tag: Tag = Tag()
                    topic_tag.topic.content = t_e[0]
                    if t_e[1]:
                        # Split emojis
                        for e in list(t_e[1]):
                            topic_tag.topic.emojis.append(e)
                    tag_as_dict = MessageToDict(topic_tag)
                    tag_as_dict["createdAt"] = firestore.SERVER_TIMESTAMP
                    self._memes_ref.document(meme_add[1].id).collection(
                        "tags").add(tag_as_dict)

                    # Add a origin tag
                    origin_tag: Tag = Tag()
                    origin_tag.origin.openai.version = 1
                    tag_as_dict = MessageToDict(origin_tag)
                    tag_as_dict["createdAt"] = firestore.SERVER_TIMESTAMP
                    self._memes_ref.document(meme_add[1].id).collection(
                        "tags").add(tag_as_dict)

                    if wikipedia_description:
                        w_d = self._openai_client.wikipedia_description(t_e[0])
                        if w_d:
                            # Add a wikipedia tag
                            wikipedia_tag: Tag = Tag()
                            wikipedia_tag.context.content = w_d
                            wikipedia_tag.context.type = Tag.Context.Type.WIKIPEDIA
                            tag_as_dict = MessageToDict(wikipedia_tag)
                            tag_as_dict["createdAt"] = firestore.SERVER_TIMESTAMP
                            self._memes_ref.document(meme_add[1].id).collection(
                                "tags").add(tag_as_dict)

                    if openai_description:
                        o_d = self._openai_client.openai_description(t_e[0])
                        if o_d:
                            # Add an OpenAI tag
                            openai_tag: Tag = Tag()
                            openai_tag.context.content = o_d
                            openai_tag.context.type = Tag.Context.Type.OPENAI
                            tag_as_dict = MessageToDict(openai_tag)
                            tag_as_dict["createdAt"] = firestore.SERVER_TIMESTAMP
                            self._memes_ref.document(meme_add[1].id).collection(
                                "tags").add(tag_as_dict)

                    if wikipedia_description:
                        time.sleep(anti_rate_limit_delay)

        return res

    def generate_save_memes_ice_break(self,
                                      memes: int = 1,
                                      memes_per_meme: int = 3,
                                      deep: bool = True,
                                      ) -> List[Tuple[Timestamp, DocumentReference]]:
        """
        :param memes_per_meme: memes per meme
        :param memes: memes
        :return:
        """
        res: List[Tuple[Timestamp, DocumentReference]] = []

        big_talks_file = open("big-talks.json")
        big_talks = json.load(big_talks_file).get("basic")
        random.shuffle(big_talks)
        for _ in range(memes):
            prompt = f"""This is a list of big talk conversation starters. \
The objective is to propose good conversation starters that break the ice between people.
1.{big_talks.pop()}
2.{big_talks.pop()}
3."""
            if deep:
                prompt = f"""The goal is to provide good conversation starters that break the ice between people and deeply strengthen their relationships.
Here is a list of deep conversation starters, free from small talks.
1.What is your life's purpose?
2.What insight about life have you acquired, that seems obvious to you but might not be obvious to everyone else?
3."""
            meme: Optional[str] = self._openai_client.call_completion(
                prompt, max_tokens=500, stop=[f"{memes_per_meme+2}."])
            if not meme:
                continue
            new = []
            for e in [e for e in meme.split("\n")]:
                cleaned = re.sub("^[0-9]*\.", "", e, 1)
                new.append(cleaned.strip() if cleaned else e)

            for n in new:
                meme_add = self._memes_ref.add({
                    "content": n,
                    "createdAt": firestore.SERVER_TIMESTAMP
                })
                res.append(meme_add)

                # Add a topic tag
                topic_tag: Tag = Tag()
                topic_tag.topic.content = "ice break"
                for e in ["🤔", "😜", "💭"]:
                    topic_tag.topic.emojis.append(e)
                tag_as_dict = MessageToDict(topic_tag)
                tag_as_dict["createdAt"] = firestore.SERVER_TIMESTAMP
                self._memes_ref.document(meme_add[1].id).collection(
                    "tags").add(tag_as_dict)

                # Add a origin tag
                origin_tag: Tag = Tag()
                origin_tag.origin.openai.version = 1
                tag_as_dict = MessageToDict(origin_tag)
                tag_as_dict["createdAt"] = firestore.SERVER_TIMESTAMP
                self._memes_ref.document(meme_add[1].id).collection(
                    "tags").add(tag_as_dict)

        big_talks_file.close()
        return res

    def list_memes(self, topics: List[str] = []) -> List[Meme]:
        """
        List memes
        :return:
        """

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
