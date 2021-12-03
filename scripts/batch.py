from langame.langame_client import LangameClient
from langame.arrays import get_prompt
import openai
import fire
from transformers import T5Tokenizer, T5ForConditionalGeneration
from langame.strings import string_similarity
import torch
import json
import datetime
import logging

class FuckOpenAIFilter(logging.Filter):
    def filter(self, record):
        return "OpenAI" not in str(record)

def generate(out_file="data/ice_breaker.txt", topics=["ice breaker"], use_gpu=False):
    """
    Generate a set of conversation starters for the given topics.
    :param out_file: The file to write the generated conversations to.
    :param topics: The topics to generate conversations for.
    :param use_gpu: Whether to use the GPU.
    """
    assert isinstance(topics, list), "topics must be a list"
    assert isinstance(out_file, str), "out_file must be a string"
    assert len(topics) > 0, "No topics given."
    assert out_file.endswith(".txt"), "out_file must be a .txt file"
    logger = logging.getLogger("batch")
    logger.addFilter(FuckOpenAIFilter())

    logging.basicConfig(level=logging.INFO)
    # Add the date to the out file before the extension with format YYYY_MM_DD
    out_file = out_file.replace(
        ".txt", f"_{datetime.datetime.now().strftime('%Y_%m_%d')}.txt"
    )

    logger.info(f"Generating conversations for topics: {topics}, writing to {out_file}")

    grammar_model_name = "flexudy/t5-small-wav2vec2-grammar-fixer"
    device = "cuda:0" if torch.cuda.is_available() and use_gpu else "cpu"

    logger.info(f"Device: {device}")

    tokenizer = T5Tokenizer.from_pretrained(grammar_model_name)
    grammar_model = T5ForConditionalGeneration.from_pretrained(grammar_model_name).to(
        device
    )

    c = LangameClient()
    existing_memes = []
    for e in c._firestore_client.collection("memes").stream():
        existing_memes.append((e.id, e.to_dict()))

    covnersation_starters = []
    for i in range(10 ** 12):
        # time.sleep(randint(1,3))
        samples = get_prompt(existing_memes, topics)
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
            logger.error(e)
            continue
        if response["choices"][0]["finish_reason"] == "length":
            continue
        text = response["choices"][0]["text"]
        try:
            text = json.loads(text)
            # If text does not have "content" or "topics"
            # or "content" is not a string or "topics" is not a list of strings
            if (
                "content" not in text
                or "topics" not in text
                or not isinstance(text["content"], str)
                or not isinstance(text["topics"], list)
            ):
                continue
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

        outputs = grammar_model.generate(
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
                    "\n".join(
                        [
                            ",".join(e["topics"]) + " ### " + e["content"]
                            for e in covnersation_starters
                        ]
                    )
                    + "\n"
                )
                covnersation_starters = []
                # print number of total rows in the file
                total_rows = sum(1 for _ in open(out_file))
                logger.info(f"total {total_rows} rows written to {out_file}")


if __name__ == "__main__":
    fire.Fire(generate)
