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
    # topics post-processing
    topics = [topic.strip().lower() for topic in topics]

    # zero-shot completion
    if prompt_rows <= 1:
        return ",".join(topics) + " ###"

    query = np.array(
        [sentence_embeddings_model.encode(",".join(topics), show_progress_bar=False)]
    )

    most_similars = {}
    D, I = index.search(
        query,
        prompt_rows
        if prompt_rows < len(conversation_starter_examples)
        else len(conversation_starter_examples),
    )
    for i, e in enumerate(I[0]):
        if is_garbage(conversation_starter_examples[e]):
            continue
        # remove duplicates by indexing on the property "content"
        most_similars[conversation_starter_examples[e]["content"]] = {
            "distance": D[0][i],
            **conversation_starter_examples[e],
        }

    # join into a prompt string with highest similarity at the end
    prompt = "\n".join(
        [
            f"{','.join(most_similars[k]['topics'])} ### {most_similars[k]['content']}"
            for k in sorted(
                most_similars,
                key=lambda k: most_similars[k]["distance"],
                reverse=False,
            )
        ]
    )

    return prompt + "\n" + ",".join(topics) + " ###"
