GCLOUD_PROJECT:=$(shell gcloud config list --format 'value(core.project)' 2>/dev/null)
FUNCTION_NAME ?= "public_starter"
API_NAME ?= "starter"
API_GATEWAY_CONFIG_NAME ?= "starter-gateway"
GCP_RUN_SVC:=$(shell gcloud iam service-accounts list --filter="Default compute service account" --format 'value(email)' 2>/dev/null)
API_GATEWAY_SVC ?= "api-gateway-svc"
API_GATEWAY_SVC_FULL:=$(shell echo "${API_GATEWAY_SVC}@${GCLOUD_PROJECT}.iam.gserviceaccount.com")

USER_EMAIL="louis.beaumont@gmail.com"
API_GATEWAY_CONFIG="starter-basic"
REGION="us-central1"
GATEWAY_NAME:=$(shell echo "${API_NAME}-gateway")
NEG_NAME ?= "api-gateway-serverless-neg"
BACKEND_SERVICE_NAME ?= "api-gateway-serverless-backend"
API_GATEWAY_URL_MAP_NAME ?= "api-gateway-serverless-url-map"
SSL_CERTIFICATE_NAME ?= "api-gateway-serverless-ssl-cert"
DOMAIN ?= "api.langa.me"
TARGET_HTTP_PROXY_NAME ?= "api-gateway-serverless-target-http-proxy"
HTTPS_FORWARDING_RULE_NAME ?= "api-gateway-serverless-https-forwarding-rule"


API_GATEWAY_HOSTNAME=$(shell gcloud api-gateway gateways describe ${GATEWAY_NAME} --location=${REGION} --project=${GCLOUD_PROJECT} --format 'value(defaultHostname)' 2>/dev/null)
API_KEY_NAME ?= "api-gateway-serverless-key"
API_KEY_FULL_NAME=$(shell gcloud alpha services api-keys list --project=${GCLOUD_PROJECT} --filter="api-gateway-serverless-key" --format 'value(name)' 2>/dev/null)
API_KEY_VALUE=$(shell gcloud alpha services api-keys get-key-string ${API_KEY_FULL_NAME} --project=${GCLOUD_PROJECT} --format 'value(keyString)' 2>/dev/null)
# sed to remove https://
AVA_URL=$(shell gcloud run services list --filter="conversation-starter" --format 'value(URL)' | sed 's/https:\/\///g' 2>/dev/null)
setup: ## [Local development] setup the GCP project
	# gcloud components update
	# gcloud config set project ${PROJECT_ID}
	# gcloud services enable apigateway.googleapis.com
	# gcloud services enable servicemanagement.googleapis.com
	# gcloud services enable servicecontrol.googleapis.com
	# gcloud iam service-accounts create ${API_GATEWAY_SVC} \
	# 	--description="api gateway service account" \
	# 	--display-name="${API_GATEWAY_SVC}"
	# gcloud iam service-accounts add-iam-policy-binding ${API_GATEWAY_SVC_FULL} \
	# 	--member user:louis.beaumont@gmail.com \
	# 	--role roles/iam.serviceAccountUser
	# gcloud api-gateway apis create ${API_NAME} --project=${GCLOUD_PROJECT}
	# gcloud api-gateway api-configs create ${API_GATEWAY_CONFIG_NAME} \
  	# 	--api=${API_NAME} \
	# 	--openapi-spec=openapi2.yaml \
  	# 	--project=${GCLOUD_PROJECT} \
	# 	--backend-auth-service-account=${API_GATEWAY_SVC_FULL}
	# gcloud api-gateway gateways create ${GATEWAY_NAME} \
	# 	--api=${API_NAME} \
	# 	--api-config=${API_NAME} \
	# 	--location=${REGION} \
	# 	--project=${GCLOUD_PROJECT}
	# gcloud beta compute network-endpoint-groups create ${NEG_NAME} \
	# 	--region=${REGION} \
	#	--project=${GCLOUD_PROJECT} \
	# 	--network-endpoint-type=serverless \
	# 	--serverless-deployment-platform=apigateway.googleapis.com \
	# 	--serverless-deployment-resource=${GATEWAY_NAME}
	# gcloud compute backend-services create ${BACKEND_SERVICE_NAME} \
	#	--project=${GCLOUD_PROJECT} \
  	# 	--global \
	# gcloud compute backend-services add-backend ${BACKEND_SERVICE_NAME} \
	# 	--global \
	# 	--project=${GCLOUD_PROJECT} \
	# 	--network-endpoint-group=${NEG_NAME} \
	# 	--network-endpoint-group-region=${REGION}
	# gcloud compute url-maps create ${API_GATEWAY_URL_MAP_NAME} \
	# 	--project=${GCLOUD_PROJECT} \
  	# 	--default-service ${BACKEND_SERVICE_NAME}
	# gcloud compute ssl-certificates create ${SSL_CERTIFICATE_NAME} \
	#	--project=${GCLOUD_PROJECT} \
  	# 	--domains ${DOMAIN}
	# gcloud compute target-https-proxies create ${TARGET_HTTP_PROXY_NAME} \
	# 	--project=${GCLOUD_PROJECT} \
	# 	--ssl-certificates=${SSL_CERTIFICATE_NAME} \
	# 	--url-map=${API_GATEWAY_URL_MAP_NAME}
	# gcloud compute forwarding-rules create ${HTTPS_FORWARDING_RULE_NAME} \
	# 	--project=${GCLOUD_PROJECT} \
	# 	--target-https-proxy=${TARGET_HTTP_PROXY_NAME} \
	# 	--global \
	# 	--ports=443
	# gcloud compute forwarding-rules list
	# update dns with ip https://dash.cloudflare.com/9850df1eb8fd807eb8e06f4057b473f1/langa.me/dns
	# curl ${DOMAIN}

	# gcloud alpha services api-keys create --display-name=${API_KEY_NAME}
	# gcloud services enable $(shell gcloud api-gateway apis describe ${API_NAME} --format 'value(managedService)' 2>/dev/null)

	curl -X POST \
		https://${API_GATEWAY_HOSTNAME}/v1/conversation/starter -H "x-api-key: ${API_KEY_VALUE}"
	
	
	

deploy: ## [Local development] deploy to GCP.
	# firebase deploy --only hosting
	gcloud beta functions deploy ${FUNCTION_NAME} \
		--runtime python39 \
		--trigger-http \
		--allow-unauthenticated \
		--set-env-vars=AVA_URL=${AVA_URL} \
		--project ${GCLOUD_PROJECT} \
		--timeout 540s
	# curl -X POST https://dapi.langa.me/starter

update_config: ## [Local development] update the config.
	gcloud api-gateway api-configs create ${API_GATEWAY_CONFIG_NAME} \
		--api=${API_NAME} \
		--openapi-spec=openapi2.yaml \
		--project=${GCLOUD_PROJECT} \
		--backend-auth-service-account=${API_GATEWAY_SVC_FULL}

	gcloud api-gateway gateways update ${GATEWAY_NAME} \
		--api=${API_NAME} \
		--api-config=${API_GATEWAY_CONFIG_NAME} \
		--location=${REGION} \
		--project=${GCLOUD_PROJECT}

apply: ## [Local development] https://firebase.google.com/docs/hosting/multisites
	firebase target:apply hosting api langame-dev-api

third_party: ## [Local development] third party dependencies
	mkdir -p third_party
	pip install -t third_party ${HOME}/Documents/langame-worker/functions/common
	echo "from .common.ava_client import get_starter" > third_party/__init__.py

.PHONY: help

help: # Run `make help` to get help on the make commands
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
