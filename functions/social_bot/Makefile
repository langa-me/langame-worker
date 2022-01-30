DISCORD_APPLICATION_ID ?= foo
GCLOUD_PROJECT:=$(shell gcloud config list --format 'value(core.project)' 2>/dev/null)

third_party: ## [Local development] third party dependencies
	rm -rf third_party
	pip install -t third_party ../common

deploy: ## [Local development] deploy to GCP.
	gcloud beta functions deploy social_bot \
		--runtime python39 \
		--min-instances 1 \
		--timeout 180 \
		--trigger-event "providers/cloud.firestore/eventTypes/document.create" \
  		--trigger-resource "projects/${GCLOUD_PROJECT}/databases/(default)/documents/social_interactions/{interactionId}" \
		--set-env-vars=DISCORD_APPLICATION_ID=${DISCORD_APPLICATION_ID}

.PHONY: help

help: # Run `make help` to get help on the make commands
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
