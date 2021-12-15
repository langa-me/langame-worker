GCLOUD_PROJECT:=$(shell gcloud config list --format 'value(core.project)' 2>/dev/null)
FUNCTION_NAME ?= "public_starter"
REGION="us-central1"

third_party: ## [Local development] third party dependencies
	rm -rf third_party
	pip install -t third_party ../../common
	echo "from .common.starter import get_starter" > third_party/__init__.py

deploy: ## [Local development] deploy to GCP.
	# firebase deploy --only hosting
	gcloud beta functions deploy ${FUNCTION_NAME} \
		--runtime python39 \
		--trigger-http \
		--allow-unauthenticated \
		--project ${GCLOUD_PROJECT} \
		--timeout 540s
	# curl -X POST https://dapi.langa.me/starter

apply: ## [Local development] https://firebase.google.com/docs/hosting/multisites
	firebase target:apply hosting api langame-dev-api

.PHONY: help

help: # Run `make help` to get help on the make commands
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
