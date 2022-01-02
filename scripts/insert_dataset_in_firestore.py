from langame import LangameClient
from firebase_admin.firestore import SERVER_TIMESTAMP
import fire
import logging
from time import sleep

def insert_dataset_in_firestore(
    in_file: str,
    delay_between_inserts: float = 3,
):
    """
    :param in_file: The file to read the messages from.
    :param delay_between_inserts: The delay between inserts.
    """
    assert isinstance(in_file, str), "out_file must be a string"
    logger = logging.getLogger("insert_dataset_in_firestore")

    logging.basicConfig(level=logging.INFO)

    logger.info(f"About to insert {in_file} into firestore")
    c = LangameClient()
    memes_collection_ref = c._firestore_client.collection("memes")

    # Ask the user if it is a deduplicated dataset
    deduplicate = input("Is this a deduplicated dataset 😇? (Y/n) ")
    # If not exit
    if deduplicate.lower() == "n":
        logger.error("Never insert non-deduplicated datasets into firestore!🤬")
        return

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

    logger.info(f"There is {len(dataset)} conversation starters to insert")

    # Ask the user if we should start inserting
    start_insert = input("Start inserting? (Y/n) ")
    if start_insert.lower() == "n":
        logger.error("Understood, bye bye!")
        return

    for topics, sentence in dataset:
        logger.info(f"Inserting conversation starter: {','.join(topics)}:{sentence}")
        result = memes_collection_ref.add(
            {
                "topics": topics,
                "content": sentence,
                "tweet": False,
                "createdAt": SERVER_TIMESTAMP,
                "disabled": True,
                "confirmed": False,
            }
        )
        logger.info(f"Inserted conversation starter: {result}")
        sleep(delay_between_inserts)

    logger.info(f"Done inserting {len(dataset)} conversation starters")

if __name__ == "__main__":
    fire.Fire(insert_dataset_in_firestore)
