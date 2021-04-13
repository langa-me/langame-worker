import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from google.cloud.firestore_v1.base_client import BaseClient
from hugging_face_client import HuggingFaceClient
from google.cloud.firestore_v1.base_collection import BaseCollectionReference
from typing import List, Tuple
from google.cloud.firestore_v1.document import DocumentReference
from google.protobuf.timestamp_pb2 import Timestamp
from google.protobuf.json_format import MessageToDict
from langame.protobuf.langame_pb2 import Question, Tag


class LangameClient:
    def __init__(self):
        self._hf_client: HuggingFaceClient = HuggingFaceClient(os.environ['HUGGING_FACE_TOKEN'])

        # Use the application default credentials
        cred = credentials.Certificate(os.environ['GOOGLE_APPLICATION_CREDENTIALS'])
        firebase_admin.initialize_app(cred)
        self._client: BaseClient = firestore.client()
        self._questions_ref: BaseCollectionReference = self._client.collection(u'questions')
        self._tags_ref = self._client.collection(u'tags')

    def classify_questions(self, questions: List[str], labels: List[str]):
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

