import os
import fire
import logging
import datetime
from datasets import load_dataset
from transformers import AutoModelForCausalLM, TrainingArguments, Trainer, AutoTokenizer
from langame.conversation_starters import get_existing_conversation_starters
from langame import LangameClient

def train(num_train_epochs: int = 200):
    """
    Train a model
    """
    c = LangameClient("./config.yaml")

    logger = logging.getLogger("classification")
    memes, _, __ = get_existing_conversation_starters(
        c._firestore_client, logger=logger, confirmed=True)
    out_file_name = f"./data/fine_tune_topic_classification_{datetime.date.today().strftime('%d_%m_%Y')}.txt"

    try:
        os.remove(out_file_name)
    except:
        pass
    for e in memes:
        with open(out_file_name, "a+") as outfile:
            if len(e['topics']) == 0: continue
            outfile.write(f"{e['content']} ### {','.join(map(str, e['topics']))}\n")


    # split the file into train.txt and eval.txt
    with open(out_file_name, "r") as f:
        lines = f.readlines()
        train_lines = lines[:int(len(lines) * 0.8)]
        eval_lines = lines[int(len(lines) * 0.8):]
        with open("train.txt", "w") as f:
            f.writelines(train_lines)
        with open("eval.txt", "w") as f:
            f.writelines(eval_lines)
    dataset = load_dataset('text', data_files={"train": "train.txt", "eval": "eval.txt"})

    model = AutoModelForCausalLM.from_pretrained("distilgpt2", eos_token_id=198)
    tokenizer = AutoTokenizer.from_pretrained("distilgpt2")
    tokenizer.pad_token = tokenizer.eos_token
    def preprocess_function(x):
        return tokenizer([e + "\n" for e in x["text"]])
    tokenized_eli5 = dataset.map(
        preprocess_function,
        batched=True,
        num_proc=4,
        remove_columns=["text"],
    )
    block_size = 128


    def group_texts(examples):
        # Concatenate all texts.
        concatenated_examples = {k: sum(examples[k], []) for k in examples.keys()}
        total_length = len(concatenated_examples[list(examples.keys())[0]])
        # We drop the small remainder, we could add padding if the model supported it instead of this drop, you can
        # customize this part to your needs.
        total_length = (total_length // block_size) * block_size
        # Split by chunks of max_len.
        result = {
            k: [t[i : i + block_size] for i in range(0, total_length, block_size)]
            for k, t in concatenated_examples.items()
        }
        result["labels"] = result["input_ids"].copy()
        return result
    lm_datasets = tokenized_eli5.map(
        group_texts,
        batched=True,
        batch_size=1000,
        num_proc=4,
    )
    training_args = TrainingArguments(
        output_dir="./models",
        evaluation_strategy="epoch",
        # learning_rate=2e-5,
        # weight_decay=0.01,
        num_train_epochs=num_train_epochs,
        # auto_find_batch_size=True,
        hub_model_id="Langame/distilgpt2-starter-classification",
        push_to_hub=True,
    )

    trainer = Trainer(
        model=model,
        tokenizer=tokenizer,
        args=training_args,
        train_dataset=lm_datasets["train"],
        eval_dataset=lm_datasets["eval"],
    )

    trainer.train()

if __name__ == "__main__":
    fire.Fire(train)
