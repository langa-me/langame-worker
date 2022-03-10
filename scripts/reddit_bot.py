import fire
import praw
import openai
from transformers import pipeline
from langame.completion import openai_completion
import schedule
import time
import os
import numpy as np
from langame.conversation_starters import get_existing_conversation_starters
import sys

from langame import LangameClient
import logging


def reddit_bot(minutes_frequency=30, nb_subreddits=3, once=False):
    """
    foo
    """

    reddit = praw.Reddit(
        client_id="5HauJ2B0dB6p4yjuVWYORQ",
        client_secret="YCiqgUfT-wM1jXRZ06up0Z8jZ2bf8g",
        password="3Lef6hgDi7&L",
        user_agent="Langame 0.0.2",
        username="Langa-me",
    )
    # classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
    # os.environ["OPENAI_KEY"] = "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"
    # os.environ["OPENAI_ORG"] = "org-KwcHNgfGe4pqdKDLQIJt99UZ"
    c = LangameClient("./config.yaml")
    logger = logging.getLogger("reddit_bot")
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.setLevel(logging.INFO)
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(formatter)
    logger.addHandler(h)
    (
        conversation_starters,
        index,
        sentence_embeddings_model,
    ) = get_existing_conversation_starters(c._firestore_client, logger=logger)
    logger.info("started")



    def job():
        for _ in range(nb_subreddits):
            subreddit = reddit.random_subreddit()

            try:
                for e in subreddit.hot(limit=1):
                    ctx = f"{subreddit.display_name}, {e.title}"
                    query = np.array(
                        [sentence_embeddings_model.encode(ctx, show_progress_bar=False)]
                    )
                    D, I = index.search(query, 1)
                    logger.info(f"ctx: {ctx}")
                    for i, j in enumerate(I[0]):
                        logger.info(f"distance: {D[0][i]}")
                        logger.info(
                            f"conversation_starters: {conversation_starters[j]['content']}",
                        )
                        comment = e.reply(
                            f"{conversation_starters[j]['content']}"
                            + "\n\nStraight from Langame, AI Augmented Conversations @ https://langa.me"
                        )
                        logger.info(
                            f"comment link: https://www.reddit.com{comment.permalink}",
                        )

            except Exception as e:
                logger.warning("fail")
                logger.warning(e)
                break

        # for _ in range(nb_subreddits):
        #     subreddit = reddit.random_subreddit()
        #     candidate_labels = [
        #         "conversations",
        #         "science",
        #         "dating",
        #         "travel",
        #         "health",
        #         "start-ups",
        #         "philosophy",
        #         "artificial intelligence",
        #     ]
        #     threshold = 0.2
        #     product_context = (
        #         "Langame is a platform and service that helps people have more profound conversations"
        #         + " with their friends, family, and new acquaintances."
        #         + " It can schedule conversations started based on your interests and personality"
        #         + " using artificial intelligence generated conversation starters."
        #         + " Also, through the conversations, users get some hints to improve the conversation."
        #         + " You can use Langame on Android, iOS, and Web, but also as a Discord bot."
        #         + " Langame - AI augmented conversations - https://langa.me"
        #     )

        #     for e in subreddit.hot(limit=1):
        #         submission_context = (
        #             f"Subbredit display name: {subreddit.display_name}."
        #             # + f"\nSubbredit description: {subreddit.description}."
        #             + f"\nSubmission title: {e.title}."
        #             # + f"\nSubmission content: {e.selftext}."
        #         )

        #         try:
        #             result = classifier(
        #                 submission_context, candidate_labels, multi_label=False
        #             )
        #             # if any score above threshold, we consider it a positive
        #             # find score index above threshold
        #             score_index = [
        #                 i
        #                 for i, score in enumerate(result["scores"])
        #                 if score > threshold
        #             ]
        #             if score_index:
        #                 print("seems to be a positive")
        #                 labels = [result["labels"][i] for i in score_index]
        #                 print("labels:", labels)
        #                 print("scores:", [result["scores"][i] for i in score_index])
        #                 hack = "Hi guys, what you are concerned about is fascinating, I believe that"
        #                 prompt = (
        #                     f"{product_context}"
        #                     +f"{submission_context}"
        #                     + "\nThis is a message to try to convince the consumers of this subredit submissions "
        #                     + f' to use Langame. "{product_context}".'
        #                     + f"\n{hack}"
        #                 )
        #                 print("prompt:", prompt)
        #                 completion = openai_completion(
        #                     prompt=prompt,
        #                     stop=["def ", "print"],
        #                     model="davinci-codex",
        #                     temperature=0.2,
        #                     max_tokens=300,
        #                     ignore_finish_reason=True,
        #                 )
        #                 print("eventual message:", hack + completion)
        #                 comment = e.reply(hack + completion)
        #                 print("comment link:", "https://www.reddit.com"+comment.permalink)
        #         except Exception as e:
        #             print("fail")
        #             print(e)


    if once:
        logger.info("running once")
        job()
        return

    schedule.every(minutes_frequency).minutes.do(job)
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    fire.Fire(reddit_bot)
