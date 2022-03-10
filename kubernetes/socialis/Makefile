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

LANGAME_APP_PATH ?= "${HOME}/Documents/langame-app"

# eval $(cat .env | sed 's/^/export /')

# baremetal

install: ## [Local development] Upgrade pip, install requirements, install package.
	(\
		python3 -m virtualenv env; \
		. env/bin/activate; \
		python3 -m pip install -U pip; \
		python3 -m pip install -e .; \
		python3 -m pip install -r requirements-test.txt; \
	)

protos: ## [Local development] Generate protos.
	python3 -m grpc_tools.protoc \
		--python_out=socialis \
		--grpc_python_out=socialis \
		-I proto/socialis/v1 \
		proto/socialis/v1/*.proto
	@echo "Assuming path to langa-me/langame-app is ${LANGAME_APP_PATH}"
	mkdir -p ${LANGAME_APP_PATH}/lib/models/langame/socialis
	protoc -I proto/socialis/v1 \
		--dart_out=grpc:${LANGAME_APP_PATH}/lib/models/langame/socialis \
		proto/socialis/v1/*.proto
	

lint: ## [Local development] Run pylint to check code style.
	@echo "Linting"
	env/bin/python3 -m pylint socialis

run: ## [Local development] run the main entrypoint
	# envoy -c envoy.yaml &
	python3 $(shell pwd)/socialis/main.py --discord_bot_token ${DISCORD_BOT_TOKEN} --svc_path ${SVC_PATH}
	# kill -9 $(ps -ef | grep envoy | grep -v grep | awk '{print $2}')

.PHONY: help

help: # Run `make help` to get help on the make commands
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
