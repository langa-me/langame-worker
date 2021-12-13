DISCORD_APPLICATION_ID ?= foo
AVA_URL ?= foo
GCLOUD_PROJECT:=$(shell gcloud config list --format 'value(core.project)' 2>/dev/null)

deploy: ## [Local development] deploy to GCP.
	gcloud beta functions deploy social_bot \
		--runtime python39 \
		--trigger-event "providers/cloud.firestore/eventTypes/document.create" \
  		--trigger-resource "projects/${GCLOUD_PROJECT}/databases/(default)/documents/social_interactions/{interactionId}" \
		--set-env-vars=DISCORD_APPLICATION_ID=${DISCORD_APPLICATION_ID} \
		--set-env-vars=AVA_URL=${AVA_URL}

.PHONY: help

help: # Run `make help` to get help on the make commands
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
