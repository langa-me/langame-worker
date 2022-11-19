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

`python3 scripts/insert_dataset_in_firestore.py --in_file=data/dataset.txt`

`python3 scripts/confirm_conversation_starter.py --in_file=data/dataset.txt`

`python3 scripts/deduplicate_dataset.py --in_file=data/dataset.txt`

`python3 scripts/batch_generate.py generate --out_file=data/common --randomize=True --topics="['education','romance','family','music','film','work','party','food','travel','psychology']"`

`python3 scripts/batch_generate.py generate --out_file=data/least_used.txt --use_least_used_topics=True`

`python3 scripts/prepare_openai.py to_openai --in_files="['data/ice_breaker_2021_12_03.txt','data/science_2021_11_28.txt']" --out_file=data/general_$(date +"%m_%d_%Y")`

`python3 scripts/prepare_openai.py from_openai --in_file=openai.jsonl --out_file=openai.txt`

`python3 scripts/prepare_openai.py create_fine_tune --train_dataset_path=data/general_12_05_2021_train.jsonl --validation_dataset_path=data/general_12_05_2021_validation.jsonl --model=curie`

`python3 scripts/load_test_api.py`


## Push library to GCP

```bash
source env/bin/activate
REGION="us-central1"

gcloud artifacts repositories create langame \
  --repository-format python \
  --location ${REGION} \
  --description "Langame Python package repository"

gcloud config set artifacts/repository langame
gcloud config set artifacts/location ${REGION}
PROJECT_ID=$(gcloud config get-value project)
URL="https://${REGION}-python.pkg.dev/${PROJECT_ID}/langame"

# create service account for uploading artifacts to artifact
# registry in gcp
gcloud iam service-accounts create artifacts-uploader \
  --display-name "Artifacts uploader"

# Grant the appropriate Artifact Registry role
# to the service account to provide repository access
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member serviceAccount:artifacts-uploader@${PROJECT_ID}.iam.gserviceaccount.com \
  --role roles/artifactregistry.admin
# TODO: narrow down permission
# add artifactregistry.repositories.uploadArtifacts
#gcloud projects add-iam-policy-binding ${PROJECT_ID} \
#  --member serviceAccount:artifacts-uploader@${PROJECT_ID}.iam.gserviceaccount.com \
#  --role roles/artifactregistry.repositories.uploadArtifacts
# get svc key
KEY_PATH="langame.artifacts-uploader.svc.prod.json"
gcloud iam service-accounts keys create ${KEY_PATH} \
  --iam-account=artifacts-uploader@${PROJECT_ID}.iam.gserviceaccount.com

export GOOGLE_APPLICATION_CREDENTIALS=${KEY_PATH}

# write everything from "[distutils]" to "password:" to "~/.pypirc"
gcloud artifacts print-settings python \
    --project ${PROJECT_ID} \
    --repository langame \
    --location ${REGION} \
    --json-key ${KEY_PATH} \
    | sed '1,10!d' > $HOME/.pypirc

# https://pip.pypa.io/en/stable/topics/configuration/#location
# write everything after "# Insert the following snippet into your pip.conf"
# into "$HOME/.pip/pip.conf"
DIR=$HOME/.config/pip/
mkdir -p $HOME/.config/pip/
gcloud artifacts print-settings python \
    --project ${PROJECT_ID} \
    --repository langame \
    --location ${REGION} \
    --json-key ${KEY_PATH} \
    | sed '11,$!d' | tee ${DIR}/pip.conf $VIRTUAL_ENV/pip.conf

pip install build twine keyrings.google-artifactregistry-auth
python3 -m build
gcloud auth login
twine upload --repository-url ${URL}/ dist/*
```
