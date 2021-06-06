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
from google.protobuf.json_format import MessageToDict
from langame.protobuf.langame_pb2 import Question, Tag, Topic
from openai_client import OpenAIClient
import time


class LangameClient:
    def __init__(self):
        self._hf_client: HuggingFaceClient = HuggingFaceClient(os.environ["HUGGING_FACE_TOKEN"])
        self._openai_client: OpenAIClient = OpenAIClient(
            os.environ["OPEN_AI_TOKEN"],
            os.environ["GOOGLE_SEARCH_API_TOKEN"],
            os.environ["GOOGLE_SEARCH_CSE_ID"],
        )

        # Use the application default credentials
        cred = credentials.Certificate(os.environ["GOOGLE_APPLICATION_CREDENTIALS"])
        firebase_admin.initialize_app(cred)
        self._firestore_client: BaseClient = firestore.client()
        self._questions_ref: BaseCollectionReference = self._firestore_client.collection(u"questions")
        self._tags_ref = self._firestore_client.collection(u"tags")
        self._topics_ref = self._firestore_client.collection(u"topics")

    def save_topics(self, topics: List[str]):
        """
        Insert topic in db, get the topic -> id mapping
        :param topics:
        :return:
        """

        for t in topics:
            t_model: Topic = Topic()
            t_model.content = t
            topic_and_id = self._topics_ref.add(MessageToDict(t_model))
            t_model.id = topic_and_id[1].id

    def list_topics(self) -> List[Topic]:
        """
        List topics
        :return:
        """
        topics: List[Topic] = []
        for t in self._topics_ref.stream():
            t_model = Topic()
            content = t.to_dict().get("content")
            if not content:
                continue
            t_model.content = content
            t_model.id = t.id
            topics.append(t_model)
        return topics

    def save_questions(self, questions: List[str]) -> None:
        """
        Save a list of strings as questions
        :param questions:
        :return:
        """

        # Insert questions in db, get the question -> id mapping
        for q in questions:
            q_model: Question = Question()
            q_model.content = q
            question_and_id = self._questions_ref.add(MessageToDict(q_model))
            q_model.id = question_and_id[1].id

    def tag_save_questions(self, questions: List[str], labels: List[str]) -> None:
        """
        Tag every given questions and save the result in db
        :param questions:
        :param labels:
        :return:
        """
        # Insert questions in db, get the question -> id mapping
        for q in questions:
            q_model: Question = Question()
            q_model.content = q
            question_and_id = self._questions_ref.add(MessageToDict(q_model))
            q_model.id = question_and_id[1].id

            # For each questions, add it to each topic with its score associated
            res = self._hf_client.online_zero_shot_classification([q], labels)

            for i, l in enumerate(res.get("labels")):
                tag: Tag = Tag()
                tag.content = l
                tag.score = res.get("scores")[i]
                tag.question = q_model.id
                tag.human = False
                self._tags_ref.add(MessageToDict(tag))

    def generate_save_questions(self, topics: List[str],
                                questions_per_topic: int = 1,
                                wikipedia_description: bool = True,
                                anti_rate_limit_delay: float = 0.1,
                                self_contexts: int = 0,
                                synonymous_contexts: int = 0,
                                related_contexts: int = 0,
                                suggested_contexts: int = 0,
                                ) -> List[Tuple[Question, Tag]]:
        """
        Generate a bunch of questions given topics and save them with deterministic tags
        it is a possibility that it fail to generate a question (model related)
        :param wikipedia_description: add a Wikipedia context description?
        :param anti_rate_limit_delay: add a delay between questions generation to prevent rate limit from google
        :param self_contexts: generate context using generated question
        :param synonymous_contexts: generate context using topic synonym
        :param related_contexts: generate context using related topic
        :param suggested_contexts: generate context using suggestions
        :param questions_per_topic: questions per topic
        :param topics:
        :return:
        """
        res: List[Tuple[Question, Tag]] = []
        for t in topics:
            for _ in range(questions_per_topic):
                q: Optional[Question] = self._openai_client.question_generation(t,
                                                                                wikipedia_description,
                                                                                self_contexts,
                                                                                synonymous_contexts,
                                                                                related_contexts,
                                                                                suggested_contexts,
                                                                                )
                if not q:
                    continue
                question_and_id = self._questions_ref.add(MessageToDict(q))
                q.id = question_and_id[1].id
                tag: Tag = Tag()
                tag.content = t
                tag.score = -1
                tag.question = q.id
                tag.human = False
                tag.generated = True
                tag_and_id = self._tags_ref.add(MessageToDict(tag))
                tag.id = tag_and_id[1].id
                res.append((q, tag))
                if wikipedia_description:
                    time.sleep(anti_rate_limit_delay)

        return res

    def list_generated_questions(self) -> List[Question]:
        """
        List generated questions
        :return:
        """
        for t in self._tags_ref.where(u"generated", u"==", True).stream():
            question_id = t.to_dict().get("question")
            if not question_id:
                continue
            q = self._questions_ref.document(question_id).get()
            q_model = Question()
            content = q.to_dict().get("content")
            if not content:
                continue
            q_model.content = content
            q_model.id = q.id
            yield q_model

    def list_questions(self) -> List[Question]:
        """
        List questions
        :return:
        """
        for t in self._questions_ref.stream():
            question = t.to_dict()
            if not question:
                continue
            q = self._questions_ref.document(question_id).get()
            q_model = Question()
            content = q.to_dict().get("content")
            if not content:
                continue
            q_model.content = content
            q_model.id = q.id
            yield q_model

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
        delete_collection(self._questions_ref)
        delete_collection(self._topics_ref)
        delete_collection(self._tags_ref)

    def add_abouts_to_questions(self):
        raise Exception("Not implemented")
        # with self._firestore_client.transaction() as t:
        #     ref = self._questions_ref
        #     snapshot = ref.stream(transaction=t)
        #     t.update(ref, {
        #         u"population": snapshot.get(u"population") + 1
        #     })

