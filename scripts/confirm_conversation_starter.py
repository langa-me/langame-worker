from langame.langame_client import LangameClient
import fire
from random import randint
import logging
from firebase_admin.firestore import SERVER_TIMESTAMP
from time import sleep
def confirm(in_file: str = None):
    """
    Given a file with rows of format [topics,] ### [sentence]
    Ask the user to confirm if the conversation starter is good enough
    or let him edit it (topics and sentence)
    then insert it in firestore.
    """

    assert isinstance(in_file, str), "out_file must be a string"
    logger = logging.getLogger("confirm_conversation_starter")
    logging.basicConfig(level=logging.INFO)
    logger.warning(
        "Assuming the input dataset rows are of format [topics,] ### [sentence]"
    )

    logger.info(f"Confirming conversation starters from {in_file}")
    logger.info(f"""If you are unsure whether these conversation starters 
are already present in database, make sure to deduplicate your file first 
using scripts/deduplicate_dataset.py""")

    c = LangameClient()
    memes_collection_ref = c._firestore_client.collection("memes")
    dataset = []
    # Load the dataset
    with open(in_file, "r") as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip()
            # Check that the format is correct
            # i.e. [topics,] ### [sentence]
            splitted = line.split("###")
            if line and len(splitted) == 2:
                topics, sentence = splitted
                topics = topics.split(",")
                dataset.append(([e.strip() for e in topics], sentence.strip()))

    confirmed_dataset = []

    logger.info(f"There is {len(dataset)} conversation starters to confirm")

    # Ask the user to confirm each conversation starter
    for i, v in enumerate(dataset):
        topics, sentence = v
        logger.info(f"Confirming conversation starter n°{i}/{len(dataset)}:")
        print(f"Sentence: {sentence}")
        print(f"Topics: {','.join(topics)}")
        # Now offer to either, confirm, edit or delete the conversation starter
        print("Is this conversation starter good enough? (y/e/d/s) (confirm/edit/delete/stop)")
        answer = input()
        if answer == "y":
            logger.info(f"Confirming conversation starter: {sentence}")
            confirmed_dataset.append((topics, sentence))
        elif answer == "e":
            logger.info(f"Editing conversation starter: {sentence}")
            print("Please enter the new conversation starter:")
            new_sentence = input()
            print("Please enter the new topics (foo,bar,baz):")
            new_topics = input()
            confirmed_dataset.append((new_topics.split(","), new_sentence))
        elif answer == "s":
            break
        else:
            logger.info(f"Deleting conversation starter: {sentence}")
            continue
    
    # Ask the user to lastly confirm the dataset by showing him the confirmed conversation starters
    print("Here are the confirmed conversation starters:")
    for topics, sentence in confirmed_dataset:
        print(f"{sentence}")
        print(f"Topics: {topics}")
    print("Is this dataset good enough? (y/n)")
    answer = input()
    if answer == "y":
        logger.info("Confirmed dataset, inserting in Firestore now")
        # Ask whether to tweet the dataset
        print("Do you want to tweet the dataset? (y/n)")
        answer = input()
        for topics, sentence in confirmed_dataset:
            logger.info(f"Inserting conversation starter: {','.join(topics)}:{sentence}")
            memes_collection_ref.add({
                "topics": topics,
                "content": sentence,
                "tweet": answer == "y",
                "createdAt": SERVER_TIMESTAMP,
                "disabled": False
            })
            # Random delay if tweeting
            if answer == "y":
                sleep(randint(1,3))

    else:
        logger.info("Denied dataset, aborting")



if __name__ == "__main__":
    fire.Fire(confirm)
