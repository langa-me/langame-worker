GCLOUD_PROJECT:=$(shell gcloud config list --format 'value(core.project)' 2>/dev/null)

deploy: ## [Local development] deploy to GCP.
	gcloud beta functions deploy translate \
		--runtime python39 \
		--trigger-event "providers/cloud.firestore/eventTypes/document.write" \
  		--trigger-resource "projects/${GCLOUD_PROJECT}/databases/(default)/documents/memes/{memeId}" \
		--timeout 240

.PHONY: help

help: # Run `make help` to get help on the make commands
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
