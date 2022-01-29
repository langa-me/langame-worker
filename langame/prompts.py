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
    sentence_embeddings_model: SentenceTransformer,
    prompt_rows: int = 60,
) -> str:
    """
    Build a prompt for a GPT-like model based on a list of conversation starters.
    :param index: The faiss index to search for conversation starters.
    :param conversation_starter_examples: The list of conversation starters.
    :param topics: The list of topics.
    :param sentence_embedding_model: The sentence embedding model.
    :param prompt_rows: The number of rows in the prompt.
    :return: prompt
    """
    query = np.array(
        [sentence_embeddings_model.encode(",".join(topics), show_progress_bar=False)]
    )

    most_similars = []
    _, I = index.search(
        query,
        prompt_rows
        if prompt_rows < len(conversation_starter_examples)
        else len(conversation_starter_examples),
    )
    for e in I[0]:
        if is_garbage(conversation_starter_examples[e]):
            continue
        most_similars.append(conversation_starter_examples[e])

    # remove duplicates by the property "content"
    # TODO: clean implementation
    # most_similars = [e for e in most_similars if e["content"] not in str(most_similars[:-1])]

    prompt = "\n".join(
        [f"{','.join(e['topics'])} ### {e['content']}" for e in most_similars]
    )

    return (
        prompt + "\nThis is a conversation starter about " + ",".join(topics) + " ###"
    )
