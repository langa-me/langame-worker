import os
from typing import List, Tuple

from flask import Flask
import json
from langame_client import LangameClient

lg_client = LangameClient()

with open('questions.json') as f:
    data = json.load(f)
    questions: List[str] = data.get('questions')

    labels = [
        'philosophy', 'sciences', 'health', 'wealth', 'nutrition',
        'wisdom', 'career', 'biology', 'physics', 'mathematics',
        'artificial intelligence', 'purpose', 'love', 'friends', 'religion',
        'death', 'meditation', 'body', 'mind', 'trading', 'bitcoin'
    ]

    lg_client.classify_questions(questions, labels)

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
