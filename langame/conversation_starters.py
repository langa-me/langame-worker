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


def is_garbage(meme: dict):
    return (
        "topics" not in meme
        or
        # Is not a list
        not isinstance(meme["topics"], list)
        or
        # Some topics are abnormally long
        any(isinstance(topic, str) and len(topic.split(" ")) > 2 for topic in meme["topics"])
        or
        # no content
        "content" not in meme
        or
        # \n in content
        "\n" in meme["content"]
    )