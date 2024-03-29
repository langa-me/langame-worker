import logging
from multiprocessing.pool import ThreadPool
import os
import shutil
from typing import Any, Optional, Tuple, List
from google.cloud.firestore import Client
import numpy as np
from autofaiss import build_index
from sentence_transformers import SentenceTransformer
import torch
from faiss.swigfaiss import IndexFlat
from tqdm import tqdm
from langame.completion import (
    CompletionType,
    local_completion,
    openai_completion,
    huggingface_api_completion,
)
from langame.prompts import build_prompt
from langame.profanity import ProfanityThreshold, is_profane
from langame.quality import is_garbage
from langame.strings import string_similarity
from transformers import (
    GPT2LMHeadModel,
    AutoTokenizer,
    T5ForConditionalGeneration,
    T5Tokenizer,
)
from datasets import Dataset
import pandas as pd


def get_existing_conversation_starters(
    client: Client,
    use_gpu: bool = False,
    limit: int = None,
    batch_embeddings_size: int = 256,
    confirmed: bool = True,
    push_to_hub: bool = False,
) -> Tuple[List[Any], IndexFlat, SentenceTransformer]:
    """
    Get the existing conversation starters from the database.
    :param client: The firestore client.
    :param use_gpu: Whether to use the GPU for rebuilding embeddings or not.
    :param limit: The limit of the number of conversation starters to get.
    :param batch_embeddings_size: The size of the batch to use for computing embeddings.
    :param confirmed: Whether to only get confirmed conversation starters.
    :param push_to_hub: Whether to push the conversation starters to the Huggingface dataset hub.
    :return: conversation starters, faiss index, sentence embeddings model.
    """
    existing_conversation_starters = []
    collection = client.collection("memes")
    if limit:
        collection = collection.limit(limit)
    if confirmed:
        collection = collection.where("confirmed", "==", True)
    for e in tqdm(collection.stream()):
        if is_garbage(e.to_dict()):
            logging.debug(f"Skipping id: {e.id}, garbage")
            continue
        existing_conversation_starters.append({"id": e.id, **e.to_dict()})
    logging.info(
        f"Got {len(existing_conversation_starters)} existing conversation starters"
    )
    if push_to_hub:
        upload_df = pd.DataFrame(existing_conversation_starters)
        upload_df.drop(columns=["id", "confirmed", "translated"], inplace=True)
        ds = Dataset.from_pandas(upload_df)
        ds.push_to_hub("Langame/starter", private=True)

    logging.info("Preparing embeddings for existing conversation starters")
    sentence_embeddings_model = None

    sentence_embeddings_model_name = "sentence-transformers/all-MiniLM-L6-v2"
    device = "cpu"
    
    if torch.backends.mps.is_available() and torch.backends.mps.is_built():
        logging.info("Using MPS")
        device = "mps"
    if torch.cuda.is_available() and use_gpu:
        logging.info("Using GPU")
        device = "cuda:0"

    logging.info(f"Loaded sentence embedding model, device: {device}")

    sentence_embeddings_model = SentenceTransformer(
        sentence_embeddings_model_name, device=device
    )

    embeddings = []
    existing_conversation_starters_as_batch = [
        [
            e["content"]
            for e in existing_conversation_starters[i : i + batch_embeddings_size]
        ]
        for i in range(0, len(existing_conversation_starters), batch_embeddings_size)
    ]
    for i, batch in enumerate(existing_conversation_starters_as_batch):
        emb = sentence_embeddings_model.encode(
            batch, show_progress_bar=False, device=device
        )

        # extends embeddings with batch
        embeddings.extend(emb)
        logging.info(
            f"Computed embeddings - {len(batch)*(i+1)}/{len(existing_conversation_starters)}"
        )

    # flatten embeddings
    embeddings = np.array(embeddings)
    logging.info(f"Done, embeddings shape: {embeddings.shape}")

    # delete "embeddings" and "indexes" folders
    for folder in ["embeddings", "indexes"]:
        if os.path.exists(folder):
            shutil.rmtree(folder)

    logging.info("Saving embeddings to disk and building index to disk")
    os.makedirs("embeddings", exist_ok=True)
    np.save("embeddings/p1.npy", embeddings)
    index, _ = build_index(
        "embeddings",
        index_path="indexes/knn.index",
        max_index_memory_usage="6G",
        current_memory_available="7G",
    )
    return existing_conversation_starters, index, sentence_embeddings_model


