"""
python3 scripts/self_chat.py generate_seeds
see ../ParlAI for self chat
"""

import os
import logging
import sys
import fire
import pandas as pd
from itertools import chain
from langame import LangameClient
from tqdm import tqdm
from langame.conversation_starters import get_existing_conversation_starters
import datetime
def generate_seeds():
    """
    a
    """
    c = LangameClient("./config.yaml")
    logger = logging.getLogger("generate_seeds")
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.setLevel(logging.INFO)
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(formatter)
    logger.addHandler(h)
    (
        conversation_starters,
        _,
        __,
    ) = get_existing_conversation_starters(c._firestore_client, logger=logger)
    logger.info("started")
    # write a file in data/all_prod_{YYYY_MM_DD}.txt
    # with conversation starters
    date_today = datetime.datetime.now().strftime("%Y_%m_%d")
    # delete existing file
    fp = f"./data/all_prod_{date_today}.txt"
    if os.path.exists(fp):
        os.remove(fp)
    for i in tqdm(range(len(conversation_starters))):
        conversation_starter = conversation_starters[i].get("content", None)
        if not conversation_starter: continue
        with open(fp, "a") as f:
            f.write(conversation_starter + "\n")


def to_firestore(
    conversations_file_path="./data/out.jsonl",
    conversations_metadata_file_path="./data/out.metadata",
):
    """
    foo
    """
    logger = logging.getLogger("self_chat")
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger.setLevel(logging.INFO)
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(formatter)
    logger.addHandler(h)
    c = LangameClient(path_to_config_file="./config.yaml")
    md = pd.read_json(conversations_metadata_file_path, lines=True).iloc[0]
    conversations = (
        pd.read_json(conversations_file_path, lines=True)["dialog"]
        .apply(lambda x: list(chain.from_iterable(x)))
        .apply(
            lambda x: [
                {"text": e["text"], "author": e["id"], "feedback": {
                    "text": "",
                    "recipient": "",
                }} for e in x
            ]
        )
    )

    # ask confirmation to the user with some information
    logger.info(f"{len(conversations)} conversations")
    logger.info(f"created at {md['date']}")
    logger.info(f"model: {md['opt']['model_file']}")
    logger.info(f"task: {md['opt']['task']}")

    confirmation = input(
        "Are you sure you want to upload this data to Firestore? (y/n)"
    )
    if confirmation != "y":
        logger.info("aborting")
        return
    for conversation in tqdm(conversations):
        c._firestore_client.collection("conversations").add(
            {
                "created_at": md["date"],
                "model": md["opt"]["model_file"],
                "task": md["opt"]["task"],
                "conversation": conversation,
            }
        )
    logger.info("done")
    # ask user if want to delete the files
    confirmation = input("Delete the files? (y/n)")
    if confirmation == "y":
        os.remove(conversations_file_path)
        os.remove(conversations_metadata_file_path)
        logger.info(f"deleted {conversations_file_path}")
        logger.info(f"deleted {conversations_metadata_file_path}")


if __name__ == "__main__":
    fire.Fire({
        "generate_seeds": generate_seeds,
        "to_firestore": to_firestore,
    })
