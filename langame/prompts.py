from typing import Any, List, Optional
import openai
import numpy as np
from langame.quality import is_garbage
from faiss.swigfaiss import IndexFlat
from sentence_transformers import SentenceTransformer


def build_prompt(
    index: IndexFlat,
    conversation_starter_examples: List[Any],
    topics: List[str],
    prompt_rows: int = 60,
    sentence_embeddings_model: Optional[SentenceTransformer] = None,
) -> str:
    """
    Build a prompt for a GPT-like model based on a list of conversation starters.
    :param index: The faiss index to search for conversation starters.
    :param conversation_starter_examples: The list of conversation starters.
    :param topics: The list of topics.
    :param prompt_rows: The number of rows in the prompt.
    :param sentence_embedding_model: The sentence embedding model.
    :return: prompt
    """
    if not sentence_embeddings_model:
        assert index.d == 1024, (
            "Your index seems to be built using sentence embeddings, "
            + "but you did not provide a sentence embedding model, "
            + "thus using OpenAI embeddings model "
            + "will fail because of different dimensions (768 vs 1024)."
        )

        response = openai.Engine(id="ada-similarity").embeddings(
            input="artificial reality"
        )
        query = np.array([response["data"][0]["embedding"]], dtype=np.float32)
    else:
        assert (
            sentence_embeddings_model is not None
        ), "If not using OpenAI embeddings, a sentence embedding model must be provided."
        query = np.array(
            [sentence_embeddings_model.encode("immortality", show_progress_bar=False)]
        )

    most_similars = []
    _, I = index.search(
        query,
        prompt_rows
        if prompt_rows < len(conversation_starter_examples)
        else len(conversation_starter_examples),
    )
    for e in I[0]:
        if is_garbage(conversation_starter_examples[e][1]):
            continue
        most_similars.append(conversation_starter_examples[e][1])

    prompt = "\n".join(
        [f"{','.join(e['topics'])} ### {e['content']}" for e in most_similars]
    )

    return (
        prompt + "\nThis is a conversation starter about " + ",".join(topics) + " ###"
    )
