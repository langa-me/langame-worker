# experiment try of gcp api gateway

https://cloud.google.com/api-gateway/docs/quickstart

```bash
PROJECT_ID=$(gcloud config get-value project)
API="conversation-starter"
SVC_NAME="api-gateway"
USER_EMAIL="louis.beaumont@gmail.com"
API_GATEWAY_CONFIG="conversation-starter-basic"
REGION="us-central1"
GATEWAY="$API-gateway"
gcloud components update
gcloud config set project ${PROJECT_ID}
gcloud services enable apigateway.googleapis.com
gcloud services enable servicemanagement.googleapis.com
gcloud services enable servicecontrol.googleapis.com
gcloud api-gateway apis create ${API} --project=${PROJECT_ID}
gcloud api-gateway apis describe ${API} --project=${PROJECT_ID}
gcloud iam service-accounts create ${SVC_NAME} \
    --description="Manage the API gateway" \
    --display-name="${SVC_NAME}"
SVC=$(gcloud iam service-accounts list | grep "${SVC_NAME}"  | awk '{print $2}')
gcloud iam service-accounts add-iam-policy-binding ${SVC} \
    --member user:${USER_EMAIL} \
    --role roles/iam.serviceAccountUser
gcloud api-gateway api-configs create ${API_GATEWAY_CONFIG} \
  --api=${API} --openapi-spec=gateway/openapi-functions.yaml \
  --project=${PROJECT_ID} --backend-auth-service-account=${SVC}
gcloud api-gateway api-configs describe ${API_GATEWAY_CONFIG} \
  --api=${API} --project=${PROJECT_ID}
gcloud api-gateway gateways create ${GATEWAY} \
  --api=${API} --api-config=${API_GATEWAY_CONFIG} \
  --location=${REGION} --project=${PROJECT_ID}
HOSTNAME=$(gcloud api-gateway gateways describe ${GATEWAY} --location=${REGION} --project=${PROJECT_ID} | grep defaultHostname | awk '{print $2}')
API_KEY_NAME="foo"
# api target does not work
gcloud alpha services api-keys create --display-name=${API_KEY_NAME} #--api-target=service=apigateway.googleapis.com #--api-target=service=cloudfunctions.googleapis.com
API_KEY_FULL_NAME=$(gcloud alpha services api-keys list | grep ${API_KEY_NAME} | awk '{print $1}')
API_KEY_VALUE=$(gcloud alpha services api-keys get-key-string ${API_KEY_FULL_NAME} | awk '{print $2}')
APP_ID_NAME="bar"
gcloud alpha services api-keys create --display-name=${APP_ID_NAME} #--api-target=service=apigateway.googleapis.com #--api-target=service=cloudfunctions.googleapis.com
APP_ID_FULL_NAME=$(gcloud alpha services api-keys list | grep ${APP_ID_NAME} | awk '{print $1}')
APP_ID_VALUE=$(gcloud alpha services api-keys get-key-string ${APP_ID_FULL_NAME} | awk '{print $2}')
curl -X POST https://$HOSTNAME/v1/conversation/starter \
    -H "X-API-KEY: ${API_KEY_VALUE}" \
    -H "X-APP-ID: ${APP_ID_VALUE}"
# Securing access by using an API key
MANAGED_SERVICE=$(gcloud api-gateway apis describe ${API} | grep managedService | awk '{print $2}')
gcloud services enable ${MANAGED_SERVICE}
```

## Updating the config

```bash
API_GATEWAY_CONFIG="conversation-starter-key2"

gcloud api-gateway api-configs create ${API_GATEWAY_CONFIG} \
  --api=${API} --openapi-spec=gateway/openapi-functions.yaml \
  --project=${PROJECT_ID} --backend-auth-service-account=${SVC}

gcloud api-gateway gateways update ${GATEWAY} \
  --api=${API} --api-config=${API_GATEWAY_CONFIG} \
  --location=${REGION} --project=${PROJECT_ID}
```