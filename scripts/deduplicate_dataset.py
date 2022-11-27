from faiss.swigfaiss import Index
from langame.langame_client import LangameClient
import fire
import torch
import datetime
import faiss
import glob
from sentence_transformers import SentenceTransformer
import numpy as np
import logging
from autofaiss import build_index
import os
from collections import defaultdict


def connected_components(neighbors):
    seen = set()

    def component(node):
        r = []
        nodes = set([node])
        while nodes:
            node = nodes.pop()
            seen.add(node)
            nodes |= set(neighbors[node]) - seen
            r.append(node)
        return r

    u = []
    for node in list(neighbors):
        if node not in seen:
            u.append(component(node))
    return u


def get_uniques(
    index: Index, embeddings, max_duplicates_per_item: int = 10, threshold: float = 0.9
):
    D, I = index.search(embeddings, k=max_duplicates_per_item)

    same_mapping = defaultdict(list)

    for i, (d, r_i) in enumerate(zip(D, I)):
        for dd, rr in zip(d, r_i):
            if dd > threshold:
                same_mapping[int(i)].append(int(rr))

    groups = connected_components(same_mapping)
    uniques = []
    for g in groups:
        uniques.append(g[0])

    return uniques


def dedup(
    in_file=None,
    use_gpu=False,
):
    """
    Deduplicate a dataset according to the similarity of the sentences.
    :param in_file: The file to read the dataset from.
    :param out_file: The file to write the deduplicated dataset to.
    :param use_gpu: Whether to use the GPU.
    """
    assert isinstance(in_file, str), "out_file must be a string"
    logger = logging.getLogger("deduplicate_dataset")
    logging.basicConfig(level=logging.INFO)
    logger.warning(
        "Assuming the input dataset rows are of format [topics,] ### [sentence]"
    )

    # Add the date to the out file before the extension with format YYYY_MM_DD
    out_file = in_file.replace(".txt", "_dedup.txt")

    logger.info(f"Deduplicating dataset from {in_file}, writing to {out_file}")

    # Skip the meme generated under this similarity threshold
    SIMILARITY_THRESHOLD = 0.8

    sentence_embeddings_model_name = "sentence-transformers/all-MiniLM-L6-v2"
    device = "cuda:0" if torch.cuda.is_available() and use_gpu else "cpu"

    logger.info(f"Device: {device}")

    sentence_embeddings_model = SentenceTransformer(
        sentence_embeddings_model_name, device=device
    )

    c = LangameClient()
    existing_memes = []
    for e in c._firestore_client.collection("memes").stream():
        if "content" in e.to_dict():
            existing_memes.append((e.id, e.to_dict()))
        else:
            logger.warning(f"Skipping meme {e.id}, no content")

    logger.info("Building embeddings for existing memes")

    existing_memes_embeddings = []
    for i, v in enumerate(existing_memes):
        existing_memes_embeddings.append(
            sentence_embeddings_model.encode(v[1]["content"], show_progress_bar=False)
        )
        if i % 1000 == 0:
            logger.info(f"Built embeddings for {i+1000} existing memes")

    new_memes = []
    new_memes_embeddings = []

    with open(in_file, "r") as f:
        lines = f.readlines()
        logger.info(f"Now building embeddings for {len(lines)} new memes")
        for i, line in enumerate(lines):
            if i % 1000 == 0:
                logger.info(f"Built embeddings for {i+1000} new memes")
            line = line.strip()
            # Check that the format is correct
            # i.e. [topics,] ### [sentence]
            splitted = line.split("###")
            if line and len(splitted) == 2:
                topics, sentence = splitted
                new_memes.append(line)
                new_memes_embeddings.append(
                    sentence_embeddings_model.encode(
                        sentence.strip(), show_progress_bar=False
                    )
                )

    new_memes_embeddings = np.array(new_memes_embeddings)
    logger.info(f"Done, new memes embeddings of shape {new_memes_embeddings.shape}")
    if len(new_memes_embeddings) == 0:
        logger.error("Failed to build new memes embeddings, exiting")
        return

    # Create the faiss indexes
    existing_memes_embeddings_dir = "embeddings/existing_memes_embeddings"
    new_memes_embeddings_dir = "embeddings/new_memes_embeddings"
    existing_memes_index_dir = "embeddings/existing_memes_indexes"
    new_memes_index_dir = "embeddings/new_memes_indexes"
    os.makedirs(existing_memes_embeddings_dir, exist_ok=True)
    os.makedirs(new_memes_embeddings_dir, exist_ok=True)
    np.save(f"{existing_memes_embeddings_dir}/p1.npy", existing_memes_embeddings)
    np.save(f"{new_memes_embeddings_dir}/p1.npy", new_memes_embeddings)
    logger.info("Done, now building indexes")

    build_index(
        embeddings=existing_memes_embeddings_dir,
        index_path=f"{existing_memes_index_dir}/knn.index",
        max_index_memory_usage="6G",
        current_memory_available="7G",
    )
    build_index(
        embeddings=new_memes_embeddings_dir,
        index_path=f"{new_memes_index_dir}/knn.index",
        max_index_memory_usage="6G",
        current_memory_available="7G",
    )
    existing_memes_index = faiss.read_index(
        glob.glob(f"{existing_memes_index_dir}/*.index")[0]
    )
    new_memes_index = faiss.read_index(glob.glob(f"{new_memes_index_dir}/*.index")[0])

    logger.info("Done, now filtering duplicates")

    # Get the new uniques
    new_uniques = get_uniques(
        new_memes_index,
        new_memes_embeddings,
        max_duplicates_per_item=10,
        threshold=SIMILARITY_THRESHOLD,
    )
    new_uniques_embeddings = new_memes_embeddings[new_uniques]

    # Get the new NEW uniques
    new_new_uniques = get_uniques(
        existing_memes_index,
        new_uniques_embeddings,
        max_duplicates_per_item=10,
        threshold=SIMILARITY_THRESHOLD,
    )

    # Write to out file
    with open(out_file, "w") as f:
        logger.info(f"Done, now writing to {out_file}")
        for new_unique in new_new_uniques:
            f.write(new_memes[new_unique] + "\n")
    logger.info(
        f"Deduplicated {len(new_memes)} into {len(new_new_uniques)} new memes, wrote to {out_file}"
    )


if __name__ == "__main__":
    fire.Fire(dedup)
