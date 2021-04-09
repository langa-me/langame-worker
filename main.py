import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from flask import Flask
import json
from hugging_face_client import HuggingFaceClient

# Use the application default credentials
cred = credentials.Certificate(os.environ['GOOGLE_APPLICATION_CREDENTIALS'])

firebase_admin.initialize_app(cred)

db = firestore.client()

with open('questions.json') as f:
    data = json.load(f)
    # # Create a reference to the questions collection
    questions_ref = db.collection(u'questions')
    hf_client = HuggingFaceClient(os.environ['HUGGING_FACE_TOKEN'])
    labels = [
        'philosophy', 'sciences', 'health', 'wealth', 'nutrition',
        'wisdom', 'career', 'biology', 'physics', 'mathematics',
        'artificial intelligence', 'purpose', 'love', 'friends', 'religion',
        'death', 'meditation', 'body', 'mind', 'trading', 'bitcoin'
    ]
    inputs = data.get('questions')
    res = hf_client.batch_zero_shot_classification(inputs, labels)
    # TODO: might filter, or not, see "anti tags"
    # for r in res:
    #     for i, s in enumerate(r.get('scores')):
    #         if s < 0.5:
    #             r.get('scores').remove(i)
    #             r.get('labels').remove(i)
    # print(res)
    for r in res:
        tags = []
        for i, l in enumerate(r.get('labels')):
            tags.append({'tag': l, 'score': r.get('scores')[i]})
        questions_ref.add({
            u'question': r.get('sequence'),
            u'tags': tags,  # TODO: might also add the model used for tagging
        })

#
# app = Flask(__name__)
#
#
# @app.route('/')
# def hello_world():
#     name = os.environ.get('NAME', 'World')
#     return 'Hello {}!'.format(name)
#
#
# if __name__ == '__main__':
#     app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
#
# users_ref = db.collection(u'users')
# docs = users_ref.stream()
#
# for doc in docs:
#     print(f'{doc.id} => {doc.to_dict()}')
