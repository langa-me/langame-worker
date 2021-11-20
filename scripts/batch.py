from tqdm import tqdm
import time
from random import randint
from langame.langame_client import LangameClient
from langame.array import intersection
import random
import openai
import fire
from transformers import T5Tokenizer, T5ForConditionalGeneration
from langame.strings import string_similarity
import torch
import json
import logging


def generate(out_file = "generated.jsonl", topics = ["ice breaker"]):
    """
    Generate a set of conversation starters for the given topics.
    :param out_file: The file to write the generated conversations to.
    :param topics: The topics to generate conversations for.
    """
    assert isinstance(topics, list), "topics must be a list"
    assert isinstance(out_file, str), "out_file must be a string"
    assert len(topics) > 0, "No topics given."
    assert out_file.endswith(".jsonl"), "out_file must be a .jsonl file"
    
    # logger = logging.getLogger("generate")
    # logger.setLevel("INFO")
    print(f"Generating conversations for topics: {topics}")

    model_name = "flexudy/t5-small-wav2vec2-grammar-fixer"
    device = "cuda:0" if torch.cuda.is_available() else "cpu"

    tokenizer = T5Tokenizer.from_pretrained(model_name)

    model = T5ForConditionalGeneration.from_pretrained(model_name).to(device)
    c = LangameClient()
    memes = []
    for e in c._firestore_client.collection("memes").stream():
        memes.append((e.id, e.to_dict()))

    def get_prompt(topics):
        rnd = random.choices(memes, k=500)
        return [
            {"content": e[1]["content"], "topics": e[1]["topics"]}
            for e in rnd
            if len(intersection(e[1]["topics"], topics)) > 0
        ]

    covnersation_starters = []
    for i in tqdm(range(10 ** 12)):
        # time.sleep(randint(1,3))
        samples = get_prompt(topics)
        p = "\n".join([json.dumps(e) for e in samples[0:60]])
        try:
            response = openai.Completion.create(
                engine="davinci-codex",
                prompt=p + "\n",
                temperature=1,
                max_tokens=100,
                top_p=1,
                frequency_penalty=0.7,
                presence_penalty=0,
                stop=["\n"],
            )
        except Exception as e:
            print(e)
            continue
        if response["choices"][0]["finish_reason"] == "length":
            continue
        text = response["choices"][0]["text"]
        try:
            text = json.loads(text)
            input_text = "fix: { " + text["content"] + " } </s>"
        except:
            continue
        input_ids = tokenizer.encode(
            input_text,
            return_tensors="pt",
            max_length=256,
            truncation=True,
            add_special_tokens=True,
        ).to(device)

        outputs = model.generate(
            input_ids=input_ids,
            max_length=256,
            num_beams=4,
            repetition_penalty=1.0,
            length_penalty=1.0,
            early_stopping=True,
        )

        sentence = tokenizer.decode(
            outputs[0], skip_special_tokens=True, clean_up_tokenization_spaces=True
        )

        if len(sentence) < 20 or string_similarity(text["content"], sentence) < 0.5:
            continue
        covnersation_starters.append(text)
        # every 10 samples, append the generated samples to file
        if i % 10 == 0:
            with open(out_file, "a") as f:
                f.write(
                    "\n".join([json.dumps(e) for e in covnersation_starters]) + "\n"
                )
                covnersation_starters = []


if __name__ == "__main__":
    fire.Fire(generate)
