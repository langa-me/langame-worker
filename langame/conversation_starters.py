import asyncio
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
    gooseai_completion,
)
from langame.prompts import build_prompt
from langame.profanity import ProfanityThreshold, is_profane, ProfaneException
from langame.quality import is_garbage
from langame.strings import string_similarity
from transformers import (
    GPT2LMHeadModel,
    AutoTokenizer,
    T5ForConditionalGeneration,
    T5Tokenizer,
)


def get_existing_conversation_starters(
    client: Client,
    logger: Optional[Logger] = None,
    use_gpu: bool = False,
    limit: int = None,
    batch_embeddings_size: int = 256,
    confirmed: bool = True,
) -> Tuple[List[Any], IndexFlat, SentenceTransformer]:
    """
    Get the existing conversation starters from the database.
    :param client: The firestore client.
    :param logger: The logger to use.
    :param use_gpu: Whether to use the GPU for rebuilding embeddings or not.
    :param limit: The limit of the number of conversation starters to get.
    :param batch_embeddings_size: The size of the batch to use for computing embeddings.
    :param confirmed: Whether to only get confirmed conversation starters.
    """
    existing_conversation_starters = []
    collection = client.collection("memes")
    if limit:
        collection = collection.limit(limit)
    if confirmed:
        collection = collection.where("confirmed", "==", True)
    for e in collection.stream():
        if is_garbage(e.to_dict()):
            if logger:
                logger.warning(f"Skipping id: {e.id}, garbage")
            continue
        existing_conversation_starters.append({"id": e.id, **e.to_dict()})
    if logger:
        logger.info(
            f"Got {len(existing_conversation_starters)} existing conversation starters"
        )
    if logger:
        logger.info("Preparing embeddings for existing conversation starters")
    sentence_embeddings_model = None

    sentence_embeddings_model_name = "sentence-transformers/LaBSE"
    device = "cuda:0" if torch.cuda.is_available() and use_gpu else "cpu"

    if logger:
        logger.info(f"Loaded sentence embedding model, device: {device}")

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
        if logger:
            logger.info(
                f"Computed embeddings - {len(batch)*(i+1)}/{len(existing_conversation_starters)}"
            )

    # flatten embeddings
    embeddings = np.array(embeddings)
    if logger:
        logger.info(f"Done, embeddings shape: {embeddings.shape}")

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
    logger: Optional[Logger] = None,
    use_classification: bool = False,
    parallel_completions: int = 1,
    fix_grammar: bool = False,
    grammar_model: Optional[T5ForConditionalGeneration] = None,
    grammar_tokenizer: Optional[T5Tokenizer] = None,
) -> List[dict]:
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
    :param logger: The logger to use.
    :param use_classification: Whether to use the classification model.
    :param parallel_completion: The number of parallel completion to use.
    :param fix_grammar: Whether to fix grammar.
    :return: conversation_starters
    """
    if logger:
        logger.info("Building prompt using sentence embeddings")
    prompt = build_prompt(
        index=index,
        conversation_starter_examples=conversation_starter_examples,
        topics=topics,
        prompt_rows=prompt_rows,
        sentence_embeddings_model=sentence_embeddings_model,
    )
    if logger:
        logger.info(f"prompt: {prompt}")

    async def gen() -> dict:
        text = {"conversation_starter": ""}
        if completion_type is CompletionType.openai_api:
            text["conversation_starter"] = openai_completion(prompt)
        elif completion_type is CompletionType.local:
            # TODO: should batch local completion
            text["conversation_starter"] = local_completion(
                model, tokenizer, prompt, use_gpu=use_gpu, deterministic=deterministic
            )
        elif completion_type is CompletionType.huggingface_api:
            text["conversation_starter"] = huggingface_api_completion(prompt)
        elif completion_type is CompletionType.gooseai:
            text["conversation_starter"] = gooseai_completion(prompt)
        else:
            return text
        text["conversation_starter"] = text["conversation_starter"].strip()
        if logger:
            logger.info(f"conversation starter: {text['conversation_starter']}")
        if profanity_threshold.value > 1:
            # We check the whole output text,
            # in the future should probably check
            # topics and text in parallel and aggregate
            if is_profane(text["conversation_starter"]) > (
                3 - profanity_threshold.value
            ):
                text["profane"] = True
        if fix_grammar: # TODO: might do in batch after instead
            input_text = "fix: { " + text["conversation_starter"] + " }"
            input_ids = grammar_tokenizer.encode(
                input_text,
                return_tensors="pt",
                max_length=256,
                truncation=True,
                add_special_tokens=True,
            ).to("cuda:0" if use_gpu else "cpu")

            outputs = grammar_model.generate(
                input_ids=input_ids,
                max_length=256,
                num_beams=4,
                repetition_penalty=1.0,
                length_penalty=1.0,
                early_stopping=True,
            )

            sentence = grammar_tokenizer.decode(
                outputs[0],
                skip_special_tokens=True,
                clean_up_tokenization_spaces=True,
            )
            if logger:
                logger.info(f"Fixed grammar: {sentence}")
            if (
                len(sentence) < 20
                or string_similarity(text["conversation_starter"], sentence) < 0.5
            ):
                if logger:
                    logger.warning(
                        f"Sentence \"{sentence}\" is too short or disimilar to \"{text['conversation_starter']}\""
                        + " after grammar fix"
                    )
                return text
            elif string_similarity(text["conversation_starter"], sentence) < 0.9:
                text["broken_grammar"] = sentence
            text["conversation_starter"] = sentence
        if use_classification:
            classification = openai_completion(
                prompt=f"{','.join(topics)} ### {text['conversation_starter']} ~~~",
                fine_tuned_model="ada:ft-personal-2022-02-08-19-57-38",
            )
            text["classification"] = classification
            if logger:
                logger.info(
                    f"{text['conversation_starter']} classification: {classification}"
                )
        return text

    loop = asyncio.get_event_loop()
    conversation_starters = loop.run_until_complete(
        asyncio.gather(*[gen() for _ in range(parallel_completions)])
    )

    return list(conversation_starters)
