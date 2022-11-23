import openai
from typing import List
import asyncio

async def extract_topics_from_bio(bios: List[str], aligned: bool = True) -> List[str]:
    """
    Extract a list of unique topics from a list of bios
    :param bios: list of bios
    :param aligned: if True, taking the intersection of topics from all bios
    if there is no intersection, return an union of topics
    :return: list of topics
    """
    topics_per_bio = []
    def _compute_bio(bio: str):
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
        except Exception as e:
            return []
        topics = response["choices"][0]["text"].split("\n-")
        topics = [topic.strip() for topic in topics]
        topics_per_bio.append(topics)
    
    # run in parallel
    await asyncio.gather(*[_compute_bio(bio) for bio in bios])

    if aligned:
        topics = set(topics_per_bio[0])
        for bio_topics in topics_per_bio[1:]:
            topics = topics.intersection(bio_topics)
        if not topics:
            topics = set.union(*topics_per_bio)
        return list(topics)
    return list(set.union(*topics_per_bio))

    
        
