# TODO:
# from dataclasses import dataclass

# @dataclass
# class ConversationStarter:
#     """Class for ..."""
#     id: str
#     conversation_starter: dict

#     def __init__(self) -> None:
#         pass
# TODO: serialization to [topics,] ### conversation_starter
# TODO: or maybe use pytorch/tf dataloader whatever, to digest


def is_garbage(conversation_starter: dict):
    # check that conversation starter is properly a dict
    assert isinstance(
        conversation_starter, dict
    ), f"Conversation starter is not a dict, but {type(conversation_starter)}"
    # TODO: somehow check if seems like a sentence / conversation starter / not too many special chars
    return (
        "topics" not in conversation_starter
        or
        # Is not a list
        not isinstance(conversation_starter["topics"], list)
        or
        # Some topics are abnormally long
        any(
            isinstance(topic, str) and len(topic.split(" ")) > 2
            for topic in conversation_starter["topics"]
        )
        or
        # no content
        "content" not in conversation_starter
        or
        # \n in content
        "\n" in conversation_starter["content"]
    )
