from logging import Logger
import os
import shutil
from typing import Any, Optional, Tuple, List
from google.cloud.firestore import Client
import numpy as np
from autofaiss import build_index
from sentence_transformers import SentenceTransformer
import torch
from faiss.swigfaiss import IndexFlat
from langame.completion import (
    CompletionType,
    local_completion,
    openai_completion,
    huggingface_api_completion,
)
from langame.prompts import build_prompt
from langame.profanity import ProfanityThreshold, is_profane, ProfaneException
from langame.quality import is_garbage
from transformers import GPT2LMHeadModel, AutoTokenizer


def get_existing_conversation_starters(
    client: Client,
    embeddings: bool = True,
    rebuild_embeddings: bool = False,
    logger: Optional[Logger] = None,
    use_gpu: bool = False,
    limit: int = None,
) -> Tuple[List[Any], Optional[IndexFlat], Optional[SentenceTransformer]]:
    """
    Get the existing conversation starters from the database.
    :param client: The firestore client.
    :param embeddings: Whether to get the embeddings or not.
    :param rebuild_embeddings: Whether to rebuild the embeddings or not.
    :param logger: The logger to use.
    :param use_gpu: Whether to use the GPU for rebuilding embeddings or not.
    :param limit: The limit of the number of conversation starters to get.
    """
    # should fail if embeddings is false and rebuild_embeddings is true
    assert not (
        not embeddings and rebuild_embeddings
    ), "Won't rebuild embeddings if embeddings are not used."

    existing_memes = []
    collection = client.collection("memes")
    if limit:
        collection = collection.limit(limit)
    if embeddings:
        # https://stackoverflow.com/questions/49579693/how-do-i-get-documents-where-a-specific-field-exists-does-not-exists-in-firebase
        collection.order_by("embedding")
    for e in collection.stream():
        existing_memes.append((e.id, e.to_dict()))
    if logger:
        logger.info(f"Got {len(existing_memes)} existing memes")
    if not embeddings:
        return existing_memes, None, None
    if logger:
        logger.info("Preparing embeddings for existing memes")
    embeddings = []
    memes_with_embedding = []
    sentence_embeddings_model = None
    if rebuild_embeddings:
        sentence_embeddings_model_name = "sentence-transformers/LaBSE"
        device = "cuda:0" if torch.cuda.is_available() and use_gpu else "cpu"

        if logger:
            logger.info(f"Loaded sentence embedding model, device: {device}")

        sentence_embeddings_model = SentenceTransformer(
            sentence_embeddings_model_name, device=device
        )

    for e in existing_memes:
        if is_garbage(e[1]):
            if logger:
                logger.warning(
                    f"Skipping meme {e[0]}, garbage, content: {e[1]['content']},"
                    + f" topics: {e[1]['topics']}"
                )
            continue

        if rebuild_embeddings:
            # TODO: building embeddings should probably be faster if done in batches
            # especially on GPU, but for now it's ok since we only run it at
            # startup time?
            if logger:
                logger.info(f"Rebuilding embedding for meme {e[0]}")
            e[1]["embedding"] = sentence_embeddings_model.encode(
                e[1]["content"], show_progress_bar=False
            )

        if "embedding" in e[1]:
            memes_with_embedding.append(e)
            # turn to np array
            memes_with_embedding[-1][1]["embedding"] = np.array(
                memes_with_embedding[-1][1]["embedding"]
            )
            # add to embeddings
            embeddings.append(memes_with_embedding[-1][1]["embedding"])
    if logger:
        logger.info(f"Got {len(memes_with_embedding)} memes with embeddings")

    if len(memes_with_embedding) == 0:
        return memes_with_embedding, None

    # delete "embeddings" and "indexes" folders
    for folder in ["embeddings", "indexes"]:
        if os.path.exists(folder):
            shutil.rmtree(folder)

    if logger:
        logger.info("Saving embeddings to disk and building index to disk")
    os.makedirs("embeddings", exist_ok=True)
    np.save("embeddings/p1.npy", embeddings)
    index, _ = build_index(
        "embeddings",
        index_path="indexes/knn.index",
        max_index_memory_usage="6G",
        current_memory_available="7G",
    )
    return memes_with_embedding, index, sentence_embeddings_model


def generate_conversation_starter(
    index: IndexFlat,
    conversation_starter_examples: List[Any],
    topics: List[str],
    prompt_rows: int = 60,
    profanity_threshold: ProfanityThreshold = ProfanityThreshold.tolerant,
    completion_type: CompletionType = CompletionType.openai_api,
    model: Optional[GPT2LMHeadModel] = None,
    tokenizer: Optional[AutoTokenizer] = None,
    use_gpu: bool = False,
    deterministic: bool = False,
    logger: Optional[Logger] = None,
    sentence_embeddings_model: Optional[SentenceTransformer] = None,
) -> str:
    """
    Build a prompt for the OpenAI API based on a list of conversation starters.
    :param index: The index to use.
    :param conversation_starter_examples: The list of conversation starters.
    :param topics: The list of topics.
    :param prompt_rows: The number of rows in the prompt.
    :param profanity_threshold: Strictly above that threshold is considered profane and None is returned.
    :param completion_type: The completion type to use.
    :param model: The model to use if using local completion.
    :param tokenizer: The tokenizer to use if using local completion.
    :param use_gpu: Whether to use the GPU if using local completion.
    :param deterministic: Whether to use the deterministic version of local completion.
    :param logger: The logger to use.
    :param sentence_embeddings_model: The sentence embeddings model to use for building the prompt.
    :return: conversation_starter
    """
    if logger:
        logger.info(
            "Building prompt using OpenAI embeddings"
            if sentence_embeddings_model is None
            else "Building prompt using sentence embeddings"
        )
    prompt = build_prompt(
        index=index,
        conversation_starter_examples=conversation_starter_examples,
        topics=topics,
        prompt_rows=prompt_rows,
        sentence_embeddings_model=sentence_embeddings_model,
    )
    if logger:
        logger.info(f"prompt: {prompt}")
    text = None
    if completion_type is CompletionType.openai_api:
        text = openai_completion(prompt)
    elif completion_type is CompletionType.local:
        assert (
            model is not None and tokenizer is not None
        ), "model and tokenizer must be provided"
        text = local_completion(
            model, tokenizer, prompt, use_gpu=use_gpu, deterministic=deterministic
        )
    elif completion_type is CompletionType.huggingface_api:
        text = huggingface_api_completion(prompt)
    else:
        raise Exception(f"Unknown completion type {completion_type}")
    conversation_starter = text.strip()
    if logger:
        logger.info(f"conversation_starter: {conversation_starter}")
    if profanity_threshold.value > 1:
        # We check the whole output text,
        # in the future should probably check
        # topics and text in parallel and aggregate
        if is_profane(text) > (3 - profanity_threshold.value):
            raise ProfaneException()
    return conversation_starter
