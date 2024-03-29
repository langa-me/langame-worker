import logging
from multiprocessing.pool import ThreadPool
from typing import Any, List, Tuple
import openai
import numpy as np
from langame.quality import is_garbage
from faiss.swigfaiss import IndexFlat
from sentence_transformers import SentenceTransformer
import openai
from typing import List


def post_process_inputs(topics: List[str], prioritize_short_topics: bool = True) -> List[str]:
    """
    :param topics: The list of topics.
    :param prioritize_short_topics: Taking in priority shortest topics.
    :return: The list of topics post-processed.
    """
    topics_to_return = set()
    long_topics = set()
    for topic in topics:
        t = topic.strip().lower()
        topics_to_return.add(t)
        # length > 20 or more than two spaces
        if prioritize_short_topics and len(t) > 20 or t.count(" ") > 2:
            long_topics.add(t)
    if prioritize_short_topics:
        copy_topics_to_return = topics_to_return.difference(long_topics)
        # ignore if we lose too much information
        new_len = len(copy_topics_to_return)
        if new_len > 2 and len(topics) - new_len < 3:
            topics_to_return = topics_to_return.difference(long_topics)
    return list(topics_to_return)


def build_prompt(
    index: IndexFlat,
    conversation_starter_examples: List[Any],
    topics: List[str],
    sentence_embeddings_model: SentenceTransformer,
    prompt_rows: int = 60,
) -> Tuple[List[str], str]:
    """
    Build a prompt for a GPT-like model based on a list of conversation starters.
    :param index: The faiss index to search for conversation starters.
    :param conversation_starter_examples: The list of conversation starters.
    :param topics: The list of topics.
    :param sentence_embedding_model: The sentence embedding model.
    :param prompt_rows: The number of rows in the prompt.
    :return: processed topics and prompt
    """
    # topics post-processing
    topics = post_process_inputs(topics)

    # zero-shot completion
    if prompt_rows <= 1:
        return topics, ",".join(topics) + " ###"

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

    return topics, prompt + "\n" + ",".join(topics) + " ###"


def extract_topics_from_personas(
    personas: List[str], aligned: bool = True
) -> List[str]:
    """
    Extract a list of unique topics from a list of personas
    :param personas: list of personass
    :param aligned: if True, taking the intersection of topics from all personass
    if there is no intersection, return an union of topics
    :return: list of topics
    """

    def _compute_persona(bio: str):
        prompt = f"User biography:\n{bio}\nList of interests:\n-"
        try:
            response = openai.Completion.create(
                model="text-davinci-003",
                prompt=prompt,
                temperature=0.7,
                max_tokens=256,
                top_p=1,
                frequency_penalty=0.1,
                presence_penalty=0.1,
            )
            topics = response["choices"][0]["text"].split("\n-")
            topics = [topic.strip() for topic in topics]
            return topics
        except Exception as e:
            logging.warning(f"Error while computing topics for persona: {e}")
            return []

    # run in parallel
    with ThreadPool(processes=len(personas)) as pool:
        topics_per_persona = pool.map(_compute_persona, personas)

    if len(topics_per_persona) == 0:
        logging.warning("Could not extract topics from personas")
        return []

    if aligned:
        topics = set(topics_per_persona[0])
        for persona_topics in topics_per_persona[1:]:
            topics = topics.intersection(persona_topics)
        if not topics:
            topics = set().union(*topics_per_persona)
        return list(topics)
    return list(set().union(*topics_per_persona))
