from tqdm import tqdm
import time
from random import randint
import os
from langame.langame_client import LangameClient
import random
import openai
from firebase_admin import firestore

import glob

c = LangameClient()
memes = []
for e in c._firestore_client.collection('memes').stream():
    memes.append((e.id, e.to_dict()))
def intersection(lst1, lst2):
    lst3 = [value for value in lst1 if value in lst2]
    return lst3
def get_prompt(topics):
    rnd = random.choices(memes, k=500)
    return [(e[1]['content'], e[1]['topics']) for e in rnd if len(intersection(e[1]['topics'], topics)) > 0]
outputs = []
for i in tqdm(range(10**12)):
  time.sleep(randint(1,3))
  samples = get_prompt(['ice breaker'])
  p = list(str(samples[0:60]))
  # replace last char by a ","
  p[-1] = ","
  p = "".join(p)
  p = """This is a list of conversation starters ice breakers about work, school, education, travel, movies, television and music.\n
This is a list of conversation starters ice breakers about work, school, education, travel, movies, television and music.\n\n""" + p
  try:
    response = openai.Completion.create(
      engine="davinci-codex",
      prompt=p,
      temperature=1,
      max_tokens=100,
      top_p=1,
      frequency_penalty=0.7,
      presence_penalty=0,
      stop=["])"]
    )
  except Exception as e:
    print(e)
    continue
  if response["choices"][0]["finish_reason"] == "length":
    continue
  text = response["choices"][0]["text"] + "]),"
  outputs.append(text)
  # every 10 samples, append the generated samples to file
  if i % 10 == 0:
    with open("generated_samples.txt", "a") as f:
      f.write("\n".join(outputs) + "\n")
    outputs = []
  # icloud = "/Users/louisbeaumont/Library/Mobile Documents/com~apple~CloudDoc/"
  # # every 1000 samples, move file to icloud
  # if i % 10 == 0:
  #   try:
  #     # add ,\n] to the file
  #     with open("generated_samples.txt", "a") as f:
  #       f.write(",\n]")
  #     shutil.move("./generated_samples.txt", icloud + "generated_samples.txt")
  #     os.remove("generated_samples.txt")
  #   except Exception as e:
  #     print(e)
