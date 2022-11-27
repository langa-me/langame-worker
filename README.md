# Langame worker

**WARNING**: before running any command, check the current google cloud project, firebase project and environment variable pointing to the service account JSON!


## Installation

```bash
make install
```

## Gitpod

```bash
base64 -i .env.production | tr -d '\\n'
base64 -i ./run/collection/.pypirc | tr -d '\\n'
base64 -i ./run/collection/pip.conf | tr -d '\\n'
# copy in Gitpod UI variables
```

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

## Automatic Cloud Run deployment

```bash
PROJECT_ID=$(gcloud config get-value project)

# create service account for pushing containers to gcr
# and deploying to cloud run
gcloud iam service-accounts create cloud-run-deployer \
  --display-name "Cloud Run deployer"

# Grant the appropriate Cloud Run role
# to the service account to provide repository access
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member serviceAccount:cloud-run-deployer@${PROJECT_ID}.iam.gserviceaccount.com \
  --role roles/run.admin

# get svc key
KEY_PATH="langame.cloud-run-deployer.svc.prod.json"
gcloud iam service-accounts keys create ${KEY_PATH} \
  --iam-account=cloud-run-deployer@${PROJECT_ID}.iam.gserviceaccount.com
cat ${KEY_PATH}
```
