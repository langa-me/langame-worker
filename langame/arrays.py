from random import  choices
from typing import Any, List
def intersection(lst1: List, lst2: List):
    """
    This function returns the intersection of two lists.
    :param lst1: The first list.
    :type lst1: List
    :param lst2: The second list.
    :type lst2: List
    :return: The intersection of the two lists.
    """
    lst3 = [value for value in lst1 if value in lst2]
    return lst3

def get_prompt(memes: List[Any], topics: List[str]):
    rnd = choices(memes, k=500)
    return [
        {"content": e[1]["content"], "topics": e[1]["topics"]}
        for e in rnd
        if len(intersection(e[1]["topics"], topics)) > 0
    ]
