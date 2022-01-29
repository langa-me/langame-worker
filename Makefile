set_prod: ## Set the GCP project to prod
	gcloud config set project langame-86ac4

set_dev: ## Set the GCP project to dev
	gcloud config set project langame-dev


install: ## [Local development] Install virtualenv, activate, install requirements, install package.
	(\
		python3 -m virtualenv env; \
		. env/bin/activate; \
		python3 -m pip install -e .; \
		python3 -m pip install -r requirements-test.txt; \
	)

clean:
	rm -rf env build **/wandb **/embeddings **/indexes *.egg-info **/index_infos.json **/__pycache__

.PHONY: help

help: # Run `make help` to get help on the make commands
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'