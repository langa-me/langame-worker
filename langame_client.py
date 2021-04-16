import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from google.cloud.firestore_v1.base_client import BaseClient
from hugging_face_client import HuggingFaceClient
from google.cloud.firestore_v1.base_collection import BaseCollectionReference
from typing import List, Tuple, Optional
from google.cloud.firestore_v1.document import DocumentReference
from google.protobuf.timestamp_pb2 import Timestamp
from google.protobuf.json_format import MessageToDict
from langame.protobuf.langame_pb2 import Question, Tag, Topic
from openai_client import OpenAIClient


class LangameClient:
    def __init__(self):
        self._hf_client: HuggingFaceClient = HuggingFaceClient(os.environ['HUGGING_FACE_TOKEN'])
        self._openai_client: OpenAIClient = OpenAIClient(os.environ['OPEN_AI_TOKEN'])

        # Use the application default credentials
        cred = credentials.Certificate(os.environ['GOOGLE_APPLICATION_CREDENTIALS'])
        firebase_admin.initialize_app(cred)
        self._firestore_client: BaseClient = firestore.client()
        self._questions_ref: BaseCollectionReference = self._firestore_client.collection(u'questions')
        self._tags_ref = self._firestore_client.collection(u'tags')
        self._topics_ref = self._firestore_client.collection(u'topics')

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

            for i, l in enumerate(res.get('labels')):
                tag: Tag = Tag()
                tag.content = l
                tag.score = res.get('scores')[i]
                tag.question = q_model.id
                tag.human = False
                self._tags_ref.add(MessageToDict(tag))

    def generate_save_questions(self, topics: List[str], amount_per_topics: int = 1) -> List[Tuple[Question, Tag]]:
        """
        Generate a bunch of questions given topics and save them with deterministic tags
        it is a possibility that it fail to generate a question (model related)
        :param amount_per_topics:
        :param topics:
        :return:
        """
        res: List[Tuple[Question, Tag]] = []
        for t in topics:
            for _ in range(amount_per_topics):
                q: Optional[Question] = self._openai_client.question_generation(t)
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
        return res

    def list_generated_questions(self) -> List[Question]:
        """
        List generated questions
        :return:
        """
        questions: List[Question] = []
        for t in self._tags_ref.where(u'generated', u'==', True).stream():
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
            questions.append(q_model)
        return questions
