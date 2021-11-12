install: ## [Local development] Install virtualenv, activate, install requirements, install package.
	python3 -m pip install virtualenv
	python3 -m virtualenv env
	env/bin/python3 -m pip install -e .
	env/bin/python3 -m pip install -r requirements-test.txt

.PHONY: help

help: # Run `make help` to get help on the make commands
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'