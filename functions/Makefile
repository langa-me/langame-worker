OPENAI_KEY ?= foo
OPENAI_ORG ?= bar
deploy: ## [Local development] deploy to GCP.
	gcloud functions deploy conversation_starter \
		--runtime python39 \
		--trigger-http \
		--allow-unauthenticated \
		--set-env-vars OPENAI_KEY=$(OPENAI_KEY),OPENAI_ORG=$(OPENAI_ORG)

test:
	python3 -m unittest conversation_starter_test.py

.PHONY: help

help: # Run `make help` to get help on the make commands
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
