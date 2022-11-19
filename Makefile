prod: ## Set the GCP project to prod
	gcloud config set project langame-86ac4

dev: ## Set the GCP project to dev
	gcloud config set project langame-dev

clean:
	rm -rf env build **/wandb **/embeddings **/indexes *.egg-info **/index_infos.json **/__pycache__

release:
	@VERSION=$$(cat setup.py | grep version | cut -d '"' -f 2); \
	echo "Releasing version $$VERSION"; \
	git add .; \
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

.PHONY: help

help: # Run `make help` to get help on the make commands
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'