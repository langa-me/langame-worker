# Langame worker

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

## Development

```bash
export GOOGLE_APPLICATION_CREDENTIALS="[PATH]"
# If using Hugging Face API
export HUGGING_FACE_TOKEN="[TOKEN]"
```
