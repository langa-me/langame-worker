from langame import LangameClient
from langame.logic import generate_conversation_starter
from langame.profanity import ProfanityThreshold
from langame.completion import CompletionType
import fire
import datetime
import logging
from random import sample, randint, seed
from time import sleep

class FuckOpenAIFilter(logging.Filter):
    def filter(self, record):
        return "OpenAI" not in str(record)


def generate(out_file="data/ice_breaker.txt", topics=["ice breaker"], randomize=False):
    """
    Generate a set of conversation starters for the given topics.
    :param out_file: The file to write the generated conversations to.
    :param topics: The topics to generate conversations for.
    """
    assert isinstance(topics, list), "topics must be a list"
    assert isinstance(out_file, str), "out_file must be a string"
    assert len(topics) > 0, "No topics given."
    assert out_file.endswith(".txt"), "out_file must be a .txt file"
    logger = logging.getLogger("batch_generate")
    logger.addFilter(FuckOpenAIFilter())

    logging.basicConfig(level=logging.INFO)
    # Add the date to the out file before the extension with format YYYY_MM_DD
    out_file = out_file.replace(
        ".txt", f"_{datetime.datetime.now().strftime('%Y_%m_%d')}.txt"
    )

    logger.info(
        f"Generating conversations for topics: {topics}, randomize: {randomize}, writing to {out_file}"
    )

    c = LangameClient()
    existing_memes = []
    for e in c._firestore_client.collection("memes").stream():
        existing_memes.append((e.id, e.to_dict()))

    logger.info(f"Fetched {len(existing_memes)} memes.")

    conversation_starters = []
    seed(randint(0, 2 ** 31))
    for i in range(10 ** 12):
        # add a bit of random delay to avoid hitting the rate limit
        sleep(randint(0, 10) / 100)
        conversation_starter = ""
        selected_topics = (
            sample(topics, randint(1, len(topics)-1)) if randomize else topics
        )
        logger.info(f"Generating conversation starter for topics: {selected_topics}")
        try:
            conversation_starter = generate_conversation_starter(
                existing_memes,
                topics,
                profanity_thresold=ProfanityThreshold.open,
                completion_type=CompletionType.openai_api,
                prompt_rows=60,
            )
        except Exception as e:
            logger.error(e)
            continue

        conversation_starters.append(
            f"{','.join(selected_topics)} ### {conversation_starter}"
        )
        # every 10 samples, append the generated samples to file
        if i % 10 == 0:
            with open(out_file, "a") as f:
                f.write("\n".join(conversation_starters) + "\n")
                conversation_starters = []
                # print number of total rows in the file
                total_rows = sum(1 for _ in open(out_file))
                logger.info(f"total {total_rows} rows written to {out_file}")


if __name__ == "__main__":
    fire.Fire(generate)
