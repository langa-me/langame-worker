REGISTRY ?= 5306t2h8.gra7.container-registry.ovh.net/$(shell cat .env | grep OVH_PROJECT_ID | cut -d '=' -f 2)/ava
# take version in setup.py, only what's between the quotes """
VERSION ?= $(shell cat setup.py | grep version | cut -d '"' -f 2)
GCLOUD_PROJECT:=$(shell gcloud config list --format 'value(core.project)' 2>/dev/null)

ifeq ($(GCLOUD_PROJECT),langame-dev)
$(info "Using develoment configuration")
DISCORD_BOT_TOKEN := $(shell cat ../../.env.development | grep -w DISCORD_BOT_TOKEN | cut -d "=" -f 2)
DISCORD_CLIENT_PUBLIC_KEY := $(shell cat ../../.env.development | grep -w DISCORD_CLIENT_PUBLIC_KEY | cut -d "=" -f 2)
SVC_PATH := "../../svc.dev.json"
else
$(info "Using production configuration")
DISCORD_BOT_TOKEN:=$(shell cat ../../.env.production | grep -w DISCORD_BOT_TOKEN | cut -d "=" -f 2)
DISCORD_CLIENT_PUBLIC_KEY:=$(shell cat ../../.env.production | grep -w DISCORD_CLIENT_PUBLIC_KEY | cut -d "=" -f 2)
SVC_PATH := "../../svc.prod.json"
endif

GCLOUD_PROJECT:=$(shell gcloud config list --format 'value(core.project)' 2>/dev/null)


lint: ## [Local development] Run pylint to check code style.
	@echo "Linting"
	env/bin/python3 -m pylint socialis

bare/run: ## [Local development] run the main entrypoint
	python3 $(shell pwd)/socialis/main.py --discord_bot_token ${DISCORD_BOT_TOKEN} --svc_path ${SVC_PATH}


docker/build: ## [Local development] build the docker image
	mkdir -p third_party/langame-worker/langame
	cp -r ../langame-worker/langame/ third_party/langame-worker/
	cp ../langame-worker/setup.py third_party/langame-worker/setup.py
	docker build -t ${REGISTRY}:${VERSION} . -f ./Dockerfile --build-arg HUGGINGFACE_TOKEN=${HUGGINGFACE_TOKEN}
	rm -rf third_party

docker/run: docker/build ## [Local development] run the docker container
	docker run \
		-v $(shell pwd)/svc.dev.json:/etc/secrets/primary/svc.json \
		-e OPENAI_KEY=${OPENAI_KEY} \
		-e OPENAI_ORG=${OPENAI_ORG} \
		-e HUGGINGFACE_TOKEN=${HUGGINGFACE_TOKEN} \
		-e HUGGINGFACE_KEY=${HUGGINGFACE_KEY} \
		${REGISTRY}:${VERSION} \
		--profanity_threshold tolerant \
		--completion_type local \
		--tweet_on_generate False \
		--use_gpu False

docker/push: docker_build ## [Local development] push the docker image to GCR
	docker push ${REGISTRY}:${VERSION}
	docker push ${REGISTRY}:latest

# k8s

k8s_deploy: ## [Local development] deploy to Kubernetes.
	helm install ava helm -f ${HELM_VALUES} -n ${K8S_NAMESPACE} --create-namespace
k8s_upgrade: ## [Local development] upgrade with new config.
	helm upgrade ava helm -f ${HELM_VALUES} -n ${K8S_NAMESPACE}
	# --recreate-pods
k8s_undeploy: ## [Local development] undeploy from Kubernetes.
	helm uninstall ava -n ${K8S_NAMESPACE}


.PHONY: help

help: # Run `make help` to get help on the make commands
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
