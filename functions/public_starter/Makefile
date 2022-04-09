GCLOUD_PROJECT:=$(shell gcloud config list --format 'value(core.project)' 2>/dev/null)
FUNCTION_NAME ?= "public_starter"
REGION="us-central1"
GET_MEMES_URL ?= "https://us-central1-${GCLOUD_PROJECT}.cloudfunctions.net/getMemes"
third_party: ## [Local development] third party dependencies
	rm -rf third_party
	python3 -m pip install -t third_party ../common


deploy: ## [Local development] deploy to GCP.
	firebase use ${GCLOUD_PROJECT}
	firebase deploy --only hosting
	gcloud beta functions deploy ${FUNCTION_NAME} \
		--runtime python39 \
		--trigger-http \
		--allow-unauthenticated \
		--project ${GCLOUD_PROJECT} \
		--timeout 540s \
		--set-env-vars GET_MEMES_URL=${GET_MEMES_URL}

apply_dev: ## [Local development] https://firebase.google.com/docs/hosting/multisites
	firebase use ${GCLOUD_PROJECT}
	firebase target:apply hosting api langame-dev-api
apply_prod: ## [Local development] https://firebase.google.com/docs/hosting/multisites
	firebase use ${GCLOUD_PROJECT}
	firebase target:apply hosting api langame-prod-api

.PHONY: help

help: # Run `make help` to get help on the make commands
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
