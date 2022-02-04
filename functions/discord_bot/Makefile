DISCORD_CLIENT_PUBLIC_KEY ?= foo
DISCORD_BOT_TOKEN ?= bar
GCLOUD_PROJECT:=$(shell gcloud config list --format 'value(core.project)' 2>/dev/null)

# if GCLOUD_PROJECT contains "dev", set DISCORD_BOT_TOKEN and DISCORD_CLIENT_PUBLIC_KEY
# with DEV_DISCORD_BOT_TOKEN and DEV_DISCORD_CLIENT_PUBLIC_KEY
# found in the file ../../.env
# otherwise use DISCORD_BOT_TOKEN and DISCORD_CLIENT_PUBLIC_KEY
# found in the file ../../.env-
ifeq ($(GCLOUD_PROJECT),langame-dev)
$(info "GCLOUD_PROJECT seems to be dev, setting DISCORD_BOT_TOKEN and DISCORD_CLIENT_PUBLIC_KEY")
$(info "with DEV_DISCORD_BOT_TOKEN and DEV_DISCORD_CLIENT_PUBLIC_KEY from ../../.env")
DISCORD_BOT_TOKEN := $(shell cat ../../.env | grep DEV_DISCORD_BOT_TOKEN | cut -d "=" -f 2)
DISCORD_CLIENT_PUBLIC_KEY := $(shell cat ../../.env | grep DEV_DISCORD_CLIENT_PUBLIC_KEY | cut -d "=" -f 2)
else
$(info "GCLOUD_PROJECT seems to be prod, setting DISCORD_BOT_TOKEN and DISCORD_CLIENT_PUBLIC_KEY")
$(info "with DISCORD_BOT_TOKEN and DISCORD_CLIENT_PUBLIC_KEY from ../../.env")
DISCORD_BOT_TOKEN:=$(shell cat ../../.env | grep DISCORD_BOT_TOKEN | cut -d "=" -f 2)
DISCORD_CLIENT_PUBLIC_KEY:=$(shell cat ../../.env | grep DISCORD_CLIENT_PUBLIC_KEY | cut -d "=" -f 2)
endif

third_party: ## [Local development] third party dependencies
	rm -rf third_party
	pip install -t third_party ../common

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
