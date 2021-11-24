APPLICATION_ID ?= foo

deploy: ## [Local development] deploy to GCP.
	gcloud beta functions deploy social_bot \
		--runtime python39 \
		--trigger-topic social_bot \
		--set-env-vars=APPLICATION_ID=${APPLICATION_ID}

.PHONY: help

help: # Run `make help` to get help on the make commands
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
