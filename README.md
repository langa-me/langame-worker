# Langame worker

**WARNING**: before running any command, check the current google cloud project, firebase project and environment variable pointing to the service account JSON!

## Installation

[Follow Google documentation directly](https://cloud.google.com/container-registry/docs/access-control#before_you_begin
)

1. Change current Google Cloud project
```bash
gcloud projects list
gcloud config set project my-project
```

2. [Optional] Create Gcloud Storage bucket

```bash
gsutil mb gs://worker-images
```

3. Allow email/service-account

```bash
gsutil iam ch [TYPE]:[EMAIL-ADDRESS]:objectAdmin gs://[BUCKET_NAME]
```

4. To create the service account and grant your service account an IAM role, run the commands
```bash
gcloud iam service-accounts create SERVICE_ACCOUNT_ID \
    --description="DESCRIPTION" \
    --display-name="DISPLAY_NAME"
    
 gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="serviceAccount:SERVICE_ACCOUNT_ID@PROJECT_ID.iam.gserviceaccount.com" \
    --role="ROLE_NAME"
```

Optional: To allow users to impersonate the service account, run the command to grant a user the Service Account User role (roles/iam.serviceAccountUser) on the service account
```bash
gcloud iam service-accounts add-iam-policy-binding \
    SERVICE_ACCOUNT_ID@PROJECT_ID.iam.gserviceaccount.com \
    --member="user:USER_EMAIL" \
    --role="roles/iam.serviceAccountUser"
```

## Usage

```bash
python3 main.py
```

## Transfer data between projects

If both projects are of different regions (otherwise jump to export/import), it's a hacky manual, using UI process:

```bash
gsutil -m cp -r "gs://langame-exports/full-snapshot/"  .
gsutil mb gs://langame-firestore
gsutil mv full-snapshot/ gs://langame-firestore/
gcloud firestore import gs://langame-firestore/full-snapshot/
```

### Export data

If not created
```bash
gsutil mb gs://langame-exports
```

Get buckets
```bash
gsutil ls
```

Export questions, for example, to the bucket "langame-exports"
```bash
gcloud firestore export gs://langame-exports --collection-ids=questions
```

Load into BigQuery
```bash
bq --location=US load \
--source_format=DATASTORE_BACKUP \
questions.questions_data \
gs://langame-exports/2021-04-17T10:32:57_17701/all_namespaces/kind_questions/all_namespaces_kind_questions.export_metadata
```

## Import data

Check IAM
```bash
gsutil iam ch serviceAccount:[DESTINATION_PROJECT_ID]@appspot.gserviceaccount.com:admin gs://[SOURCE_BUCKET]
```
i.e.
```bash
gsutil iam ch serviceAccount:langame-dev@appspot.gserviceaccount.com:admin gs://langame-exports
```

```bash
gcloud firestore import gs://[SOURCE_BUCKET]/[EXPORT_PREFIX] --async
```
i.e.
```bash
gcloud firestore import gs://langame-exports/full-snapshot --async
```

## Delete data

```bash
firebase firestore:delete langames -r --project langame-dev
```
All
```bash
firebase firestore:delete --all-collections --project langame-dev
```

## Development

### Using Conda

```bash
brew install --cask miniforge
conda init "$(basename "${SHELL}")"
conda create --name env
conda activate env
conda install --file requirements.txt
```

### Using virtualenv

```bash
virtualenv env
source env/bin/activate
arch -arch x86_64 /usr/bin/python3 -m pip install firebase-admin

```

### Docker JupyterHub

```bash
docker run -d --rm -p 8000:8000 -v $HOME/Documents:/app/ --name jupyterhub jupyterhub/jupyterhub jupyterhub
docker exec -it jupyterhub bash
pip3 install notebook
pip3 install jupyterlab
adduser basic
```

### Vars

```bash
export GOOGLE_APPLICATION_CREDENTIALS="[PATH]"
# If using Hugging Face API
export HUGGING_FACE_TOKEN="[TOKEN]"
# If using OpenAI API
export OPEN_AI_TOKEN="[TOKEN]"
# https://programmablesearchengine.google.com/about/
export GOOGLE_SEARCH_API_TOKEN="[TOKEN]"
export GOOGLE_SEARCH_CSE_ID="[CSE_ID]"
```
