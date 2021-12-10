# Langame worker

**WARNING**: before running any command, check the current google cloud project, firebase project and environment variable pointing to the service account JSON!


## Installation

```bash
make install
```

### Configuration

```bash
google:
  service_account: ...
  search_api:
    token: ...
    id: ...

openai:
  token: ...

hugging_face:
  token: ...

algolia:
  application_id:
  admin_api_key:
```

### Scripts

`python3 scripts/prepare_openai.py to_openai --in_files="['data/ice_breaker_2021_12_03.txt','data/science_2021_11_28.txt']" --out_file=data/general_$(date +"%m_%d_%Y")`
`python3 scripts/prepare_openai.py from_openai --in_file=openai.jsonl --out_file=openai.txt`
`python3 scripts/prepare_openai.py create_fine_tune --train_dataset_path=data/general_12_05_2021_train.jsonl --validation_dataset_path=data/general_12_05_2021_validation.jsonl --model=curie`