TOPIC_NAME ?= schedule_social_topic
GCLOUD_PROJECT:=$(shell gcloud config list --format 'value(core.project)' 2>/dev/null)
GET_MEMES_URL ?= "https://us-central1-${GCLOUD_PROJECT}.cloudfunctions.net/getMemes"

ifeq ($(GCLOUD_PROJECT),langame-dev)
$(info "Using develoment configuration")
DISCORD_BOT_TOKEN := $(shell cat ../../.env.development | grep -w DISCORD_BOT_TOKEN | cut -d "=" -f 2)
else
$(info "Using production configuration")
DISCORD_BOT_TOKEN:=$(shell cat ../../.env.production | grep -w DISCORD_BOT_TOKEN | cut -d "=" -f 2)
endif

third_party: ## [Local development] third party dependencies
	rm -rf third_party
	pip install -t third_party ../common

deploy: ## [Local development] deploy to GCP.
	gcloud beta functions deploy schedule_social \
		--runtime python39 \
		--trigger-resource ${TOPIC_NAME} \
		--trigger-event google.pubsub.topic.publish \
		--set-env-vars=DISCORD_BOT_TOKEN=${DISCORD_BOT_TOKEN} \
		--set-env-vars GET_MEMES_URL=${GET_MEMES_URL} \
		--timeout 540s

schedule: ## [Local development] schedule to run every minute.
	gcloud scheduler jobs create pubsub schedule_social_job \
		--schedule "*/30 * * * *" \
		--topic ${TOPIC_NAME} \
		--message-body "Hello, World!"

.PHONY: help

help: # Run `make help` to get help on the make commands
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
