from langame import LangameClient
from langame.conversation_starters import generate_conversation_starter
from langame.profanity import ProfanityThreshold
from langame.completion import CompletionType, openai_completion
from langame.messages import (
    FAILING_MESSAGES,
    PROFANITY_MESSAGES,
    UNIMPLEMENTED_TOPICS_MESSAGES,
    RATE_LIMIT_MESSAGES,
    WAITING_MESSAGES,
)
from langame.quality import is_garbage
import fire
import datetime
import logging
from random import sample, randint, seed, shuffle
from time import sleep
from enum import Enum
from typing import List, Any
import pandas as pd


class FuckOpenAIFilter(logging.Filter):
    def filter(self, record):
        return "OpenAI" not in str(record)


def generate(
    out_file: str,
    topics: List[str] = ["ice breaker"],
    randomize: bool = False,
    use_least_used_topics: bool = False,
    top_n_unused_topics: int = 20,
):
    """
    Generate a set of conversation starters for the given topics.
    :param out_file: The file to write the generated conversations to.
    :param topics: The topics to generate conversations for.
    :param randomize: Whether to randomize the order of the topics at each generation.
    :param use_least_used_topics: Whether to use the least used topics.
    :param top_n_unused_topics: The number of topics to use if use_least_used_topics is True.
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

    c = LangameClient()
    existing_memes = []

    for e in c._firestore_client.collection("memes").stream():
        if is_garbage(e.to_dict()):
            topics = e.to_dict().get("topics", None)
            logger.warning(f"Garbage meme found: {e.id} topics: {topics}")
            continue
        existing_memes.append((e.id, e.to_dict()))

    logger.info(f"Fetched {len(existing_memes)} memes.")

    if use_least_used_topics:
        logger.info("Using least used topics")
        # Find the least used topics in the dataset
        df = pd.DataFrame([e[1] for e in existing_memes])
        new_df = (
            pd.Series([item for sublist in df.topics for item in sublist])
            .value_counts()
            .rename_axis("topics")
            .reset_index(name="counts")
        )
        topics = [e[0] for e in new_df.values][-top_n_unused_topics:]
        randomize = True
    logger.info(
        f"Generating conversations for topics: {topics}, randomize: {randomize}, writing to {out_file}"
    )
    conversation_starters = []
    seed(randint(0, 2 ** 31))
    for i in range(10 ** 12):
        # add a bit of random delay to avoid hitting the rate limit
        sleep(randint(0, 10) / 100)
        conversation_starter = ""
        selected_topics = (
            # Generate using all topics or a random subset if randomize is True
            sample(topics, randint(1, len(topics) - 1 if len(topics) < 5 else 4))
            if randomize
            else topics
        )
        logger.info(f"Generating conversation starter for topics: {selected_topics}")
        try:
            conversation_starter = generate_conversation_starter(
                existing_memes,
                topics,
                profanity_threshold=ProfanityThreshold.open,
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


class MessageType(Enum):
    """
    Enum for the different message types.
    """

    FAILING = 0
    PROFANITY = 1
    UNIMPLEMENTED_TOPICS = 2
    RATE_LIMIT = 3
    WAITING = 4


def generate_messages(out_file="data/failing_messages.txt", type: str = "failing"):
    """
    :param out_file: The file to write the messages to.
    """
    message_type = MessageType[type.upper()]
    assert isinstance(message_type, MessageType), "message_type must be a MessageType"
    assert isinstance(out_file, str), "out_file must be a string"
    assert out_file.endswith(".txt"), "out_file must be a .txt file"
    logger = logging.getLogger("batch_generate_messages")
    logger.addFilter(FuckOpenAIFilter())

    logging.basicConfig(level=logging.INFO)
    # Add the date to the out file before the extension with format YYYY_MM_DD
    out_file = out_file.replace(
        ".txt", f"_{datetime.datetime.now().strftime('%Y_%m_%d')}.txt"
    )

    logger.info(f"Generating messages for type: {message_type}, writing to {out_file}")
    LangameClient()
    messages = []
    messages_prompt = []
    if message_type is MessageType.FAILING:
        messages_prompt = FAILING_MESSAGES
    elif message_type is MessageType.PROFANITY:
        messages_prompt = PROFANITY_MESSAGES
    elif message_type is MessageType.UNIMPLEMENTED_TOPICS:
        messages_prompt = UNIMPLEMENTED_TOPICS_MESSAGES
    elif message_type is MessageType.RATE_LIMIT:
        messages_prompt = RATE_LIMIT_MESSAGES
    elif message_type is MessageType.WAITING:
        messages_prompt = WAITING_MESSAGES
    else:
        raise ValueError(f"Invalid message type: {message_type}")
    seed(randint(0, 2 ** 31))
    for i in range(10 ** 12):
        # add a bit of random delay to avoid hitting the rate limit
        sleep(randint(0, 10) / 10)
        message = ""
        logger.info(f"Generating message for type: {message_type}")
        prompt_list = sample(
            messages_prompt,
            randint(round(len(messages_prompt) / 10), len(messages_prompt)),
        )
        shuffle(prompt_list)
        prompt = "\n".join(prompt_list) + "\n"
        try:
            message = openai_completion(prompt)
        except Exception as e:
            logger.error(e)
            continue

        messages.append(message)
        # every 10 samples, append the generated samples to file
        if i % 10 == 0:
            with open(out_file, "a") as f:
                f.write("\n".join(messages) + "\n")
                messages = []
                # print number of total rows in the file
                total_rows = sum(1 for _ in open(out_file))
                logger.info(f"total {total_rows} rows written to {out_file}")


if __name__ == "__main__":
    fire.Fire(
        {
            "generate": generate,
            "generate_messages": generate_messages,
        }
    )
