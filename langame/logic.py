from typing import Any, List
from langame.completion import (
    CompletionType,
    build_prompt,
    local_completion,
    openai_completion,
    huggingface_api_completion,
)
from langame.profanity import ProfanityThreshold, is_profane, ProfaneException


def generate_conversation_starter(
    conversation_starter_examples: List[Any],
    topics: List[str],
    prompt_rows: int = 60,
    profanity_threshold: ProfanityThreshold = ProfanityThreshold.tolerant,
    completion_type: CompletionType = CompletionType.huggingface_api,
) -> str:
    """
    Build a prompt for the OpenAI API based on a list of conversation starters.
    :param conversation_starter_examples: The list of conversation starters.
    :param topics: The list of topics.
    :param prompt_rows: The number of rows in the prompt.
    :param profanity_threshold: Strictly above that threshold is considered profane and None is returned.
    :param completion_type: The completion type to use.
    :return: conversation_starter
    """
    prompt = build_prompt(
        conversation_starter_examples,
        topics,
        prompt_rows,
    )
    text = None
    if completion_type is CompletionType.openai_api:
        text = openai_completion(prompt)
    elif completion_type is CompletionType.local:
        text = local_completion(prompt)
    elif completion_type is CompletionType.huggingface_api:
        text = huggingface_api_completion(prompt)
    else:
        raise Exception(f"Unknown completion type {completion_type}")
    conversation_starter = text.strip()
    if profanity_threshold.value > 1:
        # We check the whole output text,
        # in the future should probably check
        # topics and text in parallel and aggregate
        if is_profane(text) > (3 - profanity_threshold.value):
            raise ProfaneException()
    return conversation_starter