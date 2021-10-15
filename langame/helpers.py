from typing import List, Optional

from pytrends.request import TrendReq
import pandas as pd
import openai
pytrend = TrendReq()


def clean_text(txt: str) -> str:
    txt = txt.lstrip()
    txt = txt.rstrip()
    return txt


def get_synonyms(topic: str, limit: int = 5) -> List[dict]:
    """
        # TODO: test, can fail on some topics

    Example: artificial intelligence
     - ai
     - ai artificial intelligence
     - what is artificial intelligence

     return: {"synonym": s, "value", score}
    """
    pytrend.build_payload(kw_list=[topic])
    related_topic = pytrend.related_queries()
    return [{"synonym": s["query"], "value": s["value"]} for _, s in related_topic[topic]["top"].head(limit).iterrows()]


def get_related_topics(topic: str, limit: int = 5, max_words: int = 3, max_topic_length: int = 20,
                       minimum_value: int = 40) -> List[dict]:
    """
    # TODO: test, can fail on some topics
    Example ai:
    [{'topic': 'Kizuna AI', 'value': 20750},
     {'topic': 'LG ThinQ', 'value': 17850},
     {'topic': 'Deep learning', 'value': 2050},
     {'topic': 'Robot', 'value': 400},
     {'topic': 'Intelligence', 'value': 250}]

    supposedly average english word length is 4.7 characters
    """
    pytrend.build_payload(kw_list=[topic])
    related_topic = pytrend.related_topics()
    return [{"topic": t["topic_title"], "value": t["value"]} for _, t in related_topic[topic]["rising"]
            .query("topic_type == 'Topic'")
            .drop(columns=["topic_mid", "link", "formattedValue", "topic_type"])
            .iterrows()
            if len(t["topic_title"]) <= max_topic_length and
            t["value"] >= minimum_value and
            len(t["topic_title"].split(" ")) <= max_words][:limit]


def get_suggestions(topic: str, limit: int = 5) -> List[str]:
    """
        # TODO: test, can fail on some topics
    Example: physics
     - plasma
     - modern physics
     - quantum physics

    returns list of suggestions
    """
    keywords = pytrend.suggestions(keyword=topic)
    df = pd.DataFrame(keywords)
    return [s["title"] for _, s in df.drop(columns="mid").iterrows() if topic.lower() != s["title"].lower()][:limit]

def print_markdown(file_name, model):
    t = f"""# {file_name.split("/")[-1]}
{model.get("fine_tuned_model")}
    """
    print(t)

def get_model_by_dataset_name(dataset_name):
        return [e for e in openai.FineTune.list()["data"] if e["training_files"][0]["filename"] == dataset_name][0]