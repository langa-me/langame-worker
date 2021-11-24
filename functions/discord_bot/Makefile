CLIENT_PUBLIC_KEY ?= foo
deploy: ## [Local development] deploy to GCP.
	gcloud beta functions deploy discord_bot \
		--runtime python39 \
		--trigger-http \
		--allow-unauthenticated \
		--set-env-vars=CLIENT_PUBLIC_KEY=${CLIENT_PUBLIC_KEY}

.PHONY: help

help: # Run `make help` to get help on the make commands
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
