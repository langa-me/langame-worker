DISCORD_CLIENT_PUBLIC_KEY ?= foo
DISCORD_BOT_TOKEN ?= bar
GCLOUD_PROJECT:=$(shell gcloud config list --format 'value(core.project)' 2>/dev/null)

ifeq ($(GCLOUD_PROJECT),langame-dev)
$(info "Using develoment configuration")
DISCORD_BOT_TOKEN := $(shell cat ../../.env.development | grep -w DISCORD_BOT_TOKEN | cut -d "=" -f 2)
DISCORD_CLIENT_PUBLIC_KEY := $(shell cat ../../.env.development | grep -w DISCORD_CLIENT_PUBLIC_KEY | cut -d "=" -f 2)
else
$(info "Using production configuration")
DISCORD_BOT_TOKEN:=$(shell cat ../../.env.production | grep -w DISCORD_BOT_TOKEN | cut -d "=" -f 2)
DISCORD_CLIENT_PUBLIC_KEY:=$(shell cat ../../.env.production | grep -w DISCORD_CLIENT_PUBLIC_KEY | cut -d "=" -f 2)
endif

third_party: ## [Local development] third party dependencies
	rm -rf third_party
	python3 -m pip -t third_party ../common

deploy: ## [Local development] deploy to GCP.
	gcloud beta functions deploy discord_bot \
		--runtime python39 \
		--trigger-http \
		--allow-unauthenticated \
		--min-instances 1 \
		--set-env-vars=DISCORD_CLIENT_PUBLIC_KEY=${DISCORD_CLIENT_PUBLIC_KEY} \
		--set-env-vars=DISCORD_BOT_TOKEN=${DISCORD_BOT_TOKEN}

.PHONY: help

help: # Run `make help` to get help on the make commands
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
