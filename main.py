from typing import List
import json
from langame_client import LangameClient
import argparse
import logging
logging.basicConfig(level=logging.INFO)

parser = argparse.ArgumentParser()
parser.add_argument("--generate", type=bool,
                    help="generate question or classify from hard-coded ones", default=True)
args = parser.parse_args()

lg_client = LangameClient()
topics = [t.content for t in lg_client.list_topics()]
if not topics:
    raise Exception("no_topics_found")


def load_json_questions_and_tag():
    with open("questions.json") as f:
        data = json.load(f)
        questions: List[str] = data.get("questions")
        lg_client.tag_save_questions(questions, topics)


def openai_generate_questions():
    lg_client.generate_save_questions(topics,
                                      questions_per_topic=3,
                                      wikipedia_description=True,
                                      self_contexts=2,
                                      synonymous_contexts=1,
                                      related_contexts=1,
                                      suggested_contexts=1,
                                      )


if args.generate:
    logging.info("openai_generate_questions")
    openai_generate_questions()
else:
    logging.info("load_json_questions_and_tag")
    load_json_questions_and_tag()
