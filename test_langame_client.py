import unittest
import os
from langame_client import LangameClient


class TestLangameClient(unittest.TestCase):
    def setUp(self):
        # os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./langame-dev-8ac76897c7bc.json"
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./langame-86ac4-firebase-adminsdk-iojlf-2d6861b97d.json"
        self._langame_client = LangameClient()

    def test_save_topics(self):
        self._langame_client.save_topics([
            "philosophy", "sciences", "health", "wealth", "nutrition",
            "wisdom", "career", "biology", "physics", "mathematics",
            "artificial intelligence", "purpose", "love", "friends", "religion",
            "death", "mind", "politics", "law"
        ])
        topics = self._langame_client.list_topics()
        self.assertGreater(len(topics), 0, "Should not be empty")

    def test_list_topics(self):
        res = self._langame_client.list_topics()
        for r in res:
            print(r)

    def test_generate_save_questions(self):
        qs_ts = self._langame_client.generate_save_questions(["philosophy"])
        print(qs_ts)

    def test_generate_save_questions_with_context(self):
        qs_ts = self._langame_client.generate_save_questions(
            ["philosophy"],
            wikipedia_description=True,
            questions_per_topic=1,
            self_contexts=1,
            synonymous_contexts=1,
            related_contexts=1,
            suggested_contexts=1,
        )
        print(qs_ts)

    def test_list_generated_questions(self):
        [print(q) for q in self._langame_client.list_generated_questions()]

    def test_purge(self):
        self._langame_client.purge()
        length = sum(1 for _ in self._langame_client.list_generated_questions())
        self.assertEqual(length, 0)


if __name__ == "__main__":
    unittest.main()
