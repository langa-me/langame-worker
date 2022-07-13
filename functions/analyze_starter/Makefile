GCLOUD_PROJECT:=$(shell gcloud config list --format 'value(core.project)' 2>/dev/null)

ifeq ($(GCLOUD_PROJECT),langame-dev)
$(info "Using develoment configuration")
HUGGINGFACE_API_KEY := $(shell cat ../../.env.development | grep -w HUGGINGFACE_API_KEY | cut -d "=" -f 2)
else
$(info "Using production configuration")
HUGGINGFACE_API_KEY:=$(shell cat ../../.env.production | grep -w HUGGINGFACE_API_KEY | cut -d "=" -f 2)
endif

deploy: ## [Local development] deploy to GCP.
	gcloud beta functions deploy analyze_starter \
		--runtime python39 \
		--trigger-event "providers/cloud.firestore/eventTypes/document.write" \
  		--trigger-resource "projects/${GCLOUD_PROJECT}/databases/(default)/documents/memes/{memeId}" \
		--set-env-vars=HUGGINGFACE_API_KEY=${HUGGINGFACE_API_KEY} \
		--project ${GCLOUD_PROJECT} \
		--timeout 240

.PHONY: help

help: # Run `make help` to get help on the make commands
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
