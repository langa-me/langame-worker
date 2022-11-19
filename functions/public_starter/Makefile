GCLOUD_PROJECT:=$(shell gcloud config list --format 'value(core.project)' 2>/dev/null)
REGION="us-central1"
GET_MEMES_URL ?= "https://us-central1-${GCLOUD_PROJECT}.cloudfunctions.net/getMemes"


third_party: ## [Local development] third party dependencies
	rm -rf third_party
	python3 -m pip install -t third_party ../common

deploy/public_starter: ## [Local development] deploy to GCP.
	firebase use ${GCLOUD_PROJECT}
	firebase deploy --only hosting
	gcloud beta functions deploy public_starter \
		--runtime python39 \
		--trigger-http \
		--allow-unauthenticated \
		--project ${GCLOUD_PROJECT} \
		--timeout 540s \
		--entry-point public_starter \
		--set-env-vars GET_MEMES_URL=${GET_MEMES_URL}

test/collection_conversation_starter: ## [Local development] Test the function.
	functions_framework --target=collection_conversation_starter --debug

deploy/collection_conversation_starter: ## [Local development] deploy to GCP.
	firebase use ${GCLOUD_PROJECT}
	firebase deploy --only hosting
	gcloud beta functions deploy collection_conversation_starter \
		--runtime python39 \
		--trigger-http \
		--allow-unauthenticated \
		--project ${GCLOUD_PROJECT} \
		--timeout 540s \
		--entry-point collection_conversation_starter
deploy: deploy/public_starter deploy/collection_conversation_starter

apply_dev: ## [Local development] https://firebase.google.com/docs/hosting/multisites
	firebase use ${GCLOUD_PROJECT}
	firebase target:apply hosting api langame-dev-api
apply_prod: ## [Local development] https://firebase.google.com/docs/hosting/multisites
	firebase use ${GCLOUD_PROJECT}
	firebase target:apply hosting api langame-prod-api

curl/starter:
	curl -X POST -H "Content-Type: application/json" -H "X-Api-Key: $$API_KEY" -d '{"topics": ["ice breaker"]}' https://api.langa.me/v1/conversation/starter | jq '.'

curl/conversation_collection/get:
	curl -X GET -H "Content-Type: application/json" -H "X-Api-Key: $$API_KEY" https://api.langa.me/v1/conversation/collection | jq '.'


.PHONY: help

help: # Run `make help` to get help on the make commands
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