def generate_conversation_starter(
    index: IndexFlat,
    conversation_starter_examples: List[Any],
    topics: List[str],
    sentence_embeddings_model: SentenceTransformer,
    prompt_rows: int = 60,
    profanity_threshold: ProfanityThreshold = ProfanityThreshold.tolerant,
    completion_type: CompletionType = CompletionType.openai_api,
    model: Optional[GPT2LMHeadModel] = None,
    tokenizer: Optional[AutoTokenizer] = None,
    use_gpu: bool = False,
    deterministic: bool = False,
    use_classification: bool = False,
    parallel_completions: int = 3,
    fix_grammar: bool = False,
    api_completion_model: Optional[str] = None,
    api_classification_model: Optional[str] = "ada:ft-personal-2022-02-08-19-57-38",
) -> Tuple[List[str], List[dict]]:
    """
    Build a prompt for the OpenAI API based on a list of conversation starters.
    :param index: The index to use.
    :param conversation_starter_examples: The list of conversation starters.
    :param topics: The list of topics.
    :param sentence_embeddings_model: The sentence embeddings model to use for building the prompt.
    :param prompt_rows: The number of rows in the prompt.
    :param profanity_threshold: Strictly above that threshold is considered profane and None is returned.
    :param completion_type: The completion type to use.
    :param model: The model to use if using local completion.
    :param tokenizer: The tokenizer to use if using local completion.
    :param use_gpu: Whether to use the GPU if using local completion.
    :param deterministic: Whether to use the deterministic version of local completion.
    :param use_classification: Whether to use the classification model.
    :param parallel_completion: The number of parallel completion to use.
    :param fix_grammar: Whether to fix grammar.
    :param api_completion_model: The api model to use.
    :param api_classification_model: The api classification model to use.
    :return: topics and conversation starters.
    """
    logging.info("Building prompt using sentence embeddings")

    topics, prompt = build_prompt(
        index=index,
        conversation_starter_examples=conversation_starter_examples,
        topics=topics,
        prompt_rows=prompt_rows,
        sentence_embeddings_model=sentence_embeddings_model,
    )
    logging.info(f"prompt: {prompt}")

    def gen(i: int) -> dict:
        text = {"conversation_starter": ""}
        if completion_type is CompletionType.openai_api:
            text["conversation_starter"] = openai_completion(
                prompt, model=api_completion_model
            )
        elif completion_type is CompletionType.local:
            # TODO: should batch local completion
            text["conversation_starter"] = local_completion(
                model, tokenizer, prompt, use_gpu=use_gpu, deterministic=deterministic
            )
        elif completion_type is CompletionType.huggingface_api:
            text["conversation_starter"] = huggingface_api_completion(prompt)
        else:
            return text
        text["conversation_starter"] = text["conversation_starter"].strip()
        logging.info(f"[{i}] conversation starter: {text['conversation_starter']}")
        if profanity_threshold.value > 1:
            # We check the whole output text,
            # in the future should probably check
            # topics and text in parallel and aggregate
            if is_profane(text["conversation_starter"]) > (
                3 - profanity_threshold.value
            ):
                text["profane"] = True
        if fix_grammar:  # TODO: might do in batch after instead
            sentence = openai_completion(
                "Correct this to standard English:\n\n" + text["conversation_starter"],
                model="text-davinci-003",
                temperature=0,
                max_tokens=len(text["conversation_starter"]) + 800,
                stop=[
                    "\n\n\n"
                ],  # TODO: hack change function code becasue None do stupid stuff
            ).strip()
            logging.info(f"[{i}] Fixed grammar: {sentence}")
            if (
                len(sentence) < 20
                or string_similarity(text["conversation_starter"], sentence) < 0.5
            ):
                # pylint: disable=logging-not-lazy
                logging.warning(
                    f"[{i}] Sentence \"{sentence}\" is too short or disimilar to \"{text['conversation_starter']}\""
                    + " after grammar fix"
                )
                return text
            elif string_similarity(text["conversation_starter"], sentence) < 0.9:
                text["broken_grammar"] = sentence
            text["conversation_starter"] = sentence
        if use_classification:
            classification = openai_completion(
                prompt=f"{','.join(topics)} ### {text['conversation_starter']} ~~~",
                model=api_classification_model,
                is_classification=True,
            )
            text["classification"] = classification
            logging.info(
                f"[{i}] {text['conversation_starter']} classification: {classification}"
            )
        return text

    # run in parallel
    with ThreadPool(processes=parallel_completions) as pool:
        conversation_starters = pool.map(gen, range(parallel_completions))
        return topics, conversation_starters
