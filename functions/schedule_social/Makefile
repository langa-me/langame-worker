TOPIC_NAME ?= schedule_social_topic
DISCORD_BOT_TOKEN ?= foo

third_party: ## [Local development] third party dependencies
	rm -rf third_party
	pip install -t third_party ../common

deploy: ## [Local development] deploy to GCP.
	gcloud beta functions deploy schedule_social \
		--runtime python39 \
		--trigger-resource ${TOPIC_NAME} \
		--trigger-event google.pubsub.topic.publish \
		--set-env-vars=DISCORD_BOT_TOKEN=${DISCORD_BOT_TOKEN} \
		--timeout 540s

schedule: ## [Local development] schedule to run every minute.
	gcloud scheduler jobs create pubsub schedule_social_job \
		--schedule "*/30 * * * *" \
		--topic ${TOPIC_NAME} \
		--message-body "Hello, World!"

.PHONY: help

help: # Run `make help` to get help on the make commands
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
