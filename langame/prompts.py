from typing import Any, Coroutine, List, Optional
import openai
import numpy as np
from langame.quality import is_garbage
from faiss.swigfaiss import IndexFlat
from sentence_transformers import SentenceTransformer
import openai
from typing import List
import asyncio


def post_process_inputs(topics: List[str]) -> List[str]:
    """
    :param topics: The list of topics.
    :return: The list of topics post-processed.
    """
    return list(set([topic.strip().lower() for topic in topics]))


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
    topics = post_process_inputs(topics)

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


async def extract_topics_from_personas(
    personas: List[str], aligned: bool = True
) -> Coroutine[Any, Any, List[str]]:
    """
    Extract a list of unique topics from a list of personas
    :param personas: list of personass
    :param aligned: if True, taking the intersection of topics from all personass
    if there is no intersection, return an union of topics
    :return: list of topics
    """
    topics_per_bio = []

    async def _compute_bio(bio: str):
        prompt = f"User self biography:\n{bio}\nConversation topics:\n-"
        try:
            response = openai.Completion.create(
                model="text-davinci-002",
                prompt=prompt,
                temperature=0.7,
                max_tokens=256,
                top_p=1,
                frequency_penalty=0.1,
                presence_penalty=0.1,
            )
            topics = response["choices"][0]["text"].split("\n-")
            topics = [topic.strip() for topic in topics]
            topics_per_bio.append(topics)
        except:  # pylint: disable=bare-except
            return []

    # run in parallel
    await asyncio.gather(*[_compute_bio(bio) for bio in bios])

    if aligned:
        topics = set(topics_per_bio[0])
        for bio_topics in topics_per_bio[1:]:
            topics = topics.intersection(bio_topics)
        if not topics:
            topics = set().union(*topics_per_bio)
        return list(topics)
    return list(set().union(*topics_per_bio))
