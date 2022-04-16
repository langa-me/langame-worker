# take version in setup.py, only what's between the quotes """
VERSION ?= $(shell cat setup.py | grep version | cut -d '"' -f 2)
GCLOUD_PROJECT:=$(shell gcloud config list --format 'value(core.project)' 2>/dev/null)
NAME ?= socialis

ifeq ($(GCLOUD_PROJECT),langame-dev)
$(info "Using develoment configuration")
REGISTRY ?= 5306t2h8.gra7.container-registry.ovh.net/dev/${NAME}
DISCORD_BOT_TOKEN := $(shell cat ../../.env.development | grep -w DISCORD_BOT_TOKEN | cut -d "=" -f 2)
DISCORD_CLIENT_PUBLIC_KEY := $(shell cat ../../.env.development | grep -w DISCORD_CLIENT_PUBLIC_KEY | cut -d "=" -f 2)
SVC_PATH := svc.dev.json
HELM_VALUES := helm/values-dev.yaml
K8S_NAMESPACE := ${NAME}-dev
else
$(info "Using production configuration")
REGISTRY ?= 5306t2h8.gra7.container-registry.ovh.net/prod/${NAME}
DISCORD_BOT_TOKEN:=$(shell cat ../../.env.production | grep -w DISCORD_BOT_TOKEN | cut -d "=" -f 2)
DISCORD_CLIENT_PUBLIC_KEY:=$(shell cat ../../.env.production | grep -w DISCORD_CLIENT_PUBLIC_KEY | cut -d "=" -f 2)
SVC_PATH := svc.prod.json
HELM_VALUES := helm/values-prod.yaml
K8S_NAMESPACE := ${NAME}-prod
endif


lint: ## [Local development] Run pylint to check code style.
	@echo "Linting"
	env/bin/python3 -m pylint social${NAME}is

bare/run: ## [Local development] run the main entrypoint
	python3 socialis/main.py \
		--svc_path ${SVC_PATH} \
		--discord_bot_token ${DISCORD_BOT_TOKEN} \
		--parlai_websocket_url ws://localhost:8083

docker/build: ## [Local development] build the docker image
	docker buildx build -t ${REGISTRY}:${VERSION} -t ${REGISTRY}:latest --platform linux/amd64 . -f ./Dockerfile


docker/run: docker/build ## [Local development] run the docker container
	docker run \
		--network host \
		--rm \
		--name ${NAME} \
		-v $(shell pwd)/${SVC_PATH}:/etc/secrets/svc.json \
		${REGISTRY}:${VERSION} \
			--discord_bot_token ${DISCORD_BOT_TOKEN} \
			--svc_path /etc/secrets/svc.json \
			--parlai_websocket_url ws://localhost:8082


docker/push: docker/build ## [Local development] push the docker image to GCR
	docker push ${REGISTRY}:${VERSION}
	docker push ${REGISTRY}:latest

k8s/deploy: ## [Local development] deploy to Kubernetes.
	helm install ${NAME} helm -f ${HELM_VALUES} -n ${K8S_NAMESPACE} --create-namespace
k8s/upgrade: ## [Local development] upgrade with new config.
	helm upgrade ${NAME} helm -f ${HELM_VALUES} -n ${K8S_NAMESPACE}
k8s/undeploy: ## [Local development] undeploy from Kubernetes.
	helm uninstall ${NAME} -n ${K8S_NAMESPACE}


.PHONY: help

help: # Run `make help` to get help on the make commands
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
