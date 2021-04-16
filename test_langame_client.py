import unittest

from langame_client import LangameClient


class TestLangameClient(unittest.TestCase):
    def setUp(self):
        self._langame_client = LangameClient()

    def test_save_topics(self):
        self._langame_client.save_topics([
            'philosophy', 'sciences', 'health', 'wealth', 'nutrition',
            'wisdom', 'career', 'biology', 'physics', 'mathematics',
            'artificial intelligence', 'purpose', 'love', 'friends', 'religion',
            'death', 'meditation', 'body', 'mind', 'trading', 'bitcoin'
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

    def test_list_generated_questions(self):
        questions = self._langame_client.list_generated_questions()
        print(questions)


if __name__ == '__main__':
    unittest.main()
