prod: ## Set the GCP project to prod
	gcloud config set project langame-86ac4

dev: ## Set the GCP project to dev
	gcloud config set project langame-dev

clean:
	rm -rf env build **/wandb **/embeddings **/indexes *.egg-info **/index_infos.json **/__pycache__

.PHONY: help

help: # Run `make help` to get help on the make commands
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'