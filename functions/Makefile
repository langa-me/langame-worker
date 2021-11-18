OPENAI_KEY ?= foo
OPENAI_ORG ?= bar
deploy:
	gcloud functions deploy conversation_starter \
		--runtime python39 \
		--trigger-http \
		--allow-unauthenticated \
		--set-env-vars OPENAI_KEY=$(OPENAI_KEY),OPENAI_ORG=$(OPENAI_ORG)

install:
	# if gitpod "export PIP_USER=false"
	(\
		python3 -m virtualenv env; \
		. env/bin/activate; \
		python3 -m pip install -r requirements.txt; \
		python3 -m pip install -r requirements-test.txt; \
	)