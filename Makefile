GCLOUD_PROJECT:=$(shell gcloud config list --format 'value(core.project)' 2>/dev/null)
REGION="us-central1"

CLOUD_PROJECT:=$(shell gcloud config list --format 'value(core.project)' 2>/dev/null)
LATEST_IMAGE_URL=$(shell echo "gcr.io/${CLOUD_PROJECT}/collection:latest")
VERSION=$(shell sed -n 's/.*image:.*:\(.*\)/\1/p' run/collection/service.prod.yaml)
IMAGE_URL=$(shell echo "gcr.io/${CLOUD_PROJECT}/collection:${VERSION}")

install: ## Install dependencies
	@echo "Installing dependencies..."
	virtualenv -p python3 env
	. env/bin/activate && pip install -e . && \
		pip install -r requirements-test.txt && \
		pip install -r optional-requirements.txt

prod: ## Set the GCP project to prod
	gcloud config set project langame-86ac4

dev: ## Set the GCP project to dev
	gcloud config set project langame-dev

clean:
	rm -rf env build **/wandb **/embeddings **/indexes *.egg-info **/index_infos.json **/__pycache__

release:
	@VERSION=$$(cat setup.py | grep version | cut -d '"' -f 2); \
	echo "Releasing version $$VERSION"; \
	git add --all -- :!notebooks; \
	read -p "Commit content:" COMMIT; \
	echo "Committing '$$VERSION: $$COMMIT'"; \
	git commit -m "$$VERSION: $$COMMIT"; \
	git push origin main; \
	git tag $$VERSION; \
	git push origin $$VERSION
	@echo "Done, check https://github.com/langa-me/langame-worker/actions"


self_chat:
#python3 scripts/self_chat.py generate_seeds
	parlai self_chat --model-file zoo:seeker/seeker_dialogue_400M/model --task empathetic_dialogues --num-self-chats 200 --display-examples True --seed_messages_from_file="../langame-worker/seeds.txt" --outfile="./out" --rag-retriever-type search_engine 
#--search_server http://localhost:8083

## Functions & run

run/collection/hosting:
	cd run/collection; \
	firebase use ${GCLOUD_PROJECT}; \
	firebase deploy --only hosting

run/collection/build: ## [Local development] Build the docker image.
	@echo "Building docker image for urls ${LATEST_IMAGE_URL} and ${IMAGE_URL}"
	@docker buildx build ./run/collection --platform linux/amd64 -t ${LATEST_IMAGE_URL} -f ./run/collection/Dockerfile
	@docker buildx build ./run/collection --platform linux/amd64 -t ${IMAGE_URL} -f ./run/collection/Dockerfile

run/collection/push: run/collection/build ## [Local development] Push the image to GCR.
	docker push ${IMAGE_URL}
	docker push ${LATEST_IMAGE_URL}

run/collection/deploy: run/collection/push ## [Local development] Build docker image, push and deploy to GCP.
	@echo "Will deploy to ${REGION} on ${CLOUD_PROJECT}"
	gcloud beta run services replace ./run/collection/service.prod.yaml --region ${REGION}

run/collection/policy:
	gcloud run services set-iam-policy collection run/collection/policy.prod.yaml --region ${REGION}

.PHONY: help

help: # Run `make help` to get help on the make commands
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'