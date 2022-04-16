TOPIC_NAME ?= openai_sync_topic

deploy: ## [Local development] deploy to GCP.
	gcloud beta functions deploy openai_sync \
		--runtime python39 \
		--trigger-resource ${TOPIC_NAME} \
		--trigger-event google.pubsub.topic.publish \
		--set-secrets "OPENAI_KEY=openai_key:latest" \
		--set-secrets "OPENAI_ORG=openai_org:latest" \
		--timeout 540s

schedule: ## [Local development] schedule to run every minute.
	gcloud scheduler jobs create pubsub openai_sync_job \
		--schedule "*/30 * * * *" \
		--topic ${TOPIC_NAME} \
		--message-body "Hello, World!"

.PHONY: help

help: # Run `make help` to get help on the make commands
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
