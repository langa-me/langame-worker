DISCORD_APPLICATION_ID ?= foo
PROJECT_ID ?= langame-dev

deploy: ## [Local development] deploy to GCP.
	gcloud beta functions deploy social_bot \
		--runtime python39 \
		--trigger-event "providers/cloud.firestore/eventTypes/document.create" \
  		--trigger-resource "projects/${PROJECT_ID}/databases/(default)/documents/social_interactions/{interactionId}" \
		--set-env-vars=DISCORD_APPLICATION_ID=${DISCORD_APPLICATION_ID}

.PHONY: help

help: # Run `make help` to get help on the make commands
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
