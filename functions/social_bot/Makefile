GCLOUD_PROJECT:=$(shell gcloud config list --format 'value(core.project)' 2>/dev/null)
GET_MEMES_URL ?= "https://us-central1-${GCLOUD_PROJECT}.cloudfunctions.net/getMemes"

ifeq ($(GCLOUD_PROJECT),langame-dev)
$(info "Using develoment configuration")
DISCORD_APPLICATION_ID := $(shell cat ../../.env.development | grep -w DISCORD_APPLICATION_ID | cut -d "=" -f 2)
DISCORD_BOT_TOKEN := $(shell cat ../../.env.development | grep -w DISCORD_BOT_TOKEN | cut -d "=" -f 2)
else
$(info "Using production configuration")
DISCORD_APPLICATION_ID:=$(shell cat ../../.env.production | grep -w DISCORD_APPLICATION_ID | cut -d "=" -f 2)
DISCORD_BOT_TOKEN:=$(shell cat ../../.env.production | grep -w DISCORD_BOT_TOKEN | cut -d "=" -f 2)
endif

third_party: ## [Local development] third party dependencies
	rm -rf third_party
	pip install -t third_party ../common

deploy: ## [Local development] deploy to GCP.
	gcloud beta functions deploy social_bot \
		--runtime python39 \
		--timeout 180 \
		--trigger-event "providers/cloud.firestore/eventTypes/document.create" \
  		--trigger-resource "projects/${GCLOUD_PROJECT}/databases/(default)/documents/social_interactions/{interactionId}" \
		--set-env-vars=DISCORD_APPLICATION_ID=${DISCORD_APPLICATION_ID} \
		--set-env-vars=DISCORD_BOT_TOKEN=${DISCORD_BOT_TOKEN} \
		--set-env-vars GET_MEMES_URL=${GET_MEMES_URL}

.PHONY: help

help: # Run `make help` to get help on the make commands
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
